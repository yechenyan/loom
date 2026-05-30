import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/", label: "首页", end: true },
  { to: "/explore", label: "探索数据" },
];

export function TopNav() {
  return (
    <header className="top-nav">
      <div className="brand">
        <span className="brand-mark">loom</span>
        <span className="brand-sub">让 AI 先读数据卡，再按需读取原始文件</span>
      </div>
      <nav className="nav-tabs" aria-label="主导航">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) => (isActive ? "nav-tab active" : "nav-tab")}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}
