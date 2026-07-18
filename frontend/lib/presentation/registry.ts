import {
  BookOpen,
  Briefcase,
  Database,
  FileText,
  History,
  Layers3,
  Settings2,
} from "lucide-react";

import type { AppManifest } from "@/lib/apps/types";
import type {
  ApplicationPresentation,
  LocalDestination,
} from "@/lib/presentation/types";

const destination = (
  label: string,
  href: string,
  icon: LocalDestination["icon"],
): LocalDestination => ({
  label,
  href,
  icon,
  matches: (pathname) =>
    pathname === href || pathname.startsWith(`${href}/`),
});

const presentations: readonly ApplicationPresentation[] = [
  {
    id: "knowledge-studio",
    name: "Knowledge Studio",
    shortName: "Knowledge",
    mainRoute: "/chat",
    routePrefixes: ["/chat", "/knowledge-base"],
    accent: "signal",
    media: {
      dark: "/images/cinematic/knowledge-dark.jpg",
      light: "/images/cinematic/knowledge-light.jpg",
      alt: "Layered archival material illuminated by connected evidence",
      focalPoint: "62% 42%",
    },
    headline: "Evidence becomes understanding.",
    localDestinations: [
      destination("Chat", "/chat", BookOpen),
      destination("History", "/chat?panel=history", History),
      destination("Documents", "/knowledge-base", FileText),
    ],
  },
  {
    id: "aurasql",
    name: "AuraSQL",
    shortName: "AuraSQL",
    mainRoute: "/aurasql",
    routePrefixes: ["/aurasql"],
    accent: "data",
    media: {
      dark: "/images/cinematic/aurasql-dark.jpg",
      light: "/images/cinematic/aurasql-light.jpg",
      alt: "Architectural data structures receding through luminous space",
      focalPoint: "70% 48%",
    },
    headline: "Ask the business. Inspect the truth.",
    localDestinations: [
      {
        ...destination("Query", "/aurasql", Database),
        matches: (pathname) => pathname === "/aurasql" || pathname === "/aurasql/query",
      },
      destination("History", "/aurasql/history", History),
      destination("Connections", "/aurasql/connections", Settings2),
      destination("Contexts", "/aurasql/contexts", Layers3),
      destination("Settings", "/aurasql/settings", Settings2),
    ],
  },
  {
    id: "analysis",
    name: "Data Analyst Studio",
    shortName: "Analysis",
    mainRoute: "/analysis",
    routePrefixes: ["/analysis"],
    accent: "copper",
    media: {
      dark: "/images/cinematic/analysis-dark.jpg",
      light: "/images/cinematic/analysis-light.jpg",
      alt: "Observed structures separating clear signal from surrounding complexity",
      focalPoint: "68% 38%",
    },
    headline: "See the signal inside the noise.",
    localDestinations: [
      destination("Analyze", "/analysis", FileText),
      destination("History", "/analysis/history", History),
    ],
  },
  {
    id: "career-studio",
    name: "Career Studio",
    shortName: "Career",
    mainRoute: "/career",
    routePrefixes: ["/career", "/nexus"],
    accent: "career",
    media: {
      dark: "/images/cinematic/career-dark.jpg",
      light: "/images/cinematic/career-light.jpg",
      alt: "Human craft and verified documents arranged as a precise professional narrative",
      focalPoint: "72% 44%",
    },
    headline: "Score honestly. Tailor deliberately. Create beautifully.",
    localDestinations: [
      destination("Career tools", "/career", Briefcase),
    ],
  },
];

const fallback: ApplicationPresentation = {
  id: "platform",
  name: "NexusMind",
  shortName: "Workspace",
  mainRoute: "/apps",
  routePrefixes: ["/apps", "/workflows"],
  accent: "neutral",
  media: {
    dark: "/images/cinematic/platform-dark.jpg",
    light: "/images/cinematic/platform-light.jpg",
    alt: "A precise cinematic system of connected workspaces",
    focalPoint: "65% 44%",
  },
  headline: "Choose an intent. Enter the system.",
  localDestinations: [],
};

export function presentationForApp(
  app: AppManifest,
): ApplicationPresentation {
  return (
    presentations.find(
      (item) => item.id === app.id || item.mainRoute === app.frontend_route,
    ) ?? {
      ...fallback,
      id: app.id,
      name: app.name,
      shortName: app.name,
      mainRoute: app.frontend_route,
    }
  );
}

export function presentationForPath(
  pathname: string,
): ApplicationPresentation {
  return (
    presentations
      .flatMap((item) =>
        item.routePrefixes.map((prefix) => ({ item, prefix })),
      )
      .filter(
        ({ prefix }) =>
          pathname === prefix || pathname.startsWith(`${prefix}/`),
      )
      .sort((a, b) => b.prefix.length - a.prefix.length)[0]?.item ?? fallback
  );
}

export const directApplicationRoute = (app: AppManifest): string =>
  app.frontend_route;
