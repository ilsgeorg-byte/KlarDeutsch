"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Loader2, Trash2, Calendar, Clock, Sparkles, BookOpen } from "lucide-react";
import styles from "../../styles/Shared.module.css";

interface DiaryEntry {
  id: number;
  user_id: number;
  original_text: string;
  corrected_text: string;
  explanation: string;
  created_at: string;
}

export default function DiaryDetailPage() {
  const params = useParams();
  const id = params?.id as string;
  const router = useRouter();
  const [entry, setEntry] = useState<DiaryEntry | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchEntry = async () => {
      try {
        const token = localStorage.getItem("token");
        const headers: Record<string, string> = {};
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const res = await fetch(`/api/diary/history/${id}`, { headers });
        const data = await res.json();

        if (!res.ok) throw new Error(data.error || "Ошибка загрузки записи");
        setEntry(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (id) fetchEntry();
  }, [id]);

  const handleDelete = async () => {
    if (!confirm("Удалить эту запись?")) return;

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`/api/diary/history/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        router.back();
      } else {
        alert("Ошибка при удалении");
      }
    } catch (err) {
      console.error("Delete error:", err);
      alert("Ошибка при удалении");
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className={`${styles.pageWrapper} bg-slate-50 dark:bg-gray-900 min-h-screen`}>
        <div className="flex-1 flex flex-col items-center justify-center p-8">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-4" />
          <p className="text-slate-500 dark:text-gray-400 font-medium">Загружаем запись...</p>
        </div>
      </div>
    );
  }

  if (error || !entry) {
    return (
      <div className={`${styles.pageWrapper} bg-slate-50 dark:bg-gray-900 min-h-screen`}>
        <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
          <div className="w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center text-red-500 mb-4">
            <span className="text-2xl">😕</span>
          </div>
          <h2 className="text-xl font-bold text-slate-800 dark:text-white mb-2">Ой, что-то пошло не так</h2>
          <p className="text-slate-500 dark:text-gray-400 mb-6">{error || "Запись не найдена"}</p>
          <button
            onClick={() => router.back()}
            className="px-6 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors"
          >
            Вернуться назад
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`${styles.pageWrapper} bg-slate-50 dark:bg-gray-900 min-h-screen`}>
      <main className="max-w-4xl mx-auto px-6 py-12 w-full">
        {/* Кнопки Назад и Удалить */}
        <div className="flex justify-between items-center w-full mb-8">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 text-slate-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 font-medium transition-colors"
          >
            <ArrowLeft size={20} />
            Назад
          </button>

          <button
            onClick={handleDelete}
            className="flex items-center gap-2 px-4 py-2 rounded-xl font-semibold transition-all shadow-sm border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/30"
          >
            <Trash2 size={18} />
            Удалить
          </button>
        </div>

        {/* Заголовок с датой */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-800 dark:text-white mb-4">Запись в дневнике</h1>
          <div className="flex items-center gap-4 text-slate-500 dark:text-gray-400">
            <div className="flex items-center gap-2">
              <Calendar size={18} />
              <span>{formatDate(entry.created_at)}</span>
            </div>
          </div>
        </div>

        {/* Основной текст */}
        <div className="bg-white dark:bg-gray-800 rounded-3xl shadow-xl border border-slate-100 dark:border-gray-700 p-8 mb-6">
          <h2 className="text-lg font-bold text-slate-700 dark:text-gray-200 mb-4 flex items-center gap-2">
            <BookOpen size={20} className="text-blue-500" />
            Ваш текст:
          </h2>
          <p className="text-slate-800 dark:text-white text-lg leading-relaxed whitespace-pre-wrap">
            {entry.original_text}
          </p>
        </div>

        {/* Исправленный текст */}
        <div className="bg-green-50 dark:bg-green-900/20 rounded-3xl border-2 border-green-200 dark:border-green-800 p-8 mb-6">
          <h2 className="text-lg font-bold text-green-800 dark:text-green-300 mb-4 flex items-center gap-2">
            <Sparkles size={20} className="text-green-500" />
            Исправленный текст:
          </h2>
          <p className="text-green-900 dark:text-green-100 text-lg leading-relaxed font-medium whitespace-pre-wrap">
            {entry.corrected_text}
          </p>
        </div>

        {/* Объяснение */}
        {entry.explanation && (
          <div className="bg-slate-50 dark:bg-gray-700 rounded-3xl border border-slate-200 dark:border-gray-600 p-8">
            <h2 className="text-lg font-bold text-slate-700 dark:text-gray-200 mb-4">
              Объяснение:
            </h2>
            <p className="text-slate-600 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
              {entry.explanation}
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
