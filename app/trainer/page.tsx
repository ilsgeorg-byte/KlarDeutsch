"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link"; // Для кнопки "Домой"
import { Mic, Square, Volume2, ArrowRight, Eye, EyeOff, Home } from "lucide-react";
import styles from "../styles/Shared.module.css";

interface Word {
  id: number;
  de: string;
  ru: string;
  example_de?: string;
  example_ru?: string;
  level: string;
}

export default function TrainerPage() {
  const [words, setWords] = useState<Word[]>([]);
  const [level, setLevel] = useState("A1");
  const [index, setIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [loading, setLoading] = useState(false);
  const [audioStatus, setAudioStatus] = useState<string | null>(null);

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
      const res = await fetch("http://127.0.0.1:5000/api/audio", {
        method: "POST",
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
        const res = await fetch(`http://127.0.0.1:5000/api/words?level=${level}`);
        if (!res.ok) throw new Error("Failed");
        const data = await res.json();
        setWords(data.data);
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
    setIndex((prev) => (prev + 1) % words.length);
  };

  const playAudio = (text: string) => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "de-DE";
    window.speechSynthesis.speak(utterance);
  };

  const currentWord = words[index];

  return (
    <div className={styles.pageWrapper}>
      {/* Шапка */}
      <header className={styles.header}>
        <a href="/" className={styles.logo}>
          <span>🇩🇪</span> KlarDeutsch
        </a>
        <nav className={styles.nav}>
          <a href="/" className={styles.navLink}>Главная</a>
          <a href="/trainer" className={`${styles.navLink} ${styles.navLinkActive}`}>Тренажер</a>
          <a href="/audio" className={styles.navLink}>Записи</a>
        </nav>
      </header>

      {/* Основной контент */}
      <main className="flex-1 flex flex-col items-center px-4 py-6 w-full">
      
        {/* КНОПКИ УРОВНЕЙ */}
        <div className="flex flex-wrap gap-2 mb-8 justify-center">
          {["A1", "A2", "B1", "B2", "C1"].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setLevel(lvl)}
              className={`px-4 py-2 rounded-lg font-bold transition-all ${
                level === lvl
                  ? "bg-blue-600 text-white shadow-md transform scale-105"
                  : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-200"
              }`}
            >
              {lvl}
            </button>
          ))}
        </div>

        {/* КАРТОЧКА */}
        <div className="w-full max-w-md bg-white rounded-2xl shadow-xl overflow-hidden flex flex-col relative min-h-[450px]">
           {/* ... тут весь код карточки без изменений ... */}
           {loading ? (
             <div className="flex-1 flex items-center justify-center flex-col gap-4">
               <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
               <p className="text-gray-500">Загрузка...</p>
             </div>
           ) : !currentWord ? (
             <div className="flex-1 flex items-center justify-center p-8 text-center text-gray-500">
               Нет слов для этого уровня :(
             </div>
           ) : (
             <div className="flex-1 flex flex-col p-6">
                {/* ... содержимое карточки ... */}
                
                {/* (вставь сюда то, что было внутри карточки) */}
                <div className="flex flex-col items-center text-center mb-6 mt-4">
                  <h2 className="text-4xl font-bold text-gray-800 mb-4">{currentWord.de}</h2>
                  <button onClick={() => playAudio(currentWord.de)} className="p-3 bg-blue-50 text-blue-600 rounded-full hover:bg-blue-100 transition"><Volume2 size={28} /></button>
                </div>

                <div className={`transition-all duration-300 overflow-hidden ${showAnswer ? "max-h-60 opacity-100 mb-6" : "max-h-0 opacity-0"}`}>
                  <div className="bg-gray-50 p-4 rounded-xl text-center border border-gray-100">
                    <p className="text-xl text-green-700 font-medium mb-1">{currentWord.ru}</p>
                    {currentWord.example_de && <div className="text-sm text-gray-500 mt-2 pt-2 border-t border-gray-200 italic">{currentWord.example_de}</div>}
                  </div>
                </div>

                <div className="mt-auto grid grid-cols-2 gap-3">
                  <button onClick={() => setShowAnswer(!showAnswer)} className={`py-3 px-4 rounded-xl font-semibold flex justify-center items-center gap-2 transition ${showAnswer ? "bg-gray-100 text-gray-700" : "bg-blue-600 text-white shadow-lg"}`}>
                    {showAnswer ? <EyeOff size={18} /> : <Eye size={18} />} {showAnswer ? "Скрыть" : "Перевод"}
                  </button>
                  <button onClick={handleNext} className="py-3 px-4 bg-gray-800 text-white rounded-xl font-semibold flex justify-center items-center gap-2 hover:bg-black transition">
                    Далее <ArrowRight size={18} />
                  </button>
                </div>

                <div className="flex justify-center mt-4 pt-4 border-t border-gray-100">
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
