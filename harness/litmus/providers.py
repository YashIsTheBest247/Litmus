"""Model providers behind a single conversation interface.

Litmus does not care which vendor produced a patch - it cares whether the
patch survives the held-out suite. Keeping providers behind one interface is
what lets the leaderboard put OpenAI and Gemini in the same table, and makes
"which model games tests more" an answerable question rather than a vibe.

Each provider owns its own conversation history because the wire formats differ
enough that a shared history representation would leak provider details
everywhere.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

# Free-tier Gemini throttles per minute as well as per day, and an iterative
# agent burns a minute's allowance in seconds. Pace requests rather than
# discovering the limit through failures. 10/min suits the 3.x Flash models.
DEFAULT_RPM = 10
MAX_RETRIES = 6
RETRY_DELAY_PATTERN = re.compile(r"retryDelay'?\s*:\s*'?(\d+(?:\.\d+)?)s")


@dataclass
class ToolCall:
    id: str
    name: str
    args: dict[str, Any]


@dataclass
class ToolResult:
    call: ToolCall
    content: str


@dataclass
class Reply:
    text: str = ""
    calls: list[ToolCall] = field(default_factory=list)


@dataclass
class ToolSpec:
    name: str
    description: str
    properties: dict[str, Any]
    required: list[str]


class Conversation(Protocol):
    """A stateful exchange with one model."""

    def send_user(self, text: str) -> Reply: ...
    def send_tool_results(self, results: list[ToolResult]) -> Reply: ...


class ProviderError(RuntimeError):
    """Configuration or transport failure that should abort the run cleanly."""


def load_gemini_keys() -> list[str]:
    """Collect every Gemini key the environment offers, in a stable order.

    Accepts GEMINI_API_KEYS as a comma or whitespace separated list, the
    singular GEMINI_API_KEY, numbered GEMINI_API_KEY_1..N, and GOOGLE_API_KEY.
    Each key carries its own free-tier allowance, so several of them is the
    difference between a run that finishes and one that stops halfway.
    """
    found: list[str] = []

    bulk = os.environ.get("GEMINI_API_KEYS", "")
    found.extend(part.strip() for part in re.split(r"[,\s]+", bulk) if part.strip())

    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        value = (os.environ.get(name) or "").strip()
        if value:
            found.append(value)

    index = 1
    while True:
        value = (os.environ.get(f"GEMINI_API_KEY_{index}") or "").strip()
        if not value:
            break
        found.append(value)
        index += 1

    seen: set[str] = set()
    ordered = []
    for key in found:
        if key not in seen:
            seen.add(key)
            ordered.append(key)
    return ordered


class KeyPool:
    """Rotates through API keys, retiring any that run out for the day."""

    def __init__(self, keys: list[str]):
        if not keys:
            raise ProviderError(
                "no Gemini key found - set GEMINI_API_KEY, or GEMINI_API_KEYS for several"
            )
        self._keys = keys
        self._index = 0
        self._retired: set[int] = set()

    @property
    def size(self) -> int:
        return len(self._keys)

    @property
    def remaining(self) -> int:
        return len(self._keys) - len(self._retired)

    def current(self) -> str:
        return self._keys[self._index]

    def label(self) -> str:
        return f"key {self._index + 1}/{len(self._keys)}"

    def retire_and_rotate(self) -> bool:
        """Drop the current key and move to the next live one."""
        self._retired.add(self._index)
        for offset in range(1, len(self._keys) + 1):
            candidate = (self._index + offset) % len(self._keys)
            if candidate not in self._retired:
                self._index = candidate
                return True
        return False


# One pool per process, so every task in a run shares the rotation state
# instead of each starting again on an already-exhausted key.
_POOL: KeyPool | None = None


def gemini_pool() -> KeyPool:
    global _POOL
    if _POOL is None:
        _POOL = KeyPool(load_gemini_keys())
    return _POOL


def reset_gemini_pool() -> None:
    """Test hook."""
    global _POOL
    _POOL = None


class _Pacer:
    """Spaces requests so a run stays under a requests-per-minute ceiling."""

    def __init__(self, rpm: int):
        self.min_interval = 60.0 / rpm if rpm > 0 else 0.0
        self._last = 0.0

    def wait(self) -> None:
        if not self.min_interval:
            return
        remaining = self._last + self.min_interval - time.monotonic()
        if remaining > 0:
            time.sleep(remaining)
        self._last = time.monotonic()


def _classify_failure(exc: Exception, attempt: int) -> tuple[str | None, float]:
    """Decide whether a failure is worth another attempt, and how long to wait.

    Three cases hide behind superficially similar errors:
      daily     - the per-day cap. Waiting will not help before tomorrow.
      throttle  - the per-minute cap. The server tells us how long to wait.
      transient - a 5xx. The model is busy; back off exponentially.
    """
    text = str(exc)
    lowered = text.lower()

    if "429" in text or "RESOURCE_EXHAUSTED" in text or "rate limit" in lowered:
        if "PerDay" in text or "per day" in lowered:
            return "daily", 0.0
        match = RETRY_DELAY_PATTERN.search(text)
        return "throttle", (float(match.group(1)) + 1.0 if match else 20.0)

    transient = ("503" in text, "500" in text, "502" in text, "504" in text,
                 "UNAVAILABLE" in text, "overloaded" in lowered, "internal error" in lowered)
    if any(transient):
        return "transient", min(2.0 * (2**attempt), 30.0)

    return None, 0.0


def _call_with_retry(pacer: _Pacer, send: Callable[[], Any]) -> Any:
    """Pace the call, and retry the failures that are actually retryable."""
    for attempt in range(MAX_RETRIES):
        pacer.wait()
        try:
            return send()
        except Exception as exc:
            kind, delay = _classify_failure(exc, attempt)
            if kind == "daily":
                raise ProviderError(
                    "daily free-tier quota exhausted for this model - wait for the "
                    "reset or pass a different --model"
                ) from exc
            if kind is None or attempt == MAX_RETRIES - 1:
                raise ProviderError(f"{type(exc).__name__}: {exc}") from exc
            time.sleep(delay)
    raise ProviderError("exhausted retries")


# --------------------------------------------------------------- OpenAI

OPENAI_DEFAULT_MODEL = "gpt-5-codex"


class OpenAIConversation:
    def __init__(self, model: str, system: str, tools: list[ToolSpec], rpm: int = 0):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderError(
                "the openai package is not installed - pip install 'litmus[openai]'"
            ) from exc
        if not os.environ.get("OPENAI_API_KEY"):
            raise ProviderError("OPENAI_API_KEY is not set")

        self._client = OpenAI()
        self._model = model
        self._pacer = _Pacer(rpm)
        self._tools = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": {
                        "type": "object",
                        "properties": t.properties,
                        "required": t.required,
                    },
                },
            }
            for t in tools
        ]
        self._messages: list[dict[str, Any]] = [{"role": "system", "content": system}]

    def _complete(self) -> Reply:
        response = _call_with_retry(
            self._pacer,
            lambda: self._client.chat.completions.create(
                model=self._model, messages=self._messages, tools=self._tools
            ),
        )

        message = response.choices[0].message
        self._messages.append(message.model_dump(exclude_none=True))

        calls = [
            ToolCall(
                id=call.id,
                name=call.function.name,
                args=_safe_json(call.function.arguments),
            )
            for call in (message.tool_calls or [])
        ]
        return Reply(text=message.content or "", calls=calls)

    def send_user(self, text: str) -> Reply:
        self._messages.append({"role": "user", "content": text})
        return self._complete()

    def send_tool_results(self, results: list[ToolResult]) -> Reply:
        for result in results:
            self._messages.append(
                {"role": "tool", "tool_call_id": result.call.id, "content": result.content}
            )
        return self._complete()


# --------------------------------------------------------------- Gemini

# gemini-2.5-flash allows only 20 requests per DAY on the free tier, which one
# iterative task can exhaust. The 3.x Flash models are far more generous, so
# they are the sensible default for a benchmark that makes many calls.
GEMINI_DEFAULT_MODEL = "gemini-3.5-flash"


class GeminiConversation:
    """Drives Gemini with history held here rather than inside the SDK client.

    `chats.create` keeps the transcript on the client object, which would make
    swapping API keys mid-conversation lose everything said so far. Owning the
    contents list means rotating to a fresh key is just building a new client.
    """

    def __init__(self, model: str, system: str, tools: list[ToolSpec], rpm: int = DEFAULT_RPM):
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise ProviderError(
                "the google-genai package is not installed - pip install 'litmus[gemini]'"
            ) from exc

        self._genai = genai
        self._types = types
        self._model = model
        self._pool = gemini_pool()
        self._pacer = _Pacer(rpm)
        self._contents: list[Any] = []

        declarations = [
            types.FunctionDeclaration(
                name=t.name,
                description=t.description,
                parameters={
                    "type": "object",
                    "properties": t.properties,
                    "required": t.required,
                },
            )
            for t in tools
        ]

        self._config = types.GenerateContentConfig(
            system_instruction=system,
            tools=[types.Tool(function_declarations=declarations)],
            # We drive the loop ourselves; the SDK must not execute anything.
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )

    def _generate(self) -> Any:
        """Call the model, rotating keys when one is out of quota for the day."""
        while True:
            client = self._genai.Client(api_key=self._pool.current())
            try:
                return _call_with_retry(
                    self._pacer,
                    lambda: client.models.generate_content(
                        model=self._model, contents=self._contents, config=self._config
                    ),
                )
            except ProviderError as exc:
                exhausted = "daily" in str(exc) and "quota" in str(exc)
                if not exhausted:
                    raise
                spent = self._pool.label()
                if not self._pool.retire_and_rotate():
                    raise ProviderError(
                        f"every Gemini key is out of daily quota ({self._pool.size} tried)"
                    ) from exc
                print(f"    [{spent} exhausted, switching to {self._pool.label()}]")

    def _reply_from(self, response: Any) -> Reply:
        calls: list[ToolCall] = []
        for i, call in enumerate(getattr(response, "function_calls", None) or []):
            calls.append(
                ToolCall(
                    # Gemini does not always supply an id; the loop only needs
                    # it to pair results back to calls within one turn.
                    id=getattr(call, "id", None) or f"{call.name}-{i}",
                    name=call.name,
                    args=dict(call.args or {}),
                )
            )

        # Only read .text when the turn had no function calls - the SDK warns
        # loudly about non-text parts otherwise.
        text = ""
        if not calls:
            try:
                text = response.text or ""
            except (AttributeError, ValueError):
                text = ""
        return Reply(text=text, calls=calls)

    def _turn(self, content: Any) -> Reply:
        self._contents.append(content)
        response = self._generate()

        # Keep the model's own turn in history so the next call has context.
        candidates = getattr(response, "candidates", None) or []
        if candidates and getattr(candidates[0], "content", None) is not None:
            self._contents.append(candidates[0].content)

        return self._reply_from(response)

    def send_user(self, text: str) -> Reply:
        return self._turn(
            self._types.Content(role="user", parts=[self._types.Part.from_text(text=text)])
        )

    def send_tool_results(self, results: list[ToolResult]) -> Reply:
        parts = [
            self._types.Part.from_function_response(
                name=result.call.name, response={"result": result.content}
            )
            for result in results
        ]
        return self._turn(self._types.Content(role="user", parts=parts))


# ---------------------------------------------------------------- factory

PROVIDERS = {"openai", "gemini"}

DEFAULT_MODELS = {
    "openai": OPENAI_DEFAULT_MODEL,
    "gemini": GEMINI_DEFAULT_MODEL,
}


def open_conversation(
    provider: str, model: str, system: str, tools: list[ToolSpec], rpm: int = DEFAULT_RPM
) -> Conversation:
    if provider == "openai":
        return OpenAIConversation(model, system, tools, rpm=rpm)
    if provider == "gemini":
        return GeminiConversation(model, system, tools, rpm=rpm)
    raise ProviderError(f"unknown provider {provider!r}; expected one of {sorted(PROVIDERS)}")


def resolve_model(provider: str, requested: str | None) -> str:
    return requested or DEFAULT_MODELS.get(provider, "")


def _safe_json(raw: str | None) -> dict[str, Any]:
    try:
        parsed = json.loads(raw or "{}")
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}
