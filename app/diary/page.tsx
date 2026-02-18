"use client";

import React, { useState } from "react";
import styles from "./Diary.module.css";
import { Sparkles, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";

export default function DiaryPage() {
  const [text, setText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<{ corrected: string; explanation: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCheck = async () => {
    if (!text.trim()) return;

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch("/api/diary/correct", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Ошибка при проверке текста");
      }

      setResult({
        corrected: data.corrected,
        explanation: data.explanation,
      });
    } catch (err: any) {
      setError(err.message || "Произошла ошибка. Попробуйте позже.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.pageWrapper}>
      <header className={styles.header}>
        <a href="/" className={styles.logo}>
          <span>🇩🇪</span> KlarDeutsch
        </a>
        <nav className={styles.nav}>
          <a href="/" className={styles.navLink}>Главная</a>
          <a href="/trainer" className={styles.navLink}>Тренажер</a>
          <a href="/audio" className={styles.navLink}>Записи</a>
          <a href="/diary" className={styles.navLink} style={{ color: '#3b82f6', fontWeight: 600 }}>Дневник</a>
        </nav>
      </header>

      <main className={styles.container}>
        <h1 className={styles.title}>Мой дневник</h1>
        <p className={styles.subtitle}>Пишите на немецком, и ИИ поможет исправить ошибки</p>

        <div className={styles.card}>
          <textarea
            className={styles.textArea}
            placeholder="Напишите что-нибудь на немецком... (например: Ich habe ein Hund)"
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={isLoading}
          />

          <button
            className={styles.checkBtn}
            onClick={handleCheck}
            disabled={isLoading || !text.trim()}
          >
            {isLoading ? (
              <>
                <Loader2 className="animate-spin" size={20} />
                Проверяем...
              </>
            ) : (
              <>
                <Sparkles size={20} />
                Проверить
              </>
            )}
          </button>

          {error && (
            <div style={{ marginTop: '20px', color: '#ef4444', display: 'flex', gap: '8px', alignItems: 'center' }}>
              <AlertCircle size={20} />
              <span>{error}</span>
            </div>
          )}

          {result && (
            <div className={styles.resultSection}>
              <h3 className={styles.resultTitle}>
                <CheckCircle2 color="#22c55e" size={24} />
                Результат проверки:
              </h3>
              
              <div className={styles.correctedText}>
                {result.corrected}
              </div>

              <div className={styles.explanation}>
                <h4>Что мы исправили:</h4>
                <p>{result.explanation}</p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
