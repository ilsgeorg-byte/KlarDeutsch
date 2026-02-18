"use client";

import React from "react";
import { usePathname, useRouter } from "next/navigation";
import styles from "../styles/Shared.module.css";
import { LogOut, User as UserIcon } from "lucide-react";

export default function Header() {
    const pathname = usePathname();
    const router = useRouter();
    const [isLoggedIn, setIsLoggedIn] = React.useState(false);

    React.useEffect(() => {
        const token = localStorage.getItem("token");
        setIsLoggedIn(!!token);
    }, [pathname]);

    const handleLogout = () => {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        setIsLoggedIn(false);
        router.push("/login");
    };

    const navLinks = [
        { name: "Главная", href: "/" },
        { name: "Тренажер", href: "/trainer" },
        { name: "Записи", href: "/audio" },
        { name: "Дневник", href: "/diary" },
    ];

    return (
        <header className={styles.header}>
            <a href="/" className={styles.logo}>
                <span>🇩🇪</span> KlarDeutsch
            </a>
            <nav className={styles.nav}>
                {navLinks.map((link) => (
                    <a
                        key={link.href}
                        href={link.href}
                        className={`${styles.navLink} ${pathname === link.href ? styles.navLinkActive : ""
                            }`}
                    >
                        {link.name}
                    </a>
                ))}

                {isLoggedIn ? (
                    <div style={{ display: 'flex', gap: '15px', alignItems: 'center', marginLeft: '10px' }}>
                        <a
                            href="/profile"
                            className={`${styles.navLink} ${pathname === '/profile' ? styles.navLinkActive : ""}`}
                            title="Профиль"
                        >
                            <UserIcon size={18} />
                        </a>
                        <button
                            onClick={handleLogout}
                            className={styles.navLink}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', color: '#ef4444' }}
                        >
                            <LogOut size={18} />
                            Выйти
                        </button>
                    </div>
                ) : (
                    <a
                        href="/login"
                        className={`${styles.navLink} ${pathname === '/login' ? styles.navLinkActive : ""}`}
                        style={{ fontWeight: 'bold', color: '#3b82f6' }}
                    >
                        Войти
                    </a>
                )}
            </nav>
        </header>
    );
}
