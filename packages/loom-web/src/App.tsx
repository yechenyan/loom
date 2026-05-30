import { useEffect, useState } from "react";
import { getHighlights, getUseCases } from "./content";
import { getSiteCopy } from "./copy";
import { DocsPage } from "./DocsPage";
import { ExplorePage } from "./ExplorePage";
import { HeroStats } from "./HeroStats";
import { useI18n } from "./i18n";
import { MinuteGuide } from "./MinuteGuide";
import { getAppHref, getSectionHref, parseAppRoute } from "./routes";
import { SiteHeader } from "./SiteHeader";

export function App() {
  const route = useHashRoute();
  useHashScroll(route.anchor);
  const { locale } = useI18n();
  const path = route.path;

  if (path === "/explore") {
    return <ExplorePage />;
  }

  if (path === "/docs" || path.startsWith("/docs/")) {
    return <DocsPage slug={path.slice("/docs/".length)} />;
  }

  const copy = getSiteCopy(locale).home;

  return (
    <main className="site-shell">
      <SiteHeader />
      <Hero copy={copy} />
      <Intro copy={copy} />
      <MinuteGuide />
      <UseCases copy={copy} />
      <FinalCta copy={copy} />
    </main>
  );
}

function useHashRoute() {
  const [route, setRoute] = useState(() => parseAppRoute(window.location.hash));

  useEffect(() => {
    const syncRoute = () => setRoute(parseAppRoute(window.location.hash));

    window.addEventListener("hashchange", syncRoute);
    return () => window.removeEventListener("hashchange", syncRoute);
  }, []);

  return route;
}

function useHashScroll(anchor: string | null) {
  useEffect(() => {
    if (!anchor) {
      window.scrollTo({ top: 0, behavior: "auto" });
      return;
    }

    requestAnimationFrame(() => {
      const target = document.getElementById(anchor);
      if (target) {
        window.scrollTo({ top: target.offsetTop - 110, behavior: "auto" });
      }
    });
  }, [anchor]);
}

function Hero({ copy }: { copy: ReturnType<typeof getSiteCopy>["home"] }) {
  return (
    <section className="hero" id="top">
      <div className="hero-copy">
        <p className="eyebrow">{copy.eyebrow}</p>
        <h1>
          {copy.heroTitle.map((item) => (
            <span key={item}>{item}</span>
          ))}
        </h1>
        <p className="hero-lede">{copy.heroLede}</p>
        <div className="hero-actions">
          <a className="primary-button" href={getSectionHref("minute")}>
            {copy.minute}
          </a>
          <a className="text-link" href={getSectionHref("what")}>
            {copy.what}
          </a>
          <a className="text-link" href={getAppHref("/explore")}>
            {copy.explore}
          </a>
          <a className="text-link" href={getAppHref("/docs")}>
            {copy.docs}
          </a>
        </div>
      </div>
      <div className="hero-visual" aria-label="Loom dataset overview">
        <HeroStats />
      </div>
    </section>
  );
}

function Intro({ copy }: { copy: ReturnType<typeof getSiteCopy>["home"] }) {
  const { locale } = useI18n();
  const highlights = getHighlights(locale);

  return (
    <section className="intro-section" id="what">
      <div>
        <p className="section-kicker">{copy.introKicker}</p>
        <h2>{copy.introTitle}</h2>
      </div>
      <div className="intro-list">
        {highlights.map((item) => (
          <p key={item}>{item}</p>
        ))}
      </div>
    </section>
  );
}

function UseCases({ copy }: { copy: ReturnType<typeof getSiteCopy>["home"] }) {
  const { locale } = useI18n();
  const useCases = getUseCases(locale);

  return (
    <section className="fit-section" id="fit">
      <p className="section-kicker">{copy.fitKicker}</p>
      <h2>{copy.fitTitle}</h2>
      <div className="use-case-ribbon">
        {useCases.map((item) => (
          <span key={item}>{item}</span>
        ))}
      </div>
    </section>
  );
}

function FinalCta({ copy }: { copy: ReturnType<typeof getSiteCopy>["home"] }) {
  return (
    <section className="final-cta">
      <p>{copy.cta}</p>
      <a className="primary-button" href={getSectionHref("minute")}>
        {copy.ctaButton}
      </a>
    </section>
  );
}
