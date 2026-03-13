import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
// Импортируем наши глобальные компоненты
import Header from "./components/Header";
import Footer from "./components/Footer";
import { ThemeProvider } from "./context/ThemeContext";

// Оптимизированная загрузка шрифтов
const inter = Inter({
  subsets: ["latin", "cyrillic"],
  display: "swap", // Показывать fallback шрифт пока загружается
  preload: true, // Предзагрузка
  fallback: ["system-ui", "arial"], // Fallback шрифты
  variable: "--font-inter", // CSS переменная для шрифта
});

export const metadata: Metadata = {
  title: "KlarDeutsch - Тренажёр немецкого языка",
  description: "Изучайте немецкий язык эффективно с помощью интерактивных упражнений, словарных карточек и алгоритма SM-2 для запоминания слов.",
  keywords: ["немецкий язык", "учить немецкий", "слова", "тренажёр", "Deutsch lernen", "Vokabeln"],
  authors: [{ name: "KlarDeutsch Team" }],
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'),
  openGraph: {
    title: "KlarDeutsch - Тренажёр немецкого языка",
    description: "Изучайте немецкий язык эффективно",
    type: "website",
    locale: "ru_RU",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" suppressHydrationWarning className={inter.variable}>
      <body className={`${inter.className} min-h-screen flex flex-col bg-slate-50 dark:bg-gray-900 transition-colors duration-300`}>
        <ThemeProvider>
          {/* Глобальная шапка - будет на всех страницах */}
          <Header />

          {/* Основной контент страницы, растягивается чтобы прижать футер вниз */}
          <main className="flex-1 flex flex-col">
            {children}
          </main>

          {/* Глобальный подвал - будет на всех страницах */}
          <Footer />
        </ThemeProvider>
      </body>
    </html>
  );
}
