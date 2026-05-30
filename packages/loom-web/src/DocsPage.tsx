import { MarkdownView } from "./DocsMarkdown";
import { userDocs } from "./docsContent";
import { SiteHeader } from "./SiteHeader";

export function DocsPage({ slug }: { slug?: string }) {
  const currentIndex = findDocIndex(slug);
  const currentDoc = userDocs[currentIndex];
  const previousDoc = userDocs[currentIndex - 1];
  const nextDoc = userDocs[currentIndex + 1];

  return (
    <main className="docs-shell">
      <SiteHeader />
      <section className="docs-hero">
        <p className="eyebrow">USER DOCUMENTATION</p>
        <h1>从仓库文档直接生成的 Loom 使用指南。</h1>
        <p>
          这里读取根目录 <code>docs/user</code> 下的 Markdown。更新这些源文件后，
          文档页会在开发服务器或下一次构建中同步更新。
        </p>
      </section>
      <section className="docs-layout">
        <aside className="docs-sidebar" aria-label="文档目录">
          <strong>目录</strong>
          {userDocs.map((doc) => (
            <a
              aria-current={doc.slug === currentDoc.slug ? "page" : undefined}
              className={doc.slug === currentDoc.slug ? "active" : undefined}
              href={getDocHref(doc.slug)}
              key={doc.slug}
            >
              {doc.title}
            </a>
          ))}
        </aside>
        <article className="doc-article" id={currentDoc.slug}>
          <p className="doc-source">{currentDoc.sourcePath}</p>
          <MarkdownView source={currentDoc.content} />
          <nav className="doc-pager" aria-label="文档翻页">
            {previousDoc ? (
              <a href={getDocHref(previousDoc.slug)}>
                <span>上一篇</span>
                {previousDoc.title}
              </a>
            ) : (
              <span />
            )}
            {nextDoc ? (
              <a href={getDocHref(nextDoc.slug)}>
                <span>下一篇</span>
                {nextDoc.title}
              </a>
            ) : null}
          </nav>
        </article>
      </section>
    </main>
  );
}

function findDocIndex(slug?: string) {
  if (!slug) {
    return 0;
  }

  const index = userDocs.findIndex((doc) => doc.slug === slug);
  return index === -1 ? 0 : index;
}

function getDocHref(slug: string) {
  return `/docs/${slug}`;
}
