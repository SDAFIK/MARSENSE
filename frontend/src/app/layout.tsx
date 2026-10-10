import type { Metadata } from "next";
import "maplibre-gl/dist/maplibre-gl.css";
import "./globals.css";
import "./mission-console.css";
import "./visual-recovery.css";
import "./showcase.css";
export const metadata: Metadata = {
  title: "MARSENSE · The Living Mars Map",
  description:
    "A Mars map that learns from every astronaut. Evidence, human verification, and exploration memory.",
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
