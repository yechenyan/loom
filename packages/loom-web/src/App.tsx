import { useEffect } from "react";
import { highlights, useCases } from "./content";
import { DocsPage } from "./DocsPage";
import { ExplorePage } from "./ExplorePage";
import { HeroStats } from "./HeroStats";
import { MinuteGuide } from "./MinuteGuide";
import { SiteHeader } from "./SiteHeader";

export function App() {
  useHashScroll();
  const path = window.location.pathname.replace(/\/$/, "") || "/";

  if (path === "/explore") {
    return <ExplorePage />;
  }

  if (path === "/docs" || path.startsWith("/docs/")) {
    return <DocsPage slug={path.slice("/docs/".length)} />;
  }

  return (
    <main className="site-shell">
      <SiteHeader />
      <Hero />
      <Intro />
      <MinuteGuide />
      <UseCases />
      <FinalCta />
    </main>
  );
}

function useHashScroll() {
  useEffect(() => {
    if (!window.location.hash) {
      return;
    }

    requestAnimationFrame(() => {
      const target = document.querySelector<HTMLElement>(window.location.hash);

      if (target) {
        window.scrollTo({ top: target.offsetTop - 110, behavior: "auto" });
      }
    });
  }, []);
}

function Hero() {
  return (
    <section className="hero" id="top">
      <div className="hero-copy">
        <p className="eyebrow">AI agents deserve a real data memory</p>
        <h1>
          <span>少花时间找数据、</span>
          <span>解释参数、</span>
          <span>确认来源。</span>
        </h1>
        <p className="hero-lede">
          Loom 把项目数据整理成可搜索的数据卡，让人和 AI 快速找到可信数据，
          并同步到云端共享复用。
        </p>
        <div className="hero-actions">
          <a className="primary-button" href="#minute">
            看 1 分钟用法
          </a>
          <a className="text-link" href="#what">
            Loom 是什么
          </a>
          <a className="text-link" href="/explore">
            数据探索
          </a>
          <a className="text-link" href="/docs">
            阅读文档
          </a>
        </div>
      </div>
      <div className="hero-visual" aria-label="Loom dataset overview">
        <HeroStats />
      </div>
    </section>
  );
}

function Intro() {
  return (
    <section className="intro-section" id="what">
      <div>
        <p className="section-kicker">它解决什么问题</p>
        <h2>给 AI 一个轻量、可追溯的数据地图。</h2>
      </div>
      <div className="intro-list">
        {highlights.map((item) => (
          <p key={item}>{item}</p>
        ))}
      </div>
    </section>
  );
}

function UseCases() {
  return (
    <section className="fit-section" id="fit">
      <p className="section-kicker">什么时候该用</p>
      <h2>当任务依赖本地数据事实时，让 Loom 先把路标立好。</h2>
      <div className="use-case-ribbon">
        {useCases.map((item) => (
          <span key={item}>{item}</span>
        ))}
      </div>
    </section>
  );
}

function FinalCta() {
  return (
    <section className="final-cta">
      <p>从一个数据目录开始，把“读数据”变成可验证的 agent 工作流。</p>
      <a className="primary-button" href="#minute">
        开始使用 Loom
      </a>
    </section>
  );
}
