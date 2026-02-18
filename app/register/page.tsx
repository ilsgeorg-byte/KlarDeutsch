"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import styles from "../styles/Auth.module.css";
import Header from "../components/Header";
import { AlertCircle, Loader2 } from "lucide-react";

export default function RegisterPage() {
    const [username, setUsername] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const router = useRouter();

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setIsLoading(true);

        try {
            const response = await fetch("/api/auth/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, email, password }),
            });

            const data = await response.json();

            if (response.ok) {
                // После регистрации отправляем на логин
                router.push("/login?registered=true");
            } else {
                setError(data.error || "Ошибка регистрации");
            }
        } catch (err) {
            setError("Не удалось подключиться к серверу");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div style={{ backgroundColor: '#f8fafc', minHeight: '100vh' }}>
            <Header />
            <div className={styles.container}>
                <h1 className={styles.title}>Создать аккаунт</h1>
                <p className={styles.subtitle}>Начните свое путешествие в немецкий язык</p>

                {error && (
                    <div className={styles.error} style={{ marginBottom: '20px' }}>
                        <AlertCircle size={20} />
                        <span>{error}</span>
                    </div>
                )}

                <form className={styles.form} onSubmit={handleRegister}>
                    <div className={styles.inputGroup}>
                        <label className={styles.label}>Имя пользователя</label>
                        <input
                            type="text"
                            className={styles.input}
                            placeholder="vladimir_deutsch"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                        />
                    </div>

                    <div className={styles.inputGroup}>
                        <label className={styles.label}>Email</label>
                        <input
                            type="email"
                            className={styles.input}
                            placeholder="your@email.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                        />
                    </div>

                    <div className={styles.inputGroup}>
                        <label className={styles.label}>Пароль</label>
                        <input
                            type="password"
                            className={styles.input}
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>

                    <button type="submit" className={styles.button} disabled={isLoading}>
                        {isLoading ? (
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                                <Loader2 className="animate-spin" size={20} />
                                Регистрируем...
                            </div>
                        ) : (
                            "Создать аккаунт"
                        )}
                    </button>
                </form>

                <div className={styles.footer}>
                    Уже есть аккаунт?{" "}
                    <Link href="/login" className={styles.link}>
                        Войти
                    </Link>
                </div>
            </div>
        </div>
    );
}
