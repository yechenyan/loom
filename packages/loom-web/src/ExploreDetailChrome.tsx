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
      <DetailCommand label={copy.workspaceCommandLabel} value={`loom pull ${workspace.name}`} />
      <div className="datacard-hero">
        <p className="detail-path">{workspace.name}</p>
        <h2>{workspace.name}</h2>
      </div>
      <MarkdownSummary text={workspace.readme_markdown} />
    </section>
  );
}

export function DetailCommand({ label, value }: { label: string; value: string }) {
  return (
    <section className="detail-command" aria-label={label}>
      <p>{label}</p>
      <code>{value}</code>
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
