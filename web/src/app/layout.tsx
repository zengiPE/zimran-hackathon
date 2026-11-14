import type { Metadata, Viewport } from "next";
import { Big_Shoulders, Courier_Prime, IBM_Plex_Sans } from "next/font/google";
import "./globals.css";

// The three Casefile fonts. Each one becomes a CSS variable used by casefile.css.
// Google merged "Big Shoulders Display" into "Big Shoulders" with an optical-size
// axis: the variable font covers weights 600–800, and big text gets the Display cut.
const display = Big_Shoulders({
  variable: "--font-display",
  weight: "variable",
  axes: ["opsz"],
  subsets: ["latin"],
  fallback: ["Arial Narrow", "sans-serif"],
  adjustFontFallback: false, // Next has no metrics for this new family yet
});

const body = IBM_Plex_Sans({
  variable: "--font-body",
  weight: ["400", "500", "600"],
  subsets: ["latin", "cyrillic", "cyrillic-ext"], // names in Russian and Kazakh (ә, қ, ң, ө, ұ, ү, і)
});

// Courier Prime has no Cyrillic: names like "Даулет" fall back to Courier New
// (also a typewriter face) instead of a random system font.
const type = Courier_Prime({
  variable: "--font-type",
  weight: ["400", "700"],
  subsets: ["latin"],
  fallback: ["Courier New", "monospace"],
  adjustFontFallback: false,
});

export const metadata: Metadata = {
  title: "Casefile",
  description: "A case your friends crack together, one clue a day.",
};

export const viewport: Viewport = {
  themeColor: "#e9d7a9",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable} ${type.variable}`}>
      <body>{children}</body>
    </html>
  );
}
