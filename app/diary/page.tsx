"use client";

import React, { useState, useEffect } from "react";
import styles from "./Diary.module.css";
import { Sparkles, CheckCircle2, AlertCircle, Loader2, Trash2, Calendar } from "lucide-react";

import { useRouter } from "next/navigation";
import Header from "../components/Header";

export default function DiaryPage() {
  const [text, setText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<{ corrected: string; explanation: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [extractedWords, setExtractedWords] = useState<any[]>([]);
  const [isAddingWords, setIsAddingWords] = useState(false);
  const router = useRouter();

  // Проверка авторизации
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
    }
  }, []);

  const loadHistory = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/api/diary/history", {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.status === 401) {
        router.push("/login");
        return;
      }
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
      const token = localStorage.getItem("token");
      const res = await fetch(`/api/diary/history/${id}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
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

  const handleExtractWords = async (original: string, corrected: string) => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/api/diary/extract-words", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ original, corrected }),
      });
      if (res.ok) {
        const words = await res.json();
        setExtractedWords(words);
      }
    } catch (err) {
      console.error("Ошибка при извлечении слов:", err);
    }
  };

  const handleAddWordsToTrainer = async () => {
    if (extractedWords.length === 0) return;
    setIsAddingWords(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/api/diary/add-words", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(extractedWords),
      });
      if (res.ok) {
        alert(`Добавлено ${extractedWords.length} слов в тренажер!`);
        setExtractedWords([]);
      }
    } catch (err) {
      console.error("Ошибка при добавлении слов:", err);
    } finally {
      setIsAddingWords(false);
    }
  };

  const handleCheck = async () => {
    if (!text.trim()) return;

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const token = localStorage.getItem("token");
      const response = await fetch("/api/diary/correct", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
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

      // Извлекаем слова для изучения
      handleExtractWords(text, data.corrected);

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

                {extractedWords.length > 0 && (
                  <div className="mt-8 p-6 bg-blue-50/50 rounded-2xl border border-blue-100/50 animate-in fade-in slide-in-from-top-4 duration-500">
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
                      <div>
                        <h4 className="font-bold text-blue-900 flex items-center gap-2 text-lg">
                          <Sparkles size={20} className="text-blue-500" /> Выучите новые слова:
                        </h4>
                        <p className="text-xs text-blue-600/70 mt-1">ИИ нашел полезные выражения в вашем тексте</p>
                      </div>
                      <button
                        onClick={handleAddWordsToTrainer}
                        disabled={isAddingWords}
                        className="w-full sm:w-auto bg-blue-600 text-white px-5 py-2 rounded-xl font-bold hover:bg-blue-700 transition-all shadow-md active:scale-95 disabled:opacity-50 flex items-center justify-center gap-2"
                      >
                        {isAddingWords ? (
                          <Loader2 className="animate-spin" size={18} />
                        ) : (
                          <CheckCircle2 size={18} />
                        )}
                        {isAddingWords ? "Добавляем..." : "Добавить в тренажер"}
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {extractedWords.map((w, idx) => (
                        <div key={idx} className="bg-white px-3 py-1.5 rounded-xl text-sm shadow-sm border border-blue-100 flex items-center gap-2 hover:border-blue-300 transition-colors group">
                          {w.article && <span className="text-blue-500 font-bold opacity-70 group-hover:opacity-100">{w.article}</span>}
                          <span className="font-semibold text-gray-800">{w.de}</span>
                          <span className="text-gray-400 font-medium">— {w.ru}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
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
