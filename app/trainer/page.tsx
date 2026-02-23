"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Mic, Square, Volume2, Eye, Loader2, Star } from "lucide-react";
import styles from "../styles/Shared.module.css";

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

export default function TrainerPage() {
  const [words, setWords] = useState<TrainerWord[]>([]);
  const [level, setLevel] = useState("A1");
  const [index, setIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [loading, setLoading] = useState(false);
  const [audioStatus, setAudioStatus] = useState<string | null>(null);
  const router = useRouter();

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
      });
      if (res.status === 401) return router.push("/login");
      if (!res.ok) throw new Error("Failed");
            const data = await res.json();
      
      // ПЕРЕМЕШИВАЕМ СЛОВА ПЕРЕД СОХРАНЕНИЕМ В STATE
      // Явно указываем TS, что мы передаем массив TrainerWord
      const randomizedData = shuffleArray<TrainerWord>(data);


      if (isManual) {
        setWords((prev) => [...prev, ...randomizedData]);
      } else {
        setWords(randomizedData);
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
    if (!currentWord) return;
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
      if (res.ok) handleNext();
    } catch (err) {
      console.error(err);
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
      className={`${styles.pageWrapper} bg-slate-50 min-h-screen font-sans flex flex-col`}
    >
      <main className="flex-1 flex flex-col items-center px-4 w-full pt-8 pb-12">
        {/* Стильный переключатель уровней */}
        <div className="flex bg-white p-1.5 rounded-2xl shadow-sm border border-slate-200 mb-8 w-full max-w-md overflow-x-auto">
          {["A1", "A2", "B1", "B2", "C1"].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setLevel(lvl)}
              className={`flex-1 min-w-[60px] py-2.5 rounded-xl text-sm font-semibold transition-all duration-300 ${level === lvl
                ? "bg-blue-600 text-white shadow-md shadow-blue-500/30 transform scale-105"
                : "bg-transparent text-slate-500 hover:bg-slate-100 hover:text-slate-800"
                }`}
            >
              {lvl}
            </button>
          ))}
        </div>

        {/* Контейнер карточки */}
        <div className="w-full max-w-md relative perspective-1000">
          {loading ? (
            <div className="w-full h-[400px] bg-white rounded-3xl shadow-xl flex flex-col items-center justify-center border border-slate-100">
              <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-4" />
              <p className="text-slate-500 font-medium animate-pulse">
                Загружаем слова...
              </p>
            </div>
          ) : !currentWord ? (
            <div className="w-full h-[400px] bg-white rounded-3xl shadow-xl flex flex-col items-center justify-center p-8 text-center border border-slate-100">
              <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mb-6">
                <span className="text-4xl">🎉</span>
              </div>
              <h3 className="text-xl font-bold text-slate-800 mb-2">
                На сегодня всё!
              </h3>
              <p className="text-slate-500">
                Нет слов для повторения на уровне{" "}
                <span className="font-bold text-blue-600">{level}</span>.
                <br />
                Отдохните или выберите другой уровень.
              </p>
            </div>
          ) : (
            <>
              {/* Сама Карточка */}
              <div
                onClick={() => !showAnswer && setShowAnswer(true)}
                className={`relative w-full rounded-3xl shadow-xl border border-slate-100 bg-white transition-all duration-500 transform-gpu flex flex-col overflow-hidden ${!showAnswer
                  ? "hover:-translate-y-1 hover:shadow-2xl cursor-pointer"
                  : "shadow-blue-900/10 cursor-default"
                  } min-h-[380px]`}
              >
                {/* Бейджи + избранное в шапке карточки */}
                <div className="flex justify-between items-center w-full p-5 absolute top-0 left-0">
                  <span className="bg-blue-50 text-blue-600 px-3 py-1 rounded-full text-xs font-bold tracking-wide border border-blue-100">
                    {currentWord.level}
                  </span>

                  <div className="flex items-center gap-2">
                    {/* @ts-ignore */}
                    {currentWord.next_review && (
                      <span className="flex items-center gap-1.5 bg-amber-50 text-amber-600 px-3 py-1 rounded-full text-xs font-semibold border border-amber-100">
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
                  <h2 className="text-[2.5rem] font-extrabold text-slate-800 text-center leading-tight mb-6">
                    {renderWordWithArticle(currentWord)}
                  </h2>

                  {/* Кнопки аудио (Озвучка + Запись) */}
                  <div className="flex items-center gap-6">
                    {/* Диктор */}
                    <div className="flex flex-col items-center gap-2">
                      <button
                        onClick={(e) => playAudio(e, currentWord.de)}
                        className="w-14 h-14 bg-slate-50 hover:bg-blue-50 text-slate-400 hover:text-blue-600 rounded-full flex items-center justify-center transition-colors shadow-sm border border-slate-100"
                      >
                        <Volume2 size={26} strokeWidth={2.5} />
                      </button>
                      <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                        Послушать
                      </span>
                    </div>

                    {/* Разделитель */}
                    <div className="h-8 w-px bg-slate-200"></div>

                    {/* Микрофон */}
                    <div className="flex flex-col items-center gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          isRecording ? stopRecording() : startRecording();
                        }}
                        className={`w-14 h-14 rounded-full flex items-center justify-center shadow-sm transition-all border ${isRecording
                          ? "bg-red-500 text-white animate-pulse scale-110 border-red-500 shadow-red-500/40"
                          : "bg-slate-50 text-slate-400 hover:text-blue-500 hover:bg-blue-50 border-slate-100"
                          }`}
                      >
                        {isRecording ? (
                          <Square size={24} fill="currentColor" />
                        ) : (
                          <Mic size={24} strokeWidth={2.5} />
                        )}
                      </button>
                      <span
                        className={`text-[10px] uppercase font-bold tracking-wider ${isRecording ? "text-red-500" : "text-slate-400"
                          }`}
                      >
                        {isRecording ? "Идёт запись..." : "Проверить"}
                      </span>
                    </div>
                  </div>

                  {/* Статус записи (если есть) */}
                  {audioStatus && (
                    <div className="mt-4 px-4 py-1.5 bg-slate-50 rounded-lg border border-slate-100 text-xs font-medium text-slate-600">
                      {audioStatus}
                    </div>
                  )}
                </div>

                {/* Низ карточки (Подсказка или Перевод) */}
                <div className="w-full mt-auto">
                  {!showAnswer ? (
                    <div className="w-full py-5 bg-slate-50 border-t border-slate-100 text-center text-slate-400 font-medium flex items-center justify-center gap-2 transition-colors hover:bg-blue-50 hover:text-blue-500">
                      <Eye size={18} /> Нажмите, чтобы увидеть перевод
                    </div>
                  ) : (
                    <div className="w-full bg-blue-50 p-6 border-t border-blue-100 animate-fade-in-up flex flex-col items-center justify-center min-h-[120px]">
                      <p className="text-2xl text-blue-800 font-bold text-center mb-3">
                        {currentWord.ru}
                      </p>
                      {currentWord.example_de && (
                        <div className="text-sm text-blue-700/80 text-center italic bg-white/60 py-2 px-4 rounded-xl border border-blue-100/50">
                          "{currentWord.example_de}"
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Блок кнопок оценок (появляется только после переворота) */}
              <div
                className={`mt-5 grid grid-cols-4 gap-3 transition-all duration-300 ${showAnswer
                  ? "opacity-100 translate-y-0"
                  : "opacity-0 translate-y-4 pointer-events-none absolute w-full"
                  }`}
              >
                <button
                  onClick={() => handleRate(1)}
                  className="flex flex-col items-center justify-center py-3.5 bg-white border-2 border-red-100 rounded-2xl hover:bg-red-50 hover:border-red-300 transition-colors shadow-sm group"
                >
                  <span className="text-red-500 font-bold mb-1 group-hover:scale-110 transition-transform">
                    Сложно
                  </span>
                  <span className="text-[10px] text-slate-400 font-medium uppercase tracking-wide">
                    Завтра
                  </span>
                </button>
                <button
                  onClick={() => handleRate(3)}
                  className="flex flex-col items-center justify-center py-3.5 bg-white border-2 border-amber-100 rounded-2xl hover:bg-amber-50 hover:border-amber-300 transition-colors shadow-sm group"
                >
                  <span className="text-amber-500 font-bold mb-1 group-hover:scale-110 transition-transform">
                    Норма
                  </span>
                  <span className="text-[10px] text-slate-400 font-medium uppercase tracking-wide">
                    3-4 Дня
                  </span>
                </button>
                <button
                  onClick={() => handleRate(5)}
                  className="flex flex-col items-center justify-center py-3.5 bg-white border-2 border-emerald-100 rounded-2xl hover:bg-emerald-50 hover:border-emerald-300 transition-colors shadow-sm group"
                >
                  <span className="text-emerald-500 font-bold mb-1 group-hover:scale-110 transition-transform">
                    Легко
                  </span>
                  <span className="text-[10px] text-slate-400 font-medium uppercase tracking-wide">
                    Неделя+
                  </span>
                </button>
                <button
                  onClick={() => handleRate(0)}
                  className="flex flex-col items-center justify-center py-3.5 bg-slate-800 border-2 border-slate-800 rounded-2xl hover:bg-slate-900 transition-colors shadow-sm group"
                >
                  <span className="text-white font-bold mb-1 group-hover:scale-110 transition-transform">
                    Знаю
                  </span>
                  <span className="text-[10px] text-slate-300 font-medium uppercase tracking-wide">
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
