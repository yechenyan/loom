const modules = import.meta.glob("../../../docs/user/*.md", {
  eager: true,
  import: "default",
  query: "?raw",
}) as Record<string, string>;

const preferredOrder = [
  "00-overview",
  "01-quickstart",
  "02-workspaces",
  "03-scan-and-review",
  "04-ask-and-fetch",
  "05-sync-and-raw-cache",
  "06-python-api",
  "07-command-reference",
  "08-faq",
];

export type UserDoc = {
  slug: string;
  title: string;
  sourcePath: string;
  content: string;
};

export const userDocs: UserDoc[] = Object.entries(modules)
  .map(([path, content]) => {
    const slug = path.split("/").pop()?.replace(/\.md$/, "") || path;

    return {
      slug,
      title: getTitle(content, slug),
      sourcePath: `docs/user/${slug}.md`,
      content,
    };
  })
  .sort((left, right) => {
    const leftIndex = preferredOrder.indexOf(left.slug);
    const rightIndex = preferredOrder.indexOf(right.slug);

    if (leftIndex !== -1 || rightIndex !== -1) {
      return normalizeIndex(leftIndex) - normalizeIndex(rightIndex);
    }

    return left.title.localeCompare(right.title);
  });

function getTitle(content: string, fallback: string) {
  const heading = content.match(/^#\s+(.+)$/m)?.[1]?.trim();
  return heading || fallback.replace(/-/g, " ");
}

function normalizeIndex(index: number) {
  return index === -1 ? Number.MAX_SAFE_INTEGER : index;
}
