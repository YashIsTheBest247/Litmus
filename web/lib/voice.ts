/**
 * Browser voice: speech-to-text for asking, and a warm speech-synthesis voice
 * for the reply. Both are built into the browser — no backend, no key — so they
 * fit a static site and simply degrade to nothing where unsupported.
 */

// --- speech synthesis (the warm reply) -----------------------------------

// Names of voices that tend to sound natural and warm, in preference order.
// Browsers vary wildly in what they ship, so this is a soft preference with a
// sensible English fallback.
const WARM_VOICES = [
  "Samantha",
  "Google UK English Female",
  "Microsoft Aria",
  "Microsoft Jenny",
  "Google US English",
  "Microsoft Zira",
  "Karen",
  "Moira",
  "Serena",
];

let cachedVoice: SpeechSynthesisVoice | null = null;

function pickVoice(): SpeechSynthesisVoice | null {
  if (typeof window === "undefined" || !window.speechSynthesis) return null;
  const voices = window.speechSynthesis.getVoices();
  if (!voices.length) return null;
  if (cachedVoice && voices.includes(cachedVoice)) return cachedVoice;

  for (const name of WARM_VOICES) {
    const match = voices.find((v) => v.name.includes(name));
    if (match) return (cachedVoice = match);
  }
  // Prefer any local English voice; a female one if we can tell.
  const english = voices.filter((v) => v.lang.toLowerCase().startsWith("en"));
  cachedVoice =
    english.find((v) => /female|aria|jenny|zira|samantha|karen/i.test(v.name)) ??
    english[0] ??
    voices[0];
  return cachedVoice;
}

export function speechSupported(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}

export function cancelSpeech(): void {
  if (typeof window !== "undefined" && window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
}

/** Speak text in a warm, unhurried tone. */
export function speak(text: string): void {
  if (!speechSupported()) return;
  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  const voice = pickVoice();
  if (voice) utterance.voice = voice;
  // Slightly slower and a touch higher than default reads as warm and calm,
  // not robotic or rushed.
  utterance.rate = 0.97;
  utterance.pitch = 1.06;
  utterance.volume = 1;
  window.speechSynthesis.speak(utterance);
}

/** Voices load asynchronously in some browsers; warm the cache when they do. */
export function primeVoices(): void {
  if (!speechSupported()) return;
  pickVoice();
  window.speechSynthesis.onvoiceschanged = () => {
    cachedVoice = null;
    pickVoice();
  };
}

// --- speech recognition (talk to ask) ------------------------------------

type MinimalRecognition = {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  continuous: boolean;
  start: () => void;
  stop: () => void;
  onresult: ((e: unknown) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
};

export function recognitionSupported(): boolean {
  if (typeof window === "undefined") return false;
  return "SpeechRecognition" in window || "webkitSpeechRecognition" in window;
}

export function createRecognition(): MinimalRecognition | null {
  if (!recognitionSupported()) return null;
  const Ctor =
    (window as unknown as { SpeechRecognition?: new () => MinimalRecognition }).SpeechRecognition ??
    (window as unknown as { webkitSpeechRecognition?: new () => MinimalRecognition })
      .webkitSpeechRecognition;
  if (!Ctor) return null;

  const recognition = new Ctor();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  recognition.continuous = false;
  return recognition;
}

/** Pull the best transcript string out of a recognition result event. */
export function transcriptFrom(event: unknown): string {
  try {
    const results = (event as { results: ArrayLike<ArrayLike<{ transcript: string }>> }).results;
    return results?.[0]?.[0]?.transcript ?? "";
  } catch {
    return "";
  }
}
