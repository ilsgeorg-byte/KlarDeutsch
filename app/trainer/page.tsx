"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Mic, Square, Volume2, Eye, Loader2, Star } from "lucide-react";
import styles from "../styles/Shared.module.css";
import { useTheme } from "../context/ThemeContext";

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
}

// @ts-ignore — если backend добавляет это поле
interface TrainerWord extends Word {
  next_review?: string;
}

// Функция для надежного перемешивания массива (алгоритм Фишера-Йетса)
const shuffleArray = <T,>(array: T[]): T[] => {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
};

// Форматирование времени
const formatTime = (ms: number): string => {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
};

export default function TrainerPage() {
  const [words, setWords] = useState<TrainerWord[]>([]);
  const [level, setLevel] = useState("A1");
  const [index, setIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [loading, setLoading] = useState(false);
  const [audioStatus, setAudioStatus] = useState<string | null>(null);
  const { theme } = useTheme(); // Глобальная тема
  const router = useRouter();

  // Статистика сессии
  const [sessionStats, setSessionStats] = useState({
    total: 0,      // Всего пройдено
    correct: 0,    // Правильных ответов (3, 4, 5)
    hard: 0,       // Сложных (1)
    known: 0,      // Знаю (0)
    startTime: Date.now(),
  });

  // Проверка авторизации
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) router.push("/login");
  }, [router]);

  const renderWordWithArticle = (wordObj: any) => {
    let text = wordObj.de || "";
    
    if (wordObj.article) {
        const articleLower = wordObj.article.toLowerCase().trim();
        let colorClass = "";
        
        if (articleLower === "der") colorClass = "text-blue-500 font-bold";
        else if (articleLower === "die") colorClass = "text-red-500 font-bold";
        else if (articleLower === "das") colorClass = "text-green-500 font-bold";

        if (colorClass) {
            if (text.toLowerCase().startsWith(articleLower + " ")) {
                text = text.slice(articleLower.length + 1).trim();
            }
            return <><span className={colorClass}>{wordObj.article}</span> {text}</>;
        }
    }

    if (text.toLowerCase().startsWith("der ")) {
        return <><span className="text-blue-500 font-bold">der</span> {text.slice(4)}</>;
    }
    if (text.toLowerCase().startsWith("die ")) {
        return <><span className="text-red-500 font-bold">die</span> {text.slice(4)}</>;
    }
    if (text.toLowerCase().startsWith("das ")) {
        return <><span className="text-green-500 font-bold">das</span> {text.slice(4)}</>;
    }

    return <span className="font-bold">{text}</span>;
  };

  // --- ЛОГИКА ЗАПИСИ ---
  const [isRecording, setIsRecording] = useState(false);
  const [ratingInProgress, setRatingInProgress] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);

  const startRecording = async () => {
    setAudioStatus(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        await uploadAudio(blob);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error(err);
      setAudioStatus("Ошибка доступа к микрофону");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const uploadAudio = async (blob: Blob) => {
    setAudioStatus("Отправка...");
    const formData = new FormData();
    formData.append("file", blob, "recording.webm");

    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/api/audio", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (res.ok) setAudioStatus("Записано! ✅");
      else setAudioStatus("Ошибка загрузки ❌");
    } catch (e) {
      setAudioStatus("Ошибка сети");
    }
  };

      const loadWords = async (isManual = false) => {
        if (!isManual) setLoading(true);
        try {
          const token = localStorage.getItem("token");
          const res = await fetch(`/api/trainer/words?level=${level}`, {
            headers: { Authorization: `Bearer ${token}` },
            cache: 'no-store'
        });
      if (res.status === 401) return router.push("/login");
      if (!res.ok) throw new Error("Failed");
      const data = await res.json();

      if (isManual) {
        setWords((prev) => [...prev, ...data]);
      } else {
        setWords(data);
        setIndex(0);
        setShowAnswer(false);
      }
    } catch (e) {
      setAudioStatus("Ошибка загрузки слов");
    } finally {
      if (!isManual) setLoading(false);
    }
  };




  useEffect(() => {
    loadWords();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [level]);

    // Гарантированное перемешивание после загрузки массива
  const hasShuffled = useRef(false);

  useEffect(() => {
    // Если массив не пустой и мы его ещё не перемешивали для текущего уровня
    if (words.length > 1 && !hasShuffled.current) {
      setWords((prev) => shuffleArray<TrainerWord>([...prev]));
      hasShuffled.current = true;
    }
  }, [words]);

  // Сбрасываем флаг перемешивания при смене уровня
  useEffect(() => {
    hasShuffled.current = false;
  }, [level]);


  const handleNext = () => {
    setShowAnswer(false);
    setAudioStatus(null);
    const newWords = [...words];
    newWords.splice(index, 1);

    if (newWords.length === 0) loadWords();
    else {
      setWords(newWords);
      if (index >= newWords.length) setIndex(0);
    }
  };

  const handleRate = async (rating: number) => {
    if (!currentWord || ratingInProgress) return;
    
    setRatingInProgress(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/api/trainer/rate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ word_id: currentWord.id, rating }),
      });
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        console.error(`API error: ${res.status}`, errorData);
        setAudioStatus(`Ошибка: ${errorData.error || 'Не удалось сохранить прогресс'}`);
        return;
      }
      
      // Обновляем статистику
      setSessionStats(prev => ({
        ...prev,
        total: prev.total + 1,
        correct: rating >= 3 ? prev.correct + 1 : prev.correct,
        hard: rating === 1 ? prev.hard + 1 : prev.hard,
        known: rating === 0 ? prev.known + 1 : prev.known,
      }));
      
      handleNext();
    } catch (err) {
      console.error("Rate error:", err);
      setAudioStatus("Ошибка сети. Проверьте подключение к серверу.");
    } finally {
      setRatingInProgress(false);
    }
  };

  const playAudio = (e: React.MouseEvent, text: string) => {
    e.stopPropagation();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "de-DE";
    window.speechSynthesis.speak(utterance);
  };

  const toggleFavorite = async (wordId: number) => {
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        alert("Пожалуйста, войдите в систему, чтобы добавлять слова в избранное");
        return;
      }

      const res = await fetch(`/api/words/${wordId}/favorite`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) return;

      // Локально переворачиваем флаг, чтобы звезда перекрасилась
      setWords(prev =>
        prev.map(w =>
          w.id === wordId ? { ...w, is_favorite: !w.is_favorite } : w
        )
      );
    } catch (err) {
      console.error("Favorite error:", err);
    }
  };

  const currentWord = words[index];

  return (
    <div
      className={`${styles.pageWrapper} bg-slate-50 dark:bg-gray-900 min-h-screen font-sans flex flex-col`}
    >
      <main className="flex-1 flex flex-col items-center px-4 w-full pt-8 pb-12">
        {/* Стильный переключатель уровней */}
        <div className="flex bg-white dark:bg-gray-800 p-1.5 rounded-2xl shadow-sm border border-slate-200 dark:border-gray-700 mb-4 w-full max-w-md overflow-x-auto no-scrollbar">
          {["A1", "A2", "B1", "B2", "C1", "PERSONAL"].map((lvl) => (
            <button
              key={lvl}
              onClick={() => {
                setWords([]);
                setIndex(0);
                setLevel(lvl);
              }}
              className={`flex-1 min-w-[60px] py-2.5 px-3 rounded-xl text-xs sm:text-sm font-black transition-all duration-300 whitespace-nowrap ${
                level === lvl
                  ? "bg-gradient-to-br from-blue-700 to-purple-700 text-white shadow-lg shadow-blue-500/40 transform scale-105"
                  : "bg-transparent text-slate-500 dark:text-gray-400 hover:bg-slate-100 dark:hover:bg-gray-700"
              }`}
            >
              {lvl === "PERSONAL" ? "Мои слова" : lvl}
            </button>
          ))}
        </div>

        {/* Статистика сессии */}
        {sessionStats.total > 0 && (
          <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl shadow-sm border border-slate-200 dark:border-gray-700 mb-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-gray-700 dark:text-gray-200">📊 Сессия</h3>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                ⏱️ {formatTime(Date.now() - sessionStats.startTime)}
              </span>
            </div>
            <div className="grid grid-cols-4 gap-2">
              <div className="text-center">
                <div className="text-lg font-bold text-gray-900 dark:text-white">{sessionStats.total}</div>
                <div className="text-[10px] text-gray-500 dark:text-gray-400 uppercase">Всего</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-green-600 dark:text-green-400">
                  {sessionStats.total > 0 ? Math.round((sessionStats.correct / sessionStats.total) * 100) : 0}%
                </div>
                <div className="text-[10px] text-gray-500 dark:text-gray-400 uppercase">Успех</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-orange-500 dark:text-orange-400">{sessionStats.hard}</div>
                <div className="text-[10px] text-gray-500 dark:text-gray-400 uppercase">Сложно</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-blue-600 dark:text-blue-400">{sessionStats.known}</div>
                <div className="text-[10px] text-gray-500 dark:text-gray-400 uppercase">Знаю</div>
              </div>
            </div>
          </div>
        )}

        {/* Контейнер карточки */}
        <div className="w-full max-w-md relative perspective-1000">
          {loading ? (
            <div className="w-full h-[400px] bg-white dark:bg-gray-800 rounded-3xl shadow-xl flex flex-col items-center justify-center border border-slate-100 dark:border-gray-700">
              <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-4" />
              <p className="text-slate-500 dark:text-gray-400 font-medium animate-pulse">
                Загружаем слова...
              </p>
            </div>
          ) : !currentWord ? (
            <div className="w-full h-[400px] bg-white dark:bg-gray-800 rounded-3xl shadow-xl flex flex-col items-center justify-center p-8 text-center border border-slate-100 dark:border-gray-700">
              <div className="w-20 h-20 bg-slate-100 dark:bg-gray-700 rounded-full flex items-center justify-center mb-6">
                <span className="text-4xl">🎉</span>
              </div>
              <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-2">
                На сегодня всё!
              </h3>
              <p className="text-slate-500 dark:text-gray-400">
                Нет слов для повторения на уровне{" "}
                <span className="font-bold text-blue-600 dark:text-blue-400">{level}</span>.
                <br />
                Отдохните или выберите другой уровень.
              </p>
            </div>
          ) : (
            <>
              {/* Сама Карточка */}
              <div
                onClick={() => !showAnswer && !ratingInProgress && setShowAnswer(true)}
                className={`relative w-full rounded-3xl shadow-xl border border-slate-100 dark:border-gray-700 bg-white dark:bg-gray-800 transition-all duration-500 transform-gpu flex flex-col overflow-hidden ${
                  !showAnswer
                    ? "hover:-translate-y-1 hover:shadow-2xl cursor-pointer"
                    : "shadow-blue-900/10 cursor-default"
                } min-h-[380px]`}
              >
                {/* Бейджи + избранное в шапке карточки */}
                <div className="flex justify-between items-center w-full p-5 absolute top-0 left-0">
                  <span className="bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-3 py-1 rounded-full text-xs font-bold tracking-wide border border-blue-100 dark:border-blue-800">
                    {currentWord.level}
                  </span>

                  <div className="flex items-center gap-2">
                    {/* @ts-ignore */}
                    {currentWord.next_review && (
                      <span className="flex items-center gap-1.5 bg-amber-50 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 px-3 py-1 rounded-full text-xs font-semibold border border-amber-100 dark:border-amber-800">
                        <span className="w-1.5 h-1.5 bg-amber-500 rounded-full animate-pulse"></span>
                        Повторение
                      </span>
                    )}

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleFavorite(currentWord.id);
                      }}
                      className="p-1.5 text-yellow-400 hover:scale-110 transition-transform"
                    >
                      <Star
                        size={22}
                        className={
                          currentWord.is_favorite
                            ? "fill-yellow-400"
                            : "fill-none"
                        }
                      />
                    </button>
                  </div>
                </div>

                {/* Центр карточки (Слово + Звук + Микрофон) */}
                <div className="flex-1 flex flex-col items-center justify-center p-6 mt-12 mb-6">
                  {/* ИСПРАВЛЕННОЕ НЕМЕЦКОЕ СЛОВО (ВЫЗОВ ФУНКЦИИ) */}
                  <h2 className="text-[2.5rem] font-extrabold text-slate-800 dark:text-white text-center leading-tight mb-6">
                    {renderWordWithArticle(currentWord)}
                  </h2>

                  {/* Кнопки аудио (Озвучка + Запись) */}
                  <div className="flex items-center gap-6">
                    {/* Диктор */}
                    <div className="flex flex-col items-center gap-2">
                      <button
                        onClick={(e) => playAudio(e, currentWord.de)}
                        className="w-14 h-14 bg-slate-50 dark:bg-gray-700 hover:bg-blue-50 dark:hover:bg-gray-600 text-slate-400 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 rounded-full flex items-center justify-center transition-colors shadow-sm border border-slate-100 dark:border-gray-600"
                      >
                        <Volume2 size={26} strokeWidth={2.5} />
                      </button>
                      <span className="text-[10px] uppercase font-bold text-slate-400 dark:text-gray-400 tracking-wider">
                        Послушать
                      </span>
                    </div>

                    {/* Разделитель */}
                    <div className="h-8 w-px bg-slate-200 dark:bg-gray-600"></div>

                    {/* Микрофон */}
                    <div className="flex flex-col items-center gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          isRecording ? stopRecording() : startRecording();
                        }}
                        className={`w-14 h-14 rounded-full flex items-center justify-center shadow-sm transition-all border ${
                          isRecording
                            ? "bg-red-500 text-white animate-pulse scale-110 border-red-500 shadow-red-500/40"
                            : "bg-slate-50 dark:bg-gray-700 text-slate-400 dark:text-gray-300 hover:text-blue-500 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-gray-600 border-slate-100 dark:border-gray-600"
                        }`}
                      >
                        {isRecording ? (
                          <Square size={24} fill="currentColor" />
                        ) : (
                          <Mic size={24} strokeWidth={2.5} />
                        )}
                      </button>
                      <span
                        className={`text-[10px] uppercase font-bold tracking-wider ${
                          isRecording ? "text-red-500" : "text-slate-400 dark:text-gray-400"
                        }`}
                      >
                        {isRecording ? "Идёт запись..." : "Проверить"}
                      </span>
                    </div>
                  </div>

                  {/* Статус записи (если есть) */}
                  {audioStatus && (
                    <div className="mt-4 px-4 py-1.5 bg-slate-50 dark:bg-gray-700 rounded-lg border border-slate-100 dark:border-gray-600 text-xs font-medium text-slate-600 dark:text-gray-300">
                      {audioStatus}
                    </div>
                  )}
                </div>

                {/* Низ карточки (Подсказка или Перевод) */}
                <div className="w-full mt-auto">
                  {!showAnswer ? (
                    <div className="w-full py-5 bg-slate-50 dark:bg-gray-700 border-t border-slate-100 dark:border-gray-600 text-center text-slate-400 dark:text-gray-400 font-medium flex items-center justify-center gap-2 transition-colors hover:bg-blue-50 dark:hover:bg-gray-600 hover:text-blue-500 dark:hover:text-blue-400">
                      <Eye size={18} /> Нажмите, чтобы увидеть перевод
                    </div>
                  ) : (
                    <div className="w-full bg-blue-50 dark:bg-blue-900/20 p-6 border-t border-blue-100 dark:border-blue-800 animate-fade-in-up flex flex-col items-center justify-center min-h-[120px]">
                      <p className="text-2xl text-blue-800 dark:text-blue-300 font-bold text-center mb-3">
                        {currentWord.ru}
                      </p>
                      {currentWord.example_de && (
                        <div className="text-sm text-blue-700/80 dark:text-blue-400 text-center italic bg-white/60 dark:bg-blue-800/30 py-2 px-4 rounded-xl border border-blue-100/50 dark:border-blue-700/50">
                          "{currentWord.example_de}"
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Блок кнопок оценок (появляется только после переворота) */}
              <div
                className={`mt-5 grid grid-cols-4 gap-3 transition-all duration-300 ${
                  showAnswer
                    ? "opacity-100 translate-y-0"
                    : "opacity-0 translate-y-4 pointer-events-none absolute w-full"
                }`}
              >
                <button
                  onClick={() => handleRate(1)}
                  disabled={ratingInProgress}
                  className={`flex flex-col items-center justify-center py-3.5 bg-white dark:bg-gray-800 border-2 border-red-100 dark:border-red-900 rounded-2xl transition-all shadow-sm group ${
                    ratingInProgress
                      ? 'opacity-50 cursor-not-allowed'
                      : 'hover:bg-red-50 dark:hover:bg-red-900/20 hover:border-red-300 dark:hover:border-red-700 hover:shadow-md'
                  }`}
                >
                  {ratingInProgress ? (
                    <Loader2 size={20} className="animate-spin text-red-500 mb-1" />
                  ) : (
                    <span className="text-red-500 dark:text-red-400 font-bold mb-1 group-hover:scale-110 transition-transform">
                      Сложно
                    </span>
                  )}
                  <span className="text-[10px] text-slate-400 dark:text-gray-500 font-medium uppercase tracking-wide">
                    Завтра
                  </span>
                </button>
                <button
                  onClick={() => handleRate(3)}
                  disabled={ratingInProgress}
                  className={`flex flex-col items-center justify-center py-3.5 bg-white dark:bg-gray-800 border-2 border-amber-100 dark:border-amber-900 rounded-2xl transition-all shadow-sm group ${
                    ratingInProgress
                      ? 'opacity-50 cursor-not-allowed'
                      : 'hover:bg-amber-50 dark:hover:bg-amber-900/20 hover:border-amber-300 dark:hover:border-amber-700 hover:shadow-md'
                  }`}
                >
                  {ratingInProgress ? (
                    <Loader2 size={20} className="animate-spin text-amber-500 mb-1" />
                  ) : (
                    <span className="text-amber-500 dark:text-amber-400 font-bold mb-1 group-hover:scale-110 transition-transform">
                      Норма
                    </span>
                  )}
                  <span className="text-[10px] text-slate-400 dark:text-gray-500 font-medium uppercase tracking-wide">
                    3-4 Дня
                  </span>
                </button>
                <button
                  onClick={() => handleRate(5)}
                  disabled={ratingInProgress}
                  className={`flex flex-col items-center justify-center py-3.5 bg-white dark:bg-gray-800 border-2 border-emerald-100 dark:border-emerald-900 rounded-2xl transition-all shadow-sm group ${
                    ratingInProgress
                      ? 'opacity-50 cursor-not-allowed'
                      : 'hover:bg-emerald-50 dark:hover:bg-emerald-900/20 hover:border-emerald-300 dark:hover:border-emerald-700 hover:shadow-md'
                  }`}
                >
                  {ratingInProgress ? (
                    <Loader2 size={20} className="animate-spin text-emerald-500 mb-1" />
                  ) : (
                    <span className="text-emerald-500 dark:text-emerald-400 font-bold mb-1 group-hover:scale-110 transition-transform">
                      Легко
                    </span>
                  )}
                  <span className="text-[10px] text-slate-400 dark:text-gray-500 font-medium uppercase tracking-wide">
                    Неделя+
                  </span>
                </button>
                <button
                  onClick={() => handleRate(0)}
                  disabled={ratingInProgress}
                  className={`flex flex-col items-center justify-center py-3.5 bg-slate-800 dark:bg-gray-700 border-2 border-slate-800 dark:border-gray-600 rounded-2xl transition-all shadow-sm group ${
                    ratingInProgress
                      ? 'opacity-50 cursor-not-allowed'
                      : 'hover:bg-slate-900 dark:hover:bg-gray-600 hover:shadow-lg'
                  }`}
                >
                  {ratingInProgress ? (
                    <Loader2 size={20} className="animate-spin text-white mb-1" />
                  ) : (
                    <span className="text-white dark:text-gray-200 font-bold mb-1 group-hover:scale-110 transition-transform">
                      Знаю
                    </span>
                  )}
                  <span className="text-[10px] text-slate-300 dark:text-gray-400 font-medium uppercase tracking-wide">
                    Убрать
                  </span>
                </button>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
