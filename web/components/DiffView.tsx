import type { CheatFlag } from "@/lib/report";

/** Evidence strings come from the detector as whitespace-collapsed source. */
function fingerprints(flags: CheatFlag[]): string[] {
  return flags
    .map((f) => f.evidence.replace(/…$/, "").replace(/\s+/g, " ").trim())
    .filter((e) => e.length >= 6)
    .map((e) => e.slice(0, 34));
}

export function DiffView({ patch, flags }: { patch: string; flags: CheatFlag[] }) {
  if (!patch.trim()) {
    return (
      <p className="px-5 py-8 text-center font-mono text-[12.5px] text-paper/35">
        the agent changed nothing
      </p>
    );
  }

  const marks = fingerprints(flags);
  const lines = patch.replace(/\n$/, "").split("\n");

  return (
    <div className="overflow-x-auto py-3">
      {lines.map((line, i) => {
        const kind = classify(line);
        const normalized = line.slice(1).replace(/\s+/g, " ").trim();
        const flagged =
          kind === "add" && marks.some((m) => normalized.includes(m));

        return (
          <code
            key={i}
            className={[
              "diff-line",
              flagged ? "diff-flagged" : "",
              !flagged && kind === "add" ? "diff-add" : "",
              !flagged && kind === "del" ? "diff-del" : "",
              kind === "meta" ? "diff-meta" : "",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            {line || " "}
          </code>
        );
      })}
    </div>
  );
}

function classify(line: string): "add" | "del" | "meta" | "ctx" {
  if (line.startsWith("+++") || line.startsWith("---") || line.startsWith("@@")) return "meta";
  if (line.startsWith("+")) return "add";
  if (line.startsWith("-")) return "del";
  return "ctx";
}
