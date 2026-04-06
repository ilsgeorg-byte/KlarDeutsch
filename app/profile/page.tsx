"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { BookOpen, CheckCircle, TrendingUp, Layers, Star, Plus, Upload, ChevronRight, X } from "lucide-react";
import UploadWordsModal from "../components/UploadWordsModal";
import { useStats, useFavorites } from "../lib/hooks";

interface Word {
  id: number;
  de: string;
  ru: string;
  article?: string;
  verb_forms?: string;
  plural?: string;
  level: string;
  topic: string;
  example_de?: string;
  example_ru?: string;
  audio_url?: string;
  is_favorite?: boolean;
  next_review?: string;
}

export default function ProfilePage() {
  const router = useRouter();
  const [selectedLevel, setSelectedLevel] = useState<string | null>(null);
  const [levelWords, setLevelWords] = useState<Word[]>([]);
  const [loadingLevel, setLoadingLevel] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  // Используем хуки вместо ручных fetch
  const { stats, isLoading: statsLoading, error: statsError } = useStats();
  const { favorites, isLoading: favLoading } = useFavorites();

  // Проверка авторизации
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
    }
  }, [router]);

  const loadLevelWords = async (level: string) => {
    setLoadingLevel(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`/api/learning/words?level=${level}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setLevelWords(Array.isArray(data) ? data : []);
        setSelectedLevel(level);
        
        // Плавный скролл к списку
        setTimeout(() => {
          document.getElementById('level-words-list')?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      }
    } finally {
      setLoadingLevel(false);
    }
  };

  const totalWordsInDb = stats ? Object.values(stats.total_words).reduce((a, b) => a + b, 0) : 0;
  const knownWords = stats?.user_progress["known"] || 0;
  const learningWords = stats?.user_progress["learning"] || 0;

  const isLoading = statsLoading || favLoading;

  if (isLoading) return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex justify-center items-center">
      <div className="w-12 h-12 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 animate-fade-in pb-20">
      <main className="max-w-6xl mx-auto px-6 py-12 w-full">
        
        {/* Адаптивная шапка */}
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
          <div className="space-y-2 text-center md:text-left">
            <h1 className="text-4xl md:text-5xl font-black text-slate-900 dark:text-white tracking-tight">
              Ваш профиль
            </h1>
            <p className="text-slate-500 dark:text-slate-400 text-lg font-medium">
              Статистика обучения в <span className="text-indigo-600 font-bold">KlarDeutsch</span>
            </p>
          </div>
          <div className="grid grid-cols-2 sm:flex sm:flex-row gap-3 w-full md:w-auto">
            <button
              onClick={() => router.push("/profile/my-words")}
              className="flex items-center justify-center gap-2 px-4 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-2xl font-black text-sm sm:text-base shadow-lg shadow-indigo-200 dark:shadow-none transition-all active:scale-95"
            >
              <Plus size={20} className="hidden sm:block" />
              Мои слова
            </button>
            <button
              onClick={() => setIsUploadModalOpen(true)}
              className="flex items-center justify-center gap-2 px-4 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-2xl font-black text-sm sm:text-base shadow-sm transition-all"
            >
              <Upload size={20} className="hidden sm:block" />
              Импорт
            </button>
          </div>
        </header>

        {/* Сетка показателей */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-12">
          {[
            { icon: Layers, label: "В базе", value: totalWordsInDb, color: "blue" },
            { icon: CheckCircle, label: "Выучено", value: knownWords, color: "emerald" },
            { icon: TrendingUp, label: "В процессе", value: learningWords, color: "orange" }
          ].map((item, i) => (
            <div key={i} className="bg-white dark:bg-slate-900 p-8 rounded-[32px] border border-slate-100 dark:border-slate-800 shadow-sm modern-shadow-hover text-center">
              <div className={`w-14 h-14 bg-${item.color}-50 dark:bg-${item.color}-900/20 text-${item.color}-600 dark:text-${item.color}-400 rounded-2xl flex items-center justify-center mx-auto mb-4`}>
                <item.icon size={28} />
              </div>
              <p className="text-xs font-black uppercase tracking-widest text-slate-400 dark:text-slate-500 mb-1">{item.label}</p>
              <p className="text-4xl font-black text-slate-900 dark:text-white">{item.value}</p>
            </div>
          ))}
        </div>

        {/* Прогресс по уровням */}
        <div className="mb-12">
          <h2 className="text-2xl font-black text-slate-900 dark:text-white mb-8 flex items-center gap-3">
            <BookOpen className="text-indigo-600" /> Прогресс по уровням
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {["A1", "A2", "B1", "B2", "C1"].map((lvl) => {
              const total = stats?.total_words[lvl] || 0;
              const known = stats?.detailed.find(d => d.level === lvl && d.status === "known")?.count || 0;
              const percent = total > 0 ? Math.round((known / total) * 100) : 0;

              return (
                <div
                  key={lvl}
                  onClick={() => loadLevelWords(lvl)}
                  className="group bg-white dark:bg-slate-900 p-7 rounded-[32px] border border-slate-100 dark:border-slate-800 cursor-pointer modern-shadow-hover"
                >
                  <div className="flex justify-between items-center mb-6">
                    <span className="px-4 py-1.5 bg-slate-900 dark:bg-slate-800 text-white text-xs font-black rounded-xl uppercase tracking-tighter">
                      Level {lvl}
                    </span>
                    <span className="text-lg font-black text-indigo-600">{percent}%</span>
                  </div>
                  <div className="w-full bg-slate-100 dark:bg-slate-800 h-3 rounded-full mb-6 overflow-hidden">
                    <div
                      className="bg-indigo-600 h-full rounded-full transition-all duration-1000"
                      style={{ width: `${percent}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-sm font-bold text-slate-500">
                    <span>{known} / {total} слов</span>
                    <ChevronRight size={18} className="group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Список слов уровня */}
        {selectedLevel && (
          <div className="mb-16 animate-fade-in scroll-mt-24" id="level-words-list">
            <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-6 mb-10 bg-white dark:bg-slate-900 p-8 rounded-[40px] border border-slate-100 dark:border-slate-800 shadow-sm">
              <div className="flex items-center gap-5">
                <div className="w-16 h-16 bg-indigo-600 rounded-3xl flex items-center justify-center text-white shadow-lg shadow-indigo-200 dark:shadow-none">
                  <span className="text-2xl font-black">{selectedLevel}</span>
                </div>
                <div>
                  <h2 className="text-3xl font-black text-slate-900 dark:text-white flex items-center gap-3">
                    Слова на повторении
                  </h2>
                  <p className="text-slate-500 font-bold flex items-center gap-2">
                    <span className="w-2 h-2 bg-indigo-500 rounded-full"></span>
                    {levelWords.length} слов в вашем плане
                  </p>
                </div>
              </div>
              <button 
                onClick={() => setSelectedLevel(null)}
                className="self-start sm:self-center p-4 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-2xl transition-all active:scale-90 group"
              >
                <X size={24} className="text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-200" />
              </button>
            </div>
            
            {loadingLevel ? (
              <div className="flex flex-col items-center justify-center py-24 bg-white dark:bg-slate-900 rounded-[40px] border border-slate-100 dark:border-slate-800">
                <div className="w-12 h-12 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mb-4"></div>
                <p className="text-slate-400 font-black uppercase tracking-widest text-xs">Загрузка слов...</p>
              </div>
            ) : levelWords.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {levelWords.map((word) => (
                  <button
                    key={word.id}
                    onClick={() => router.push(`/dictionary/${word.id}`)}
                    className="group p-8 bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-[40px] hover:border-indigo-400 dark:hover:border-indigo-600 transition-all text-left shadow-sm modern-shadow-hover relative flex flex-col min-h-[180px]"
                  >
                    <div className="flex justify-between items-start mb-4">
                      <p className="text-2xl font-black text-slate-900 dark:text-white group-hover:text-indigo-600 transition-colors">
                        {word.article && <span className="text-indigo-500 mr-2 font-black">{word.article}</span>}
                        {word.de}
                      </p>
                    </div>
                    <p className="text-slate-500 dark:text-slate-400 font-bold text-lg mb-8">{word.ru}</p>
                    
                    <div className="mt-auto flex items-center justify-between pt-5 border-t border-slate-50 dark:border-slate-800">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                        <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">
                          {word.next_review ? `Повтор: ${new Date(word.next_review).toLocaleDateString()}` : "Новое"}
                        </span>
                      </div>
                      <ChevronRight size={18} className="text-slate-300 group-hover:text-indigo-500 group-hover:translate-x-2 transition-all duration-300" />
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className="bg-white dark:bg-slate-900 p-24 rounded-[48px] border-4 border-dashed border-slate-100 dark:border-slate-800 text-center">
                <div className="w-24 h-24 bg-slate-50 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-8">
                  <BookOpen className="text-slate-200" size={40} />
                </div>
                <h3 className="text-3xl font-black text-slate-900 dark:text-white mb-4">Список пуст</h3>
                <p className="text-slate-500 max-w-sm mx-auto text-lg font-medium leading-relaxed">
                  Похоже, вы еще не добавили ни одного слова этого уровня в свой учебный план.
                </p>
                <button 
                  onClick={() => router.push("/trainer")}
                  className="mt-10 px-8 py-4 bg-indigo-600 text-white rounded-2xl font-black shadow-xl shadow-indigo-100 dark:shadow-none hover:bg-indigo-700 transition-all active:scale-95"
                >
                  Перейти в тренажер
                </button>
              </div>
            )}
          </div>
        )}

        {/* Избранное */}
        {favorites.length > 0 && (
          <div className="bg-white dark:bg-slate-900 p-8 rounded-[40px] border border-slate-100 dark:border-slate-800 shadow-sm">
            <h2 className="text-2xl font-black text-slate-900 dark:text-white mb-8 flex items-center gap-3">
              <Star className="text-amber-400" fill="currentColor" /> Избранное
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {favorites.map((word) => (
                <button
                  key={word.id}
                  onClick={() => router.push(`/dictionary/${word.id}`)}
                  className="p-5 border border-slate-50 dark:border-slate-800 rounded-3xl hover:border-indigo-200 dark:hover:border-indigo-900 hover:bg-indigo-50/30 dark:hover:bg-indigo-900/10 transition-all text-left group"
                >
                  <p className="font-black text-slate-900 dark:text-white mb-1 group-hover:text-indigo-600 transition-colors">
                    {word.article && <span className="text-indigo-500 mr-1.5">{word.article}</span>}
                    {word.de}
                  </p>
                  <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{word.ru}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        <UploadWordsModal
          isOpen={isUploadModalOpen}
          onClose={() => setIsUploadModalOpen(false)}
          onSuccess={() => window.location.reload()}
        />
      </main>
    </div>
  );
}
