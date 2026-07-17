import type { Metadata } from "next";
import { IBM_Plex_Mono, Newsreader, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { ClientProviders } from "@/components/layout/ClientProviders";
import { RouteProviders } from "@/components/layout/RouteProviders";
import { themeBootstrapScript } from "@/lib/appearance";

const space = Space_Grotesk({ subsets: ["latin"], variable: "--font-space-grotesk", display: "swap" });
const newsreader = Newsreader({
  subsets: ["latin"],
  variable: "--font-newsreader",
  display: "swap",
  style: ["normal", "italic"],
  adjustFontFallback: false,
});
const mono = IBM_Plex_Mono({ subsets: ["latin"], variable: "--font-ibm-plex-mono", weight: ["400", "600"], display: "swap" });

export const metadata: Metadata = {
  title: { default: "NexusMind — Intelligence made tangible", template: "%s · NexusMind" },
  description: "Grounded research, data intelligence, and high-stakes output in one authored AI system.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className={`${space.variable} ${newsreader.variable} ${mono.variable}`}>
      <head><script dangerouslySetInnerHTML={{ __html: themeBootstrapScript }} /></head>
      <body>
        <ClientProviders>
          <RouteProviders>{children}</RouteProviders>
        </ClientProviders>
      </body>
    </html>
  );
}
