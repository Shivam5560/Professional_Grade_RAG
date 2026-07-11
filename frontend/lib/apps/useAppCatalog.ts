"use client";

import { useCallback, useEffect, useRef, useState } from "react";

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

export function useAppCatalog(): CatalogState {
  const [state, setState] = useState<CatalogSnapshot>({
    status: "loading",
    apps: [],
    error: null,
  });
  const mountedRef = useRef(false);
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
    void load();

    return () => {
      mountedRef.current = false;
      requestIdRef.current += 1;
    };
  }, [load]);

  return { ...state, retry: load };
}
