"use client";

import Link from "next/link";
import { BookOpen, Menu, X, LogOut, User, Moon, Sun, Sparkles } from "lucide-react";
import { useState, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useTheme } from "../context/ThemeContext";

export default function Header() {
    const pathname = usePathname();
    const router = useRouter();
    const { theme, toggleTheme } = useTheme();
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [isMounted, setIsMounted] = useState(false);
    const [scrolled, setScrolled] = useState(false);
    const [isAuthenticated, setIsAuthenticated] = useState(false); // New state for authentication

    useEffect(() => {
        setIsMounted(true);
        const handleScroll = () => setScrolled(window.scrollY > 20);
        window.addEventListener("scroll", handleScroll);

        // Check authentication status on mount
        const token = localStorage.getItem("token");
        if (token) {
            setIsAuthenticated(true);
        }

        return () => {
            window.removeEventListener("scroll", handleScroll);
        };
    }, []);

    const handleLogout = () => {
        localStorage.removeItem("token");
        setIsAuthenticated(false); // Update auth state
        setIsMenuOpen(false);
        router.push("/login");
    };

    const handleLogin = () => {
        setIsMenuOpen(false);
        router.push("/login");
    };

    const handleRegister = () => {
        setIsMenuOpen(false);
        router.push("/register");
    };

    useEffect(() => {
        setIsMenuOpen(false); // This closes the mobile menu
        // Re-check authentication status when pathname changes
        const token = localStorage.getItem("token");
        setIsAuthenticated(!!token); // Update state based on token presence
    }, [pathname]); // Dependency on pathname

    useEffect(() => {
        if (isMenuOpen) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = 'unset';
        }
    }, [isMenuOpen]);

    // Define nav links, filter based on authentication status
    const allNavLinks = [
        { href: "/", label: "Главная" },
        { href: "/dictionary", label: "Словарь" },
        { href: "/trainer", label: "Тренажер" },
        { href: "/diary", label: "Записи" },
    ];

    const displayedNavLinks = isAuthenticated
        ? allNavLinks
        : allNavLinks.filter(link => link.href === "/"); // Only show "Главная" if not authenticated

    const isActive = (path: string) => {
        if (path === '/' && pathname !== '/') return false;
        return pathname?.startsWith(path);
    };

    if (!isMounted) return null;

    return (
        <header className={`w-full sticky top-0 z-[100] transition-all duration-300 ${
            scrolled
            ? "bg-white/80 dark:bg-slate-950/80 backdrop-blur-xl border-b border-slate-200/60 dark:border-slate-800/60 shadow-lg shadow-slate-200/20 dark:shadow-none py-2"
            : "bg-transparent py-4"
        }`}>
            <div className="max-w-7xl mx-auto px-6 flex items-center justify-between gap-4">

                {/* Логотип */}
                <Link href="/" className="flex items-center gap-2.5 group transition-transform active:scale-95">
                    <div className="bg-indigo-600 dark:bg-indigo-500 text-white p-2 rounded-xl shadow-lg shadow-indigo-200 dark:shadow-none group-hover:rotate-6 transition-transform">
                        <Sparkles size={20} />
                    </div>
                    <span className="text-xl font-black text-slate-900 dark:text-white tracking-tight">
                        Klar<span className="text-indigo-600 dark:text-indigo-400">Deutsch</span>
                    </span>
                </Link>

                {/* Десктопная навигация */}
                <nav className="hidden md:flex items-center bg-slate-100/50 dark:bg-slate-800/50 p-1.5 rounded-2xl border border-slate-200/50 dark:border-slate-700/50 backdrop-blur-sm">
                    {displayedNavLinks.map((link) => ( // Use filtered links
                        <Link
                            key={link.href}
                            href={link.href}
                            className={`px-5 py-2 text-sm font-bold rounded-xl transition-all duration-200 ${
                                isActive(link.href)
                                ? "bg-white dark:bg-slate-700 text-indigo-600 dark:text-indigo-400 shadow-sm"
                                : "text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400"
                            }`}
                        >
                            {link.label}
                        </Link>
                    ))}
                </nav>

                {/* Действия */}
                <div className="hidden md:flex items-center gap-3">
                    <button
                        onClick={toggleTheme}
                        className="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 hover:text-indigo-600 transition-all active:scale-90"
                    >
                        {theme === 'dark' ? <Sun size={20} className="text-amber-400" /> : <Moon size={20} />}
                    </button>

                    <div className="h-6 w-[1px] bg-slate-200 dark:bg-slate-800 mx-1" />

                    {isAuthenticated ? (
                        <>
                            <Link
                                href="/profile"
                                className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all"
                            >
                                <User size={18} className="text-slate-400" />
                                Профиль
                            </Link>

                            <button
                                onClick={handleLogout}
                                className="p-2.5 rounded-xl bg-rose-50 dark:bg-rose-900/20 text-rose-500 hover:bg-rose-100 dark:hover:bg-rose-900/40 transition-all active:scale-90"
                                title="Выйти"
                            >
                                <LogOut size={20} />
                            </button>
                        </>
                    ) : (
                        <>
                            <Link
                                href="/login"
                                onClick={handleLogin}
                                className="px-4 py-2.5 rounded-xl text-sm font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all"
                            >
                                Войти
                            </Link>
                            <Link
                                href="/register"
                                onClick={handleRegister}
                                className="px-4 py-2.5 rounded-xl text-sm font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all"
                            >
                                Зарегистрироваться
                            </Link>
                        </>
                    )}
                </div>

                {/* Мобильное меню */}
                <div className="flex md:hidden items-center gap-2">
                     <button
                        onClick={toggleTheme}
                        className="p-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-600 transition-all"
                    >
                        {theme === 'dark' ? <Sun size={18} className="text-amber-400" /> : <Moon size={18} />}
                    </button>
                    <button
                        className="p-2 bg-indigo-600 text-white rounded-xl shadow-lg shadow-indigo-200"
                        onClick={() => setIsMenuOpen(!isMenuOpen)}
                    >
                        {isMenuOpen ? <X size={22} /> : <Menu size={22} />}
                    </button>
                </div>

                {/* Выпадающее мобильное меню */}
                <div className={`
                    fixed inset-0 bg-white/95 dark:bg-slate-950/95 backdrop-blur-2xl z-[90] transform transition-all duration-500 flex flex-col pt-24 px-6
                    ${isMenuOpen ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-full pointer-events-none"}
                `}>
                    <div className="flex flex-col gap-2">
                        {displayedNavLinks.map((link) => ( // Use filtered links for mobile too
                            <Link
                                key={link.href}
                                href={link.href}
                                className={`text-2xl font-black py-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between ${
                                    isActive(link.href) ? "text-indigo-600" : "text-slate-400"
                                }`}
                            >
                                {link.label}
                                {isActive(link.href) && <Sparkles size={20} />}
                            </Link>
                        ))}
                    </div>

                    <div className="mt-auto mb-10 grid grid-cols-2 gap-4">
                        {isAuthenticated ? (
                            <>
                                <Link
                                    href="/profile"
                                    className="flex items-center justify-center gap-2 py-4 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 rounded-2xl font-bold"
                                >
                                    <User size={20} />
                                    Профиль
                                </Link>
                                <button
                                    onClick={handleLogout}
                                    className="flex items-center justify-center gap-2 py-4 bg-rose-50 text-rose-600 rounded-2xl font-bold"
                                >
                                    <LogOut size={20} />
                                    Выйти
                                </button>
                            </>
                        ) : (
                            <>
                                <Link
                                    href="/login"
                                    onClick={handleLogin}
                                    className="flex items-center justify-center gap-2 py-4 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 rounded-2xl font-bold"
                                >
                                    <User size={20} /> {/* Re-using User icon for Login button for now */}
                                    Войти
                                </Link>
                                <Link
                                    href="/register"
                                    onClick={handleRegister}
                                    className="flex items-center justify-center gap-2 py-4 bg-indigo-600 text-white rounded-2xl font-bold"
                                >
                                    <Sparkles size={20} /> {/* Re-using Sparkles icon for Register button for now */}
                                    Зарегистрироваться
                                </Link>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
}
