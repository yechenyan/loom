import { useEffect } from "react";
import { useAtomValue, useSetAtom } from "jotai";
import { Outlet } from "react-router-dom";
import { TopNav } from "../components/layout/TopNav";
import { exploreStateAtom, loadCatalogAtom } from "../state/exploreState";

export function AppShell() {
  const state = useAtomValue(exploreStateAtom);
  const loadCatalog = useSetAtom(loadCatalogAtom);

  useEffect(() => {
    if (state.workspaces.length === 0 && state.loading) {
      loadCatalog();
    }
  }, [loadCatalog, state.loading, state.workspaces.length]);

  return (
    <div className="app-shell">
      <div className="ambient ambient-left" />
      <div className="ambient ambient-right" />
      <TopNav />
      <Outlet />
    </div>
  );
}
