import { useState } from "react";
import { getExploreCopy } from "./exploreCopy";
import type { ExploreWorkspace } from "./exploreTypes";

export function WorkspaceDetail({
  copy,
  workspace,
}: {
  copy: ReturnType<typeof getExploreCopy>;
  workspace: ExploreWorkspace;
}) {
  return (
    <section className="detail-body">
      <DetailCommand
        label={copy.workspaceCommandLabel}
        modes={[
          { key: "agent", label: copy.agentModeLabel, value: `loom pull ${workspace.name}` },
          { key: "cli", label: copy.cliModeLabel, value: `loomcli pull ${workspace.name}` },
        ]}
      />
      <div className="datacard-hero">
        <p className="detail-path">{workspace.name}</p>
        <h2>{workspace.name}</h2>
      </div>
      <MarkdownSummary text={workspace.readme_markdown} />
    </section>
  );
}

export function DetailCommand({
  label,
  modes,
  value,
}: {
  label: string;
  modes?: { key: string; label: string; value: string }[];
  value?: string;
}) {
  const [activeMode, setActiveMode] = useState(modes?.[0]?.key || "default");
  const [status, setStatus] = useState<"copied" | "error" | "idle">("idle");
  const currentValue = modes?.find((mode) => mode.key === activeMode)?.value || value || "";

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(currentValue);
      setStatus("copied");
    } catch {
      setStatus("error");
    }

    window.setTimeout(() => setStatus("idle"), 1200);
  }

  return (
    <section className="detail-command" aria-label={label}>
      <div className="detail-command-row">
        <div className="detail-command-heading">
          <p>{label}</p>
          {modes?.length ? (
            <div className="detail-command-modes" aria-label={`${label} modes`}>
              {modes.map((mode) => (
                <button
                  className={mode.key === activeMode ? "active" : ""}
                  key={mode.key}
                  onClick={() => setActiveMode(mode.key)}
                  type="button"
                >
                  {mode.label}
                </button>
              ))}
            </div>
          ) : null}
        </div>
        <button className={`detail-copy-button${status !== "idle" ? ` ${status}` : ""}`} onClick={handleCopy} type="button">
          {status === "copied" ? "Copied" : status === "error" ? "Error" : "Copy"}
        </button>
      </div>
      <code>{currentValue}</code>
    </section>
  );
}

function MarkdownSummary({ text }: { text: string }) {
  return (
    <div className="markdown-summary">
      {text
        .split("\n")
        .filter((line) => line.trim())
        .slice(0, 18)
        .map((line) => (
          <p key={line}>{line.replace(/^#+\s*/, "").replace(/^- /, "")}</p>
        ))}
    </div>
  );
}
