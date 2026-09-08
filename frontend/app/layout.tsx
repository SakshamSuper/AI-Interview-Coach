import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { Providers } from "@/components/Providers";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AI Interview Coach — Adaptive GenAI & ML Platform",
  description:
    "Adaptive technical interview coaching platform powered by LangGraph, FAISS RAG, and Scikit-Learn.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} h-full`} suppressHydrationWarning>
      <body
        className="h-full text-slate-900 flex overflow-hidden antialiased font-sans"
        style={{ backgroundColor: "#F5F7FA" }}
        suppressHydrationWarning
      >
        <Providers>
          <Sidebar />
          <div className="flex-1 flex flex-col h-screen overflow-hidden">
            <Header />
            <main className="flex-1 overflow-y-auto" style={{ backgroundColor: "#F5F7FA" }}>
              <div className="max-w-6xl mx-auto px-6 py-6 space-y-6">
                {children}
              </div>
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
