"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { BookOpen, CheckCircle, TrendingUp, Award, Layers, Star } from "lucide-react";
import styles from "../styles/Shared.module.css";

interface Stats {
  total_words: { [key: string]: number };
  user_progress: { [key: string]: number };
  detailed: Array<{
    level: string;
    status: string;
    count: number;
  }>;
}

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
  examples?: { de: string; ru: string }[];
  synonyms?: string;
  antonyms?: string;
  collocations?: string;
  audio_url?: string;
  is_favorite?: boolean;
  next_review?: string;
  interval?: number;
  ease_factor?: number;
  reps?: number;
}

export default function ProfilePage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [favorites, setFavorites] = useState<Word[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedLevel, setSelectedLevel] = useState<string | null>(null);
  const [levelWords, setLevelWords] = useState<Word[]>([]);
  const [loadingLevel, setLoadingLevel] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const fetchData = async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        router.push("/login");
        return;
      }

      try {
        setError(null);
        
        // Fetch Stats
        const statsRes = await fetch("/api/trainer/stats", {
          headers: { Authorization: `Bearer ${token}` },
        });
        
        if (statsRes.status === 401) {
          localStorage.removeItem("token");
          router.push("/login");
          return;
        }
        
        if (!statsRes.ok) {
          const errorData = await statsRes.json().catch(() => ({}));
          throw new Error(errorData.error || `HTTP ${statsRes.status}`);
        }
        
        const statsData = await statsRes.json();
        console.log("Stats loaded:", statsData);
        setStats(statsData);

        // Fetch Favorites
        const favsRes = await fetch("/api/favorites", {
          headers: { Authorization: `Bearer ${token}` },
        });
        
        if (favsRes.ok) {
          const favsData = await favsRes.json();
          console.log("Favorites loaded:", favsData);
          setFavorites(Array.isArray(favsData) ? favsData : (favsData.words || []));
        } else {
          console.warn("Failed to load favorites:", favsRes.status);
          setFavorites([]);
        }
      } catch (err) {
        console.error("Failed to fetch profile data:", err);
        setError(err instanceof Error ? err.message : "Неизвестная ошибка");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [router]);

  // Загрузка слов для уровня (только те, что в изучении)
  const loadLevelWords = async (level: string) => {
    setLoadingLevel(true);
    try {
      const token = localStorage.getItem("token");
      
      // Загружаем ВСЕ слова в изучении через новый API
      const res = await fetch(`/api/learning/words?level=${level}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (res.ok) {
        const data = await res.json();
        setLevelWords(Array.isArray(data) ? data : []);
        setSelectedLevel(level);
      }
    } catch (err) {
      console.error("Failed to load level words:", err);
      setLevelWords([]);
    } finally {
      setLoadingLevel(false);
    }
  };

  const totalWordsInDb = stats ? Object.values(stats.total_words).reduce((a, b) => a + b, 0) : 0;
  const knownWords = stats?.user_progress["known"] || 0;
  const learningWords = stats?.user_progress["learning"] || 0;

  const renderWordWithArticle = (wordObj: any) => {
    let text = wordObj.de || "";

    if (wordObj.article) {
      const articleLower = wordObj.article.toLowerCase().trim();
      let colorClass = "";

      if (articleLower === "der") colorClass = "text-blue-500";
      else if (articleLower === "die") colorClass = "text-red-500";
      else if (articleLower === "das") colorClass = "text-green-500";

      if (colorClass) {
        if (text.toLowerCase().startsWith(articleLower + " ")) {
          text = text.slice(articleLower.length + 1).trim();
        }
        return (
          <>
            <span className={`${colorClass} font-extrabold`}>{wordObj.article}</span>{" "}
            <span className="text-gray-900 font-extrabold">{text}</span>
          </>
        );
      }
    }

    if (text.toLowerCase().startsWith("der ")) {
      return (
        <>
          <span className="text-blue-500 font-extrabold">der</span>{" "}
          <span className="text-gray-900 font-extrabold">{text.slice(4)}</span>
        </>
      );
    }
    if (text.toLowerCase().startsWith("die ")) {
      return (
        <>
          <span className="text-red-500 font-extrabold">die</span>{" "}
          <span className="text-gray-900 font-extrabold">{text.slice(4)}</span>
        </>
      );
    }
    if (text.toLowerCase().startsWith("das ")) {
      return (
        <>
          <span className="text-green-500 font-extrabold">das</span>{" "}
          <span className="text-gray-900 font-extrabold">{text.slice(4)}</span>
        </>
      );
    }

    return <span className="text-gray-900 font-extrabold">{text}</span>;
  };

  return (
    <div className={styles.pageWrapper}>
      <main className="max-w-5xl mx-auto px-6 py-12 w-full">
        <header className="mb-12">
          <h1 className="text-4xl font-extrabold text-gray-900 mb-2">Ваш профиль</h1>
          <p className="text-gray-500 text-lg">Статистика и избранные слова в KlarDeutsch</p>
        </header>

        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : error ? (
          <div className="bg-white p-12 rounded-3xl shadow-sm text-center">
            <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Ошибка загрузки данных</h3>
            <p className="text-gray-500 mb-6">{error}</p>
            <div className="flex gap-4 justify-center">
              <button
                onClick={() => window.location.reload()}
                className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition-colors"
              >
                Обновить страницу
              </button>
              <button
                onClick={() => {
                  localStorage.removeItem("token");
                  router.push("/login");
                }}
                className="px-6 py-3 bg-gray-100 text-gray-700 font-semibold rounded-xl hover:bg-gray-200 transition-colors"
              >
                Войти снова
              </button>
            </div>
          </div>
        ) : !stats ? (
          <div className="bg-white p-12 rounded-3xl shadow-sm text-center">
            <p className="text-gray-500">Не удалось загрузить данные. Попробуйте обновить страницу.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-12">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {/* Карточки основных показателей */}
              <div className="bg-white p-8 rounded-3xl shadow-sm border border-gray-100 flex flex-col items-center text-center">
                <div className="w-16 h-16 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mb-4">
                  <Layers size={32} />
                </div>
                <span className="text-sm font-medium text-gray-400 mb-1 uppercase tracking-wider">
                  Всего в базе
                </span>
                <span className="text-4xl font-black text-gray-900">{totalWordsInDb}</span>
                <span className="text-xs text-gray-400 mt-2">слов всех уровней</span>
              </div>

              <div className="bg-white p-8 rounded-3xl shadow-sm border border-gray-100 flex flex-col items-center text-center">
                <div className="w-16 h-16 bg-green-50 text-green-600 rounded-2xl flex items-center justify-center mb-4">
                  <CheckCircle size={32} />
                </div>
                <span className="text-sm font-medium text-gray-400 mb-1 uppercase tracking-wider">
                  Выучено
                </span>
                <span className="text-4xl font-black text-gray-900">{knownWords}</span>
                <span className="text-xs text-gray-400 mt-2">помечено как "знаю"</span>
              </div>

              <div className="bg-white p-8 rounded-3xl shadow-sm border border-gray-100 flex flex-col items-center text-center">
                <div className="w-16 h-16 bg-orange-50 text-orange-600 rounded-2xl flex items-center justify-center mb-4">
                  <TrendingUp size={32} />
                </div>
                <span className="text-sm font-medium text-gray-400 mb-1 uppercase tracking-wider">
                  В процессе
                </span>
                <span className="text-4xl font-black text-gray-900">{learningWords}</span>
                <span className="text-xs text-gray-400 mt-2">активно тренируются</span>
              </div>
            </div>

            {/* Секция избранных слов */}
            <div className="bg-white p-8 rounded-3xl shadow-sm border border-gray-100">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
                <Star className="text-yellow-500" fill="#f59e0b" /> Избранные слова ({favorites.length})
              </h2>

              {favorites.length === 0 ? (
                <p className="text-gray-500 py-4">
                  У вас пока нет избранных слов. Добавляйте их в словаре!
                </p>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {favorites.map((word) => (
                    <button
                      key={word.id}
                      onClick={() => router.push(`/dictionary/${word.id}`)}
                      className="p-4 border border-gray-100 rounded-2xl hover:border-blue-200 hover:bg-blue-50/30 transition-all text-left flex flex-col gap-1"
                    >
                      <div className="flex items-center gap-2">
                        {/* убрали отдельный word.article, оставляем только хелпер */}
                        <span className="font-bold text-gray-900">
                          {renderWordWithArticle(word)}
                        </span>
                      </div>
                      <span className="text-sm text-gray-500">{word.ru}</span>
                      <div className="mt-2 flex items-center gap-2">
                        <span className="text-[10px] bg-gray-100 px-2 py-0.5 rounded-full font-bold uppercase">
                          {word.level}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Прогресс по уровням */}
            <div className="mt-4">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
                <BookOpen className="text-blue-600" /> Прогресс по уровням
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {["A1", "A2", "B1", "B2", "C1"].map((lvl) => {
                  const total = stats.total_words[lvl] || 0;
                  const userLvlStats = stats.detailed.filter((d) => d.level === lvl);
                  const known = userLvlStats.find((d) => d.status === "known")?.count || 0;
                  const learning = userLvlStats.find((d) => d.status === "learning")?.count || 0;
                  const percent = total > 0 ? Math.round((known / total) * 100) : 0;

                  return (
                    <div
                      key={lvl}
                      onClick={() => loadLevelWords(lvl)}
                      className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100 cursor-pointer hover:shadow-lg hover:border-blue-300 transition-all"
                    >
                      <div className="flex justify-between items-center mb-4">
                        <span className="px-3 py-1 bg-gray-900 text-white text-xs font-bold rounded-lg">
                          {lvl}
                        </span>
                        <span className="text-sm font-bold text-blue-600">{percent}%</span>
                      </div>

                      <div className="w-full bg-gray-100 h-2 rounded-full mb-6 overflow-hidden">
                        <div
                          className="bg-blue-600 h-full rounded-full transition-all duration-1000"
                          style={{ width: `${percent}%` }}
                        ></div>
                      </div>

                      <div className="flex flex-col gap-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-500">Выучено</span>
                          <span className="font-semibold text-gray-900">
                            {known} / {total}
                          </span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-500">Тренируется</span>
                          <span className="font-semibold text-orange-600">{learning}</span>
                        </div>
                        <div className="text-xs text-blue-600 mt-2 text-center">
                          👆 Нажми чтобы увидеть слова
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Секция достижений (мокап) */}
            <div className="bg-gradient-to-r from-blue-600 to-indigo-700 p-10 rounded-3xl text-white shadow-xl flex flex-col md:flex-row items-center justify между gap-8">
              <div>
                <h3 className="text-3xl font-bold mb-2 flex items-center gap-2">
                  <Award size={32} className="text-yellow-400" /> KlarDeutsch Star
                </h3>
                <p className="text-blue-100 text-lg">
                  Вы на правильном пути! Сохраняйте ударный режим.
                </p>
              </div>
              <div className="text-center bg-white/10 backdrop-blur-md px-8 py-6 rounded-2xl border border-white/20">
                <span className="block text-5xl font-black mb-1">7</span>
                <span className="text-xs uppercase tracking-widest font-bold text-blue-200">
                  Дней подряд
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Модальное окно со словами уровня */}
        {selectedLevel && (
          <div 
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setSelectedLevel(null)}
          >
            <div 
              className="bg-white rounded-3xl shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Заголовок */}
              <div className="flex items-center justify-between p-6 border-b border-gray-200">
                <div className="flex items-center gap-3">
                  <BookOpen className="text-blue-600" size={28} />
                  <div>
                    <h3 className="text-2xl font-bold text-gray-900">
                      Слова уровня {selectedLevel}
                    </h3>
                    <p className="text-sm text-gray-500">
                      В изучении: {stats?.detailed.find(d => d.level === selectedLevel && d.status === 'learning')?.count || 0} • 
                      Показано: {levelWords.length}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedLevel(null)}
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Контент */}
              <div className="overflow-y-auto max-h-[60vh] p-6">
                {loadingLevel ? (
                  <div className="flex justify-center items-center h-40">
                    <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                  </div>
                ) : levelWords.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">
                    Нет слов этого уровня
                  </p>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {levelWords.map((word) => (
                      <button
                        key={word.id}
                        onClick={() => {
                          setSelectedLevel(null);
                          router.push(`/dictionary/${word.id}`);
                        }}
                        className="p-4 border border-gray-200 rounded-2xl hover:border-blue-300 hover:bg-blue-50 transition-all text-left"
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-bold text-gray-900">
                            {renderWordWithArticle(word)}
                          </span>
                        </div>
                        <span className="text-sm text-gray-600">{word.ru}</span>
                        <div className="flex items-center gap-2 mt-2 flex-wrap">
                          <span className="text-[10px] bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-bold uppercase">
                            {word.level}
                          </span>
                          {word.topic && (
                            <span className="text-[10px] bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                              {word.topic}
                            </span>
                          )}
                          {word.next_review && (
                            <span className="text-[10px] bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">
                              Повтор: {new Date(word.next_review).toLocaleDateString('ru-RU')}
                            </span>
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Подвал */}
              <div className="p-4 border-t border-gray-200 bg-gray-50 text-center text-sm text-gray-600">
                Показано {levelWords.length} слов • Нажмите на слово для просмотра
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
