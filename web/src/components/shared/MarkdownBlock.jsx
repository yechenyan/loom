export function MarkdownBlock({ markdown }) {
  const lines = String(markdown ?? "")
    .split("\n")
    .map((line) => line.trimEnd())
    .filter((line, index, all) => !(line === "" && all[index - 1] === ""));

  return (
    <div className="markdown-block">
      {lines.map((line, index) => {
        if (line.startsWith("# ")) {
          return <h3 key={index}>{line.slice(2)}</h3>;
        }
        if (line.startsWith("## ")) {
          return <h4 key={index}>{line.slice(3)}</h4>;
        }
        if (line.startsWith("- ")) {
          return (
            <p key={index} className="markdown-bullet">
              {line}
            </p>
          );
        }
        if (!line) {
          return <div key={index} className="markdown-spacer" />;
        }
        return <p key={index}>{line}</p>;
      })}
    </div>
  );
}
