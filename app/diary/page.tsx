"use client";

import React, { useState } from "react";
import styles from "./Diary.module.css";
import { Sparkles, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";

import Header from "../components/Header";

export default function DiaryPage() {
  const [text, setText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<{ corrected: string; explanation: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<any[]>([]);

  const loadHistory = async () => {
    try {
      const res = await fetch("/api/diary/history");
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (err) {
      console.error("Ошибка загрузки истории:", err);
    }
  };

  React.useEffect(() => {
    loadHistory();
  }, []);

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

      // Обновляем историю после успешной проверки
      loadHistory();
    } catch (err: any) {
      setError(err.message || "Произошла ошибка. Попробуйте позже.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.pageWrapper}>
      <Header />

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

        {history.length > 0 && (
          <div className={styles.historySection}>
            <h3 className={styles.resultTitle}>История записей</h3>
            <div className={styles.historyList}>
              {history.map((item) => (
                <div key={item.id} className={styles.historyItem}>
                  <div className={styles.historyHeader}>
                    <span className={styles.historyDate}>{item.created_at}</span>
                  </div>
                  <div className={styles.historyContent}>
                    <div className={styles.historyOriginal}>
                      <strong>Я написал:</strong> {item.original_text}
                    </div>
                    <div className={styles.historyCorrected}>
                      <strong>ИИ исправил:</strong> {item.corrected_text}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
