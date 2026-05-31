import { MarkdownView } from "./DocsMarkdown";
import { getSiteCopy } from "./copy";
import { useI18n } from "./i18n";
import { getAppHref } from "./routes";
import { userDocs } from "./docsContent";
import { SiteHeader } from "./SiteHeader";

export function DocsPage({ slug }: { slug?: string }) {
  const { locale } = useI18n();
  const copy = getSiteCopy(locale).docs;
  const currentIndex = findDocIndex(slug);
  const currentDoc = userDocs[currentIndex];
  const previousDoc = userDocs[currentIndex - 1];
  const nextDoc = userDocs[currentIndex + 1];

  return (
    <main className="docs-shell">
      <SiteHeader />
      <section className="docs-hero">
        <p className="eyebrow">USER DOCUMENTATION</p>
        <h1>{copy.title}</h1>
        <p>
          {copy.descriptionPrefix}
          <code>docs/user</code>
          {copy.descriptionSuffix}
        </p>
      </section>
      <section className="docs-layout">
        <aside className="docs-sidebar" aria-label={copy.toc}>
          <strong>{copy.toc}</strong>
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
          <nav className="doc-pager" aria-label={copy.pager}>
            {previousDoc ? (
              <a href={getDocHref(previousDoc.slug)}>
                <span>{copy.previous}</span>
                {previousDoc.title}
              </a>
            ) : (
              <span />
            )}
            {nextDoc ? (
              <a href={getDocHref(nextDoc.slug)}>
                <span>{copy.next}</span>
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
  return getAppHref(`/docs/${slug}`);
}
