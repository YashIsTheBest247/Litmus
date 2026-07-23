import type { Metadata } from "next";
import { IBM_Plex_Mono, Plus_Jakarta_Sans } from "next/font/google";

import { PageTransition } from "@/components/PageTransition";
import { SITE_URL } from "@/lib/site";

import "./globals.css";

const sans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
  style: ["normal", "italic"],
  variable: "--font-sans",
  display: "swap",
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono",
  display: "swap",
});

const DESCRIPTION =
  "Coding agents are graded on tests they can read. Litmus grades them on a suite they never see, and reports the distance between the two scores.";

export const metadata: Metadata = {
  // Needed so social preview URLs resolve to absolute addresses.
  metadataBase: new URL(SITE_URL),
  title: "Litmus",
  description: DESCRIPTION,
  openGraph: {
    title: "Litmus — held-out grading for coding agents",
    description: DESCRIPTION,
    type: "website",
    siteName: "Litmus",
  },
  twitter: {
    card: "summary_large_image",
    title: "Litmus — held-out grading for coding agents",
    description: DESCRIPTION,
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${sans.variable} ${mono.variable}`}>
        <PageTransition>{children}</PageTransition>
      </body>
    </html>
  );
}
