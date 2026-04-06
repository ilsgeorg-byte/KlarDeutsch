"use client";

import React, { useState, useEffect } from "react";
import styles from "./Diary.module.css";
import { Sparkles, CheckCircle2, AlertCircle, Loader2, Trash2, Calendar, Clock } from "lucide-react";
import { useRouter } from "next/navigation";
import { 
  useDiaryHistory, 
  useCorrectText, 
  useDeleteDiaryEntry,
  useExtractWords,
  useAddDiaryWords
} from "../lib/hooks";

export default function DiaryPage() {
  const [text, setText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<{ corrected: string; explanation: string } | null>(null);
  const [extractedWords, setExtractedWords] = useState<any[]>([]);
  const [isAddingWords, setIsAddingWords] = useState(false);
  const router = useRouter();

  // Используем хуки вместо ручных fetch
  const { entries: history, isLoading: historyLoading, mutate: mutateHistory } = useDiaryHistory();
  const { correctText } = useCorrectText();
  const { deleteEntry } = useDeleteDiaryEntry();
  const { extractWords } = useExtractWords();
  const { addWords } = useAddDiaryWords();

  // Проверка авторизации
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
    }
  }, [router]);

  const handleCheck = async () => {
    if (!text.trim()) return;

    setIsLoading(true);
    try {
      const correction = await correctText(text);
      
      if (!correction) {
        console.error("Correction returned undefined");
        return;
      }

      setResult({
        corrected: correction.corrected,
        explanation: correction.explanation,
      });

      // Извлекаем слова для изучения
      const words = await extractWords(text, correction.corrected);
      setExtractedWords(words || []);

      // Обновляем историю
      mutateHistory();
    } catch (err: any) {
      console.error("Ошибка проверки:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Удалить эту запись из истории?")) return;

    try {
      await deleteEntry(id);
    } catch (err) {
      console.error("Ошибка удаления:", err);
    }
  };

  const handleAddWordsToTrainer = async () => {
    if (extractedWords.length === 0) return;
    setIsAddingWords(true);
    try {
      await addWords(extractedWords);
      alert(`Добавлено ${extractedWords.length} слов в тренажер!`);
      setExtractedWords([]);
    } catch (err) {
      console.error("Ошибка при добавлении слов:", err);
    } finally {
      setIsAddingWords(false);
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
    <div className={`${styles.pageWrapper} bg-slate-50 dark:bg-gray-900 min-h-screen`}>

      <main className={styles.container}>
        <h1 className={`${styles.title} text-slate-800 dark:text-white`}>Мои записи</h1>
        <p className={`${styles.subtitle} text-slate-600 dark:text-gray-400`}>Пишите на немецком, и ИИ поможет исправить ошибки</p>

        <section className={styles.mainContent}>
          <div className={`${styles.card} dark:bg-gray-800 dark:border-gray-700`}>
            <textarea
              className={`${styles.textArea} dark:bg-gray-700 dark:border-gray-600 dark:text-white`}
              placeholder="Напишите что-нибудь на немецком... (например: Ich habe ein Hund)"
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={isLoading}
            />

            <button
              className={`${styles.checkBtn} dark:bg-blue-600 dark:hover:bg-blue-700`}
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

            {result && (
              <div className={`${styles.resultSection} dark:bg-gray-700 dark:border-gray-600`}>
                <h3 className={`${styles.resultTitle} text-slate-800 dark:text-white`}>
                  <CheckCircle2 className="text-green-500" size={24} />
                  Результат проверки:
                </h3>

                <div className={`${styles.correctedText} text-slate-800 dark:text-white`}>
                  {result.corrected}
                </div>

                <div className={`${styles.explanation} text-slate-600 dark:text-gray-300`}>
                  <h4 className="text-slate-800 dark:text-white">Что мы исправили:</h4>
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
          <h3 className={`${styles.resultTitle} text-slate-800 dark:text-white`}>История записей</h3>
          {historyLoading ? (
            <div className="flex justify-center items-center py-12">
              <Loader2 className="animate-spin text-blue-600" size={32} />
            </div>
          ) : history.length === 0 ? (
            <p className="text-slate-500 dark:text-gray-400" style={{ textAlign: 'center', marginTop: '40px' }}>У вас пока нет записей</p>
          ) : (
            <div className={`${styles.historyList} dark:bg-gray-800 dark:border-gray-700`}>
              {Object.entries(groupedHistory).map(([dateLabel, items]) => (
                <div key={dateLabel} className={styles.dateGroup}>
                  <div className={`${styles.dateHeader} text-slate-700 dark:text-gray-300`}>
                    <Calendar size={14} />
                    {dateLabel}
                  </div>
                  {items.map((item) => {
                    // Обрезаем текст до 2 строк
                    const previewText = item.original_text.length > 100 
                      ? item.original_text.substring(0, 100) + '...' 
                      : item.original_text;
                    
                    return (
                      <div 
                        key={item.id} 
                        className={`${styles.historyItem} dark:bg-gray-700 dark:border-gray-600 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors`}
                        onClick={() => window.location.href = `/diary/${item.id}`}
                      >
                        <button
                          className={styles.deleteBtn}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(item.id);
                          }}
                          title="Удалить запись"
                        >
                          <Trash2 size={16} />
                        </button>
                        <div className={styles.historyHeader}>
                          <Clock size={14} className="text-slate-400" />
                          <span className={`${styles.historyDate} text-slate-600 dark:text-gray-400`}>{item.created_at.split(' ')[1]}</span>
                        </div>
                        <div className={styles.historyContent}>
                          <p className="text-slate-700 dark:text-gray-200 text-sm leading-relaxed">
                            {previewText}
                          </p>
                          <p className="text-blue-600 dark:text-blue-400 text-xs mt-2 font-medium">
                            → Подробнее
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          )}
        </aside>
      </main>
    </div>
  );
}
