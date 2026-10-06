import type { Metadata, Viewport } from "next";
import { Nunito } from "next/font/google";
import Providers from "@/components/Providers";
import "./globals.css";

const nunito = Nunito({ variable: "--font-nunito", subsets: ["latin", "latin-ext"], weight: ["600", "700", "800", "900"] });

export const metadata: Metadata = {
  title: "Duolingo Clone · with an adaptive AI tutor",
  description: "A Duolingo-style Spanish course with an agentic tutor that adapts to your mistakes.",
};

export const viewport: Viewport = { themeColor: "#58CC02", width: "device-width", initialScale: 1 };

// Apply the saved theme before paint to avoid a light flash in dark mode.
const themeScript = `try{if(localStorage.getItem('duo_theme')==='dark')document.documentElement.dataset.theme='dark'}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${nunito.variable} h-full antialiased`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="min-h-full">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
