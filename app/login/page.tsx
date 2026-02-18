"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import styles from "../styles/Auth.module.css";
import Header from "../components/Header";
import { AlertCircle, Loader2 } from "lucide-react";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const router = useRouter();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setIsLoading(true);

        try {
            const response = await fetch("/api/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
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
                localStorage.setItem("token", data.token);
                localStorage.setItem("user", JSON.stringify(data.user));
                router.push("/profile");
            } else {
                setError(data.error || "Ошибка входа");
            }
        } catch (err: any) {
            setError("Не удалось подключиться к серверу. Убедитесь, что бэкенд запущен (api/app.py)");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div style={{ backgroundColor: '#f8fafc', minHeight: '100vh' }}>
            <Header />
            <div className={styles.container}>
                <h1 className={styles.title}>С возвращением!</h1>
                <p className={styles.subtitle}>Войдите в свой аккаунт KlarDeutsch</p>

                {error && (
                    <div className={styles.error} style={{ marginBottom: '20px' }}>
                        <AlertCircle size={20} />
                        <span>{error}</span>
                    </div>
                )}

                <form className={styles.form} onSubmit={handleLogin}>
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
                                Входим...
                            </div>
                        ) : (
                            "Войти"
                        )}
                    </button>
                </form>

                <div className={styles.footer}>
                    Нет аккаунта?{" "}
                    <Link href="/register" className={styles.link}>
                        Зарегистрироваться
                    </Link>
                </div>
            </div>
        </div>
    );
}
