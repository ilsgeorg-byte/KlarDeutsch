"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpen, Menu, X, LogOut, User } from "lucide-react";
import { useState, useEffect } from "react";

export default function Header() {
    const pathname = usePathname();
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [isMounted, setIsMounted] = useState(false);

    useEffect(() => {
        setIsMounted(true);
    }, []);

    // Закрываем меню при смене страницы
    useEffect(() => {
        setIsMenuOpen(false);
    }, [pathname]);

    // Блокируем скролл страницы, когда открыто мобильное меню
    useEffect(() => {
        if (isMenuOpen) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = 'unset';
        }
        return () => {
            document.body.style.overflow = 'unset';
        };
    }, [isMenuOpen]);

    const navLinks = [
        { href: "/", label: "Главная" },
        { href: "/dictionary", label: "Словарь" },
        { href: "/trainer", label: "Тренажер" },
        { href: "/diary", label: "Дневник" },
    ];

    const isActive = (path: string) => {
        if (path === '/' && pathname !== '/') return false;
        return pathname?.startsWith(path);
    };

    if (!isMounted) return null;

    return (
        <header className="w-full bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between overflow-x-hidden w-full gap-2">


                {/* Логотип */}
                <Link href="/" className="flex items-center gap-2 z-50">
                    <div className="bg-blue-600 text-white p-1.5 rounded-lg">
                        <BookOpen size={20} />
                    </div>
                    <span className="text-xl font-bold text-slate-800 tracking-tight">
                        Klar<span className="text-blue-600">Deutsch</span>
                    </span>
                </Link>

                {/* Десктопная навигация */}
                <nav className="hidden md:flex items-center gap-8">
                    {navLinks.map((link) => (
                        <Link
                            key={link.href}
                            href={link.href}
                            className={`text-sm font-semibold transition-colors py-2 ${isActive(link.href)
                                ? "text-blue-600 border-b-2 border-blue-600"
                                : "text-slate-600 hover:text-blue-600"
                                }`}
                        >
                            {link.label}
                        </Link>
                    ))}
                </nav>

                {/* Десктопный профиль */}
                <div className="hidden md:flex items-center gap-4">
                    <button className="flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-blue-600 transition-colors">
                        <User size={18} />
                        Профиль
                    </button>
                    <button className="flex items-center gap-2 text-sm font-semibold text-red-500 hover:text-red-600 transition-colors bg-red-50 hover:bg-red-100 px-3 py-1.5 rounded-lg">
                        <LogOut size={16} />
                        Выйти
                    </button>
                </div>

                {/* Мобильная кнопка меню */}

                <button
                    className="md:hidden p-2 text-slate-600 hover:bg-slate-100 rounded-lg z-50 flex-shrink-0 ml-auto"

                    onClick={() => setIsMenuOpen(!isMenuOpen)}
                    aria-label="Toggle menu"
                >
                    {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
                </button>

                {/* Мобильное выпадающее меню */}
                <div className={`
                    fixed inset-0 bg-white z-40 transform transition-transform duration-300 ease-in-out pt-20 flex flex-col md:hidden
                    ${isMenuOpen ? "translate-x-0" : "translate-x-full"}
                `}>
                    <nav className="flex flex-col px-6 gap-2">
                        {navLinks.map((link) => (
                            <Link
                                key={link.href}
                                href={link.href}
                                className={`text-lg font-semibold py-4 border-b border-slate-100 flex items-center ${isActive(link.href)
                                    ? "text-blue-600"
                                    : "text-slate-700"
                                    }`}
                            >
                                {link.label}
                            </Link>
                        ))}
                    </nav>

                    <div className="mt-auto px-6 py-8 flex flex-col gap-4 bg-slate-50 border-t border-slate-200">
                        <button className="flex items-center justify-center gap-2 w-full py-3 bg-white border border-slate-200 text-slate-700 rounded-xl font-semibold shadow-sm">
                            <User size={18} />
                            Профиль
                        </button>
                        <button className="flex items-center justify-center gap-2 w-full py-3 bg-red-50 text-red-600 rounded-xl font-semibold">
                            <LogOut size={18} />
                            Выйти
                        </button>
                    </div>
                </div>

            </div>
        </header>
    );
}
