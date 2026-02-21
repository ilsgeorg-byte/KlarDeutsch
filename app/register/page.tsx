"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import styles from "../styles/Auth.module.css";

import { AlertCircle, Loader2 } from "lucide-react";

export default function RegisterPage() {
    const [username, setUsername] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const router = useRouter();

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setIsLoading(true);

        if (password !== confirmPassword) {
            setError("Пароли не совпадают");
            setIsLoading(false);
            return;
        }

        if (password.length < 6) {
            setError("Пароль должен быть не менее 6 символов");
            setIsLoading(false);
            return;
        }

        try {
            const response = await fetch("/api/auth/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, email, password }),
            });

            let data;
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                data = await response.json();
            } else {
                const text = await response.text();
                setError(text.includes("<!doctype html>") ? "Ошибка сервера (404/500)" : text);
                setIsLoading(false);
                return;
            }

            if (response.ok) {
                // Сохраняем токен и пользователя для автоматического входа
                localStorage.setItem("token", data.token);
                localStorage.setItem("user", JSON.stringify(data.user));
                // Отправляем в профиль
                router.push("/profile");
            } else {
                setError(data.error || "Ошибка регистрации");
            }
        } catch (err: any) {
            setError("Не удалось подключиться к серверу. Убедитесь, что бэкенд запущен (api/app.py)");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div style={{ backgroundColor: '#f8fafc', minHeight: '100vh' }}>
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

                    <div className={styles.inputGroup}>
                        <label className={styles.label}>Подтвердите пароль</label>
                        <input
                            type="password"
                            className={styles.input}
                            placeholder="••••••••"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
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
