import type { LucideIcon } from "lucide-react";

export type ApplicationAccent =
  | "signal"
  | "data"
  | "copper"
  | "career"
  | "neutral";

export interface LocalDestination {
  label: string;
  href: string;
  icon: LucideIcon;
  matches(pathname: string): boolean;
}

export interface ApplicationPresentation {
  id: string;
  name: string;
  shortName: string;
  mainRoute: string;
  routePrefixes: readonly string[];
  accent: ApplicationAccent;
  media: {
    dark: string;
    light: string;
    alt: string;
    focalPoint: string;
  };
  headline: string;
  localDestinations: readonly LocalDestination[];
}
