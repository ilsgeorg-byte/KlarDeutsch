"use client";

import React, { useState, useEffect } from "react";
import styles from "./Diary.module.css";
import { Sparkles, CheckCircle2, AlertCircle, Loader2, Trash2, Calendar } from "lucide-react";

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

  useEffect(() => {
    loadHistory();
  }, []);

  const handleDelete = async (id: number) => {
    if (!confirm("Удалить эту запись из истории?")) return;

    try {
      const res = await fetch(`/api/diary/history/${id}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setHistory(prev => prev.filter(item => item.id !== id));
      } else {
        alert("Ошибка при удалении");
      }
    } catch (err) {
      console.error("Ошибка удаления:", err);
      alert("Ошибка сети");
    }
  };

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

  // Группировка истории по датам
  const groupHistoryByDate = (historyItems: any[]) => {
    const groups: { [key: string]: any[] } = {};
    const today = new Date().toLocaleDateString();
    const yesterday = new Date(Date.now() - 86400000).toLocaleDateString();

    historyItems.forEach(item => {
      if (!item.created_at) return;

      const dateStr = item.created_at.split(' ')[0]; // ГГГГ-ММ-ДД
      const date = new Date(dateStr);
      let label = date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' });

      const itemLocaleDate = date.toLocaleDateString();
      if (itemLocaleDate === today) label = "Сегодня";
      else if (itemLocaleDate === yesterday) label = "Вчера";

      if (!groups[label]) groups[label] = [];
      groups[label].push(item);
    });

    return groups;
  };

  const groupedHistory = groupHistoryByDate(history);

  return (
    <div className={styles.pageWrapper}>
      <Header />

      <main className={styles.container}>
        <h1 className={styles.title}>Мой дневник</h1>
        <p className={styles.subtitle}>Пишите на немецком, и ИИ поможет исправить ошибки</p>

        <section className={styles.mainContent}>
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
        </section>

        <aside className={styles.historySection}>
          <h3 className={styles.resultTitle}>История записей</h3>
          {history.length === 0 ? (
            <p style={{ color: '#94a3b8', textAlign: 'center', marginTop: '40px' }}>У вас пока нет записей</p>
          ) : (
            <div className={styles.historyList}>
              {Object.entries(groupedHistory).map(([dateLabel, items]) => (
                <div key={dateLabel} className={styles.dateGroup}>
                  <div className={styles.dateHeader}>
                    <Calendar size={14} />
                    {dateLabel}
                  </div>
                  {items.map((item) => (
                    <div key={item.id} className={styles.historyItem}>
                      <button
                        className={styles.deleteBtn}
                        onClick={() => handleDelete(item.id)}
                        title="Удалить запись"
                      >
                        <Trash2 size={16} />
                      </button>
                      <div className={styles.historyHeader}>
                        <span className={styles.historyDate}>{item.created_at.split(' ')[1]}</span>
                      </div>
                      <div className={styles.historyContent}>
                        <div className={styles.historyOriginal}>
                          <strong>Текст:</strong> {item.original_text}
                        </div>
                        <div className={styles.historyCorrected}>
                          {item.corrected_text}
                        </div>
                        {item.explanation && (
                          <div style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '8px', paddingLeft: '12px', borderLeft: '2px solid #e2e8f0' }}>
                            {item.explanation}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}
        </aside>
      </main>
    </div>
  );
}
