"use client";

import {
  createContext,
  createElement,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { listApps } from "./client";
import type { AppManifest } from "./types";

type RetryCatalog = () => Promise<void>;

export type CatalogState =
  | { status: "loading"; apps: []; error: null; retry: RetryCatalog }
  | { status: "empty"; apps: []; error: null; retry: RetryCatalog }
  | {
      status: "success";
      apps: AppManifest[];
      error: null;
      retry: RetryCatalog;
    }
  | { status: "error"; apps: []; error: Error; retry: RetryCatalog };

type CatalogSnapshot =
  | { status: "loading"; apps: []; error: null }
  | { status: "empty"; apps: []; error: null }
  | { status: "success"; apps: AppManifest[]; error: null }
  | { status: "error"; apps: []; error: Error };

const AppCatalogContext = createContext<CatalogState | null>(null);

export function isAppEnabled(
  catalog: CatalogState,
  appId: AppManifest["id"],
): boolean {
  return (
    catalog.status === "success" &&
    catalog.apps.some((app) => app.id === appId)
  );
}

export function AppCatalogProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<CatalogSnapshot>({
    status: "loading",
    apps: [],
    error: null,
  });
  const mountedRef = useRef(false);
  const initialLoadStartedRef = useRef(false);
  const requestIdRef = useRef(0);

  const load = useCallback(async () => {
    const requestId = ++requestIdRef.current;

    if (mountedRef.current) {
      setState({ status: "loading", apps: [], error: null });
    }

    try {
      const catalog = await listApps();

      if (!mountedRef.current || requestId !== requestIdRef.current) {
        return;
      }

      setState(
        catalog.length === 0
          ? { status: "empty", apps: [], error: null }
          : { status: "success", apps: catalog, error: null },
      );
    } catch (reason) {
      if (!mountedRef.current || requestId !== requestIdRef.current) {
        return;
      }

      setState({
        status: "error",
        apps: [],
        error:
          reason instanceof Error
            ? reason
            : new Error("Unable to load applications"),
      });
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;

    if (!initialLoadStartedRef.current) {
      initialLoadStartedRef.current = true;
      void load();
    }

    return () => {
      mountedRef.current = false;
    };
  }, [load]);

  const catalog = useMemo<CatalogState>(
    () => ({ ...state, retry: load }),
    [load, state],
  );

  return createElement(AppCatalogContext.Provider, { value: catalog }, children);
}

export function useAppCatalog(): CatalogState {
  const catalog = useContext(AppCatalogContext);

  if (catalog === null) {
    throw new Error(
      "useAppCatalog must be used within an AppCatalogProvider",
    );
  }

  return catalog;
}
