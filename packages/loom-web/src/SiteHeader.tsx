import { useI18n } from "./i18n";

export function SiteHeader() {
  const { locale, localeNames, setLocale } = useI18n();

  const copy = {
    en: {
      brand: "Loom home",
      nav: "Main navigation",
      home: "Home",
      docs: "Docs",
      explore: "Explore",
      language: "Language",
    },
    de: {
      brand: "Loom Startseite",
      nav: "Hauptnavigation",
      home: "Start",
      docs: "Docs",
      explore: "Daten erkunden",
      language: "Sprache",
    },
    zh: {
      brand: "Loom 首页",
      nav: "主要导航",
      home: "首页",
      docs: "文档",
      explore: "数据探索",
      language: "语言",
    },
  }[locale];

  return (
    <header className="topbar" aria-label="Loom navigation">
      <a className="brand" href="/" aria-label={copy.brand}>
        <span className="brand-mark">L</span>
        <span>Loom</span>
      </a>
      <nav className="nav-links" aria-label={copy.nav}>
        <a href="/">{copy.home}</a>
        <a href="/docs">{copy.docs}</a>
        <a href="/explore">{copy.explore}</a>
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
