import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
// Импортируем наши глобальные компоненты
import Header from "./components/Header";
import Footer from "./components/Footer";

const inter = Inter({ subsets: ["latin", "cyrillic"] });

export const metadata: Metadata = {
  title: "KlarDeutsch",
  description: "Тренажер немецкого языка",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <body className={`${inter.className} min-h-screen flex flex-col bg-slate-50`}>
        {/* Глобальная шапка - будет на всех страницах */}
        <Header />

        {/* Основной контент страницы, растягивается чтобы прижать футер вниз */}
        <main className="flex-1 flex flex-col">
          {children}
        </main>

        {/* Глобальный подвал - будет на всех страницах */}
        <Footer />
      </body>
    </html>
  );
}
