"use client";

import { createContext, useContext, useMemo, useReducer } from "react";
import { initialShowcaseState, showcaseReducer } from "@/lib/showcase/reducer";
import type { ShowcaseScenario, ShowcaseState } from "@/lib/showcase/types";

interface Value {
  state: ShowcaseState;
  advance(): void;
  restart(): void;
}

const Context = createContext<Value | null>(null);

export function ShowcaseProvider({
  scenario,
  children,
}: {
  scenario: ShowcaseScenario;
  children: React.ReactNode;
}) {
  const [state, dispatch] = useReducer(showcaseReducer, scenario, initialShowcaseState);
  const value = useMemo(
    () => ({
      state,
      advance: () => dispatch({ type: "advance" }),
      restart: () => dispatch({ type: "restart" }),
    }),
    [state],
  );
  return <Context.Provider value={value}>{children}</Context.Provider>;
}

export function useShowcase() {
  const value = useContext(Context);
  if (!value) throw new Error("useShowcase must be used within ShowcaseProvider");
  return value;
}
