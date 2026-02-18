"use client";

import React from "react";
import { usePathname } from "next/navigation";
import styles from "../styles/Shared.module.css";

export default function Header() {
    const pathname = usePathname();

    const navLinks = [
        { name: "Главная", href: "/" },
        { name: "Тренажер", href: "/trainer" },
        { name: "Записи", href: "/audio" },
        { name: "Дневник", href: "/diary" },
        { name: "Профиль", href: "/profile" },
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
            </nav>
        </header>
    );
}
