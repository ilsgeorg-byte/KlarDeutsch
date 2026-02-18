"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Mic, Square, Volume2, ArrowRight, Eye, EyeOff, Home, Loader2 } from "lucide-react";
import styles from "../styles/Shared.module.css";

interface Word {
  id: number;
  de: string;
  ru: string;
  example_de?: string;
  example_ru?: string;
  level: string;
  article?: string;
  next_review?: string;
}

import Header from "../components/Header";

export default function TrainerPage() {
  const [words, setWords] = useState<Word[]>([]);
  const [level, setLevel] = useState("A1");
  const [index, setIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [loading, setLoading] = useState(false);
  const [audioStatus, setAudioStatus] = useState<string | null>(null);
  const router = useRouter();

  // Проверка авторизации
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
    }
  }, []);

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
    console.log("Размер блоба:", blob.size, "байт");

    const formData = new FormData();
    formData.append("file", blob, "recording.webm");

    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/api/audio", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        },
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        console.log("Загрузка успешна:", data);
        setAudioStatus("Записано! ✅");
      } else {
        const error = await res.json();
        console.error("Ошибка сервера:", error);
        setAudioStatus("Ошибка загрузки ❌");
      }
    } catch (e) {
      console.error("Ошибка сети:", e);
      setAudioStatus("Ошибка сети");
    }
  };
  // ---------------------

  useEffect(() => {
    const loadWords = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem("token");
        const res = await fetch(`/api/trainer/words?level=${level}`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (res.status === 401) {
          router.push("/login");
          return;
        }
        if (!res.ok) throw new Error("Failed");
        const data = await res.json();
        setWords(data);
        setIndex(0);
        setShowAnswer(false);
      } catch (e) {
        console.error("Ошибка при загрузке слов:", e);
        setAudioStatus("Ошибка загрузки слов");
      } finally {
        setLoading(false);
      }
    };
    loadWords();
  }, [level]);

  const handleNext = () => {
    setShowAnswer(false);
    setAudioStatus(null);
    if (words.length > 0) {
      setIndex((prev) => (prev + 1) % words.length);
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
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          word_id: currentWord.id,
          rating: rating
        })
      });

      if (res.ok) {
        handleNext();
      }
    } catch (err) {
      console.error("Ошибка сохранения прогресса:", err);
    }
  };

  const playAudio = (text: string) => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "de-DE";
    window.speechSynthesis.speak(utterance);
  };

  const currentWord = words[index];

  return (
    <div className={styles.pageWrapper}>
      <Header />

      <main className="flex-1 flex flex-col items-center px-4 py-6 w-full">

        <div className="flex flex-wrap gap-2 mb-8 justify-center">
          {["A1", "A2", "B1", "B2", "C1"].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setLevel(lvl)}
              className={`px-4 py-2 rounded-lg font-bold transition-all ${level === lvl
                ? "bg-blue-600 text-white shadow-md transform scale-105"
                : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-200"
                }`}
            >
              {lvl}
            </button>
          ))}
        </div>

        <div className="w-full max-w-md bg-white rounded-2xl shadow-xl overflow-hidden flex flex-col relative min-h-[500px]">
          {loading ? (
            <div className="flex-1 flex items-center justify-center flex-col gap-4">
              <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-gray-500">Подготовка сессии...</p>
            </div>
          ) : !currentWord ? (
            <div className="flex-1 flex items-center justify-center p-8 text-center text-gray-500">
              Пока нет слов для повторения на уровне {level}. <br />Попробуйте другой уровень или зайдите позже!
            </div>
          ) : (
            <div className="flex-1 flex flex-col p-6">
              <div className="flex justify-between items-center mb-4">
                <span className="text-xs font-bold text-blue-500 uppercase tracking-wider">{currentWord.level}</span>
                {/* @ts-ignore */}
                {currentWord.next_review && (
                  <span className="text-[10px] text-gray-400 bg-gray-50 px-2 py-1 rounded">Повторение</span>
                )}
              </div>

              <div className="flex flex-col items-center text-center mb-6 mt-4">
                <h2 className="text-4xl font-bold text-gray-800 mb-4">
                  {/* @ts-ignore */}
                  {currentWord.article && !currentWord.de.toLowerCase().startsWith(currentWord.article.toLowerCase() + " ") && (
                    <span className="text-blue-500 text-2xl mr-2">{currentWord.article}</span>
                  )}
                  {currentWord.de}
                </h2>
                <button onClick={() => playAudio(currentWord.de)} className="p-3 bg-blue-50 text-blue-600 rounded-full hover:bg-blue-100 transition"><Volume2 size={28} /></button>
              </div>

              <div className={`transition-all duration-300 overflow-hidden ${showAnswer ? "max-h-60 opacity-100 mb-6" : "max-h-0 opacity-0"}`}>
                <div className="bg-gray-50 p-4 rounded-xl text-center border border-gray-100">
                  <p className="text-xl text-green-700 font-medium mb-1">{currentWord.ru}</p>
                  {currentWord.example_de && (
                    <div className="text-sm text-gray-500 mt-2 pt-2 border-t border-gray-200 italic">
                      {currentWord.example_de}
                    </div>
                  )}
                </div>
              </div>

              <div className="mt-auto">
                {!showAnswer ? (
                  <button onClick={() => setShowAnswer(true)} className="w-full py-4 bg-blue-600 text-white rounded-xl font-bold shadow-lg hover:bg-blue-700 transition flex items-center justify-center gap-2">
                    <Eye size={20} /> Показать перевод
                  </button>
                ) : (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    <button
                      onClick={() => handleRate(0)}
                      className="flex flex-col items-center gap-1 py-3 bg-gray-100 text-gray-500 rounded-xl hover:bg-gray-200 transition border border-gray-200"
                    >
                      <span className="font-bold text-sm">Знаю</span>
                      <span className="text-[10px] opacity-70">Убрать</span>
                    </button>
                    <button
                      onClick={() => handleRate(1)}
                      className="flex flex-col items-center gap-1 py-3 bg-red-50 text-red-600 rounded-xl hover:bg-red-100 transition border border-red-100"
                    >
                      <span className="font-bold text-sm">Сложно</span>
                      <span className="text-[10px] opacity-70">Завтра</span>
                    </button>
                    <button
                      onClick={() => handleRate(3)}
                      className="flex flex-col items-center gap-1 py-3 bg-blue-50 text-blue-600 rounded-xl hover:bg-blue-100 transition border border-blue-100"
                    >
                      <span className="font-bold text-sm">Норма</span>
                      <span className="text-[10px] opacity-70">3-4 дня</span>
                    </button>
                    <button
                      onClick={() => handleRate(5)}
                      className="flex flex-col items-center gap-1 py-3 bg-green-50 text-green-600 rounded-xl hover:bg-green-100 transition border border-green-100"
                    >
                      <span className="font-bold text-sm">Легко</span>
                      <span className="text-[10px] opacity-70">Неделя+</span>
                    </button>
                  </div>
                )}
              </div>

              <div className="flex justify-center mt-6 pt-4 border-t border-gray-100">
                <button onClick={isRecording ? stopRecording : startRecording} className={`p-4 rounded-full transition-all shadow-md ${isRecording ? "bg-red-500 text-white animate-pulse scale-110" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}>
                  {isRecording ? <Square size={24} fill="currentColor" /> : <Mic size={24} />}
                </button>
              </div>
              {audioStatus && <p className="text-center text-xs text-gray-400 mt-2 h-4">{audioStatus}</p>}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
