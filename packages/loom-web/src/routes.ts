export type AppRoute = {
  anchor: string | null;
  path: "/" | `/${string}`;
};

export function parseAppRoute(hash: string): AppRoute {
  if (!hash || hash === "#") {
    return { path: "/", anchor: null };
  }

  if (hash.startsWith("#/")) {
    const path = normalizePath(hash.slice(1));
    return { path, anchor: null };
  }

  return { path: "/", anchor: hash.slice(1) || null };
}

export function getAppHref(path: string) {
  return `#${normalizePath(path)}`;
}

export function getSectionHref(anchor: string) {
  return `#${anchor.replace(/^#/, "")}`;
}

function normalizePath(path: string): "/" | `/${string}` {
  if (!path || path === "/") {
    return "/";
  }

  const normalized = path.startsWith("/") ? path : `/${path}`;
  return normalized.replace(/\/+$/, "") as `/${string}`;
}
