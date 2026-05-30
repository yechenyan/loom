import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { I18nProvider } from "./i18n";
import "./styles/base.css";
import "./styles/layout.css";
import "./styles/sections.css";
import "./styles/hero.css";
import "./styles/chat.css";
import "./styles/closing.css";
import "./styles/explore.css";
import "./styles/explore-card.css";
import "./styles/explore-empty.css";
import "./styles/docs.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <I18nProvider>
      <App />
    </I18nProvider>
  </StrictMode>,
);
