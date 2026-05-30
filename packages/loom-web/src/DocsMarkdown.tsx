import type { ReactNode } from "react";

type MarkdownBlock =
  | { type: "code"; code: string; language: string }
  | { type: "heading"; depth: number; text: string }
  | { type: "list"; ordered: boolean; items: string[] }
  | { type: "paragraph"; text: string };

export function MarkdownView({ source }: { source: string }) {
  return <>{parseMarkdown(source).map(renderBlock)}</>;
}

function renderBlock(block: MarkdownBlock, index: number) {
  if (block.type === "heading") {
    const Heading = `h${Math.min(block.depth, 3)}` as "h1" | "h2" | "h3";
    return <Heading key={index}>{renderInline(block.text)}</Heading>;
  }

  if (block.type === "code") {
    return (
      <pre className="doc-code" key={index}>
        <code>{block.code}</code>
      </pre>
    );
  }

  if (block.type === "list") {
    const List = block.ordered ? "ol" : "ul";
    return (
      <List key={index}>
        {block.items.map((item, itemIndex) => (
          <li key={`${item}-${itemIndex}`}>{renderInline(item)}</li>
        ))}
      </List>
    );
  }

  return <p key={index}>{renderInline(block.text)}</p>;
}

function parseMarkdown(source: string) {
  const blocks: MarkdownBlock[] = [];
  const lines = source.split(/\r?\n/);
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];

    if (!line.trim()) {
      index += 1;
      continue;
    }

    const fence = line.match(/^```(\w*)/);
    if (fence) {
      const codeLines: string[] = [];
      index += 1;

      while (index < lines.length && !lines[index].startsWith("```")) {
        codeLines.push(lines[index]);
        index += 1;
      }

      blocks.push({ type: "code", language: fence[1] || "", code: codeLines.join("\n") });
      index += 1;
      continue;
    }

    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      blocks.push({ type: "heading", depth: heading[1].length, text: heading[2] });
      index += 1;
      continue;
    }

    const ordered = line.match(/^\d+\.\s+(.+)$/);
    const unordered = line.match(/^[-*]\s+(.+)$/);
    if (ordered || unordered) {
      const items: string[] = [];
      const orderedList = Boolean(ordered);

      while (index < lines.length) {
        const item = lines[index].match(orderedList ? /^\d+\.\s+(.+)$/ : /^[-*]\s+(.+)$/);

        if (!item) {
          break;
        }

        items.push(item[1]);
        index += 1;
      }

      blocks.push({ type: "list", ordered: orderedList, items });
      continue;
    }

    const paragraph: string[] = [];
    while (index < lines.length && isParagraphLine(lines[index])) {
      paragraph.push(lines[index].trim());
      index += 1;
    }

    blocks.push({ type: "paragraph", text: paragraph.join(" ") });
  }

  return blocks;
}

function isParagraphLine(line: string) {
  return (
    Boolean(line.trim()) &&
    !line.startsWith("```") &&
    !line.match(/^(#{1,6})\s+(.+)$/) &&
    !line.match(/^\d+\.\s+(.+)$/) &&
    !line.match(/^[-*]\s+(.+)$/)
  );
}

function renderInline(text: string) {
  const nodes: ReactNode[] = [];
  const pattern = /(`[^`]+`)|\[([^\]]+)\]\(([^)]+)\)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(text))) {
    if (match.index > lastIndex) {
      nodes.push(text.slice(lastIndex, match.index));
    }

    if (match[1]) {
      nodes.push(<code key={nodes.length}>{match[1].slice(1, -1)}</code>);
    } else {
      nodes.push(
        <a href={match[3]} key={nodes.length}>
          {match[2]}
        </a>,
      );
    }

    lastIndex = pattern.lastIndex;
  }

  if (lastIndex < text.length) {
    nodes.push(text.slice(lastIndex));
  }

  return nodes;
}
