import { useI18n } from "./i18n";
import { getAppHref } from "./routes";

const GITHUB_URL = "https://github.com/yechenyan/loom";

export function SiteHeader() {
  const { locale, localeNames, setLocale } = useI18n();

  const copy = {
    en: {
      brand: "Loom home",
      nav: "Main navigation",
      home: "Home",
      docs: "Docs",
      explore: "Explore",
      github: "GitHub",
      language: "Language",
    },
    de: {
      brand: "Loom Startseite",
      nav: "Hauptnavigation",
      home: "Start",
      docs: "Docs",
      explore: "Daten erkunden",
      github: "GitHub",
      language: "Sprache",
    },
    zh: {
      brand: "Loom 首页",
      nav: "主要导航",
      home: "首页",
      docs: "文档",
      explore: "数据探索",
      github: "GitHub",
      language: "语言",
    },
  }[locale];

  return (
    <header className="topbar" aria-label="Loom navigation">
      <a className="brand" href={getAppHref("/")} aria-label={copy.brand}>
        <span className="brand-mark">L</span>
        <span>Loom</span>
      </a>
      <nav className="nav-links" aria-label={copy.nav}>
        <a href={getAppHref("/")}>{copy.home}</a>
        <a href={getAppHref("/docs")}>{copy.docs}</a>
        <a href={getAppHref("/explore")}>{copy.explore}</a>
        <a href={GITHUB_URL} rel="noreferrer" target="_blank">
          {copy.github}
        </a>
      </nav>
      <label className="locale-picker">
        <span>{copy.language}</span>
        <select onChange={(event) => setLocale(event.target.value as typeof locale)} value={locale}>
          {Object.entries(localeNames).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>
    </header>
  );
}
