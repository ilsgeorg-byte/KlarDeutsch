"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import styles from "../styles/Shared.module.css";
import Header from "../components/Header";
import WordCard, { Word } from "../components/WordCard";

export default function TrainerPage() {
  const [words, setWords] = useState<Word[]>([]);
  const [level, setLevel] = useState("A1");
  const [index, setIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [audioStatus, setAudioStatus] = useState<string | null>(null);
  const router = useRouter();

  // Проверка авторизации
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) router.push("/login");
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
    const formData = new FormData();
    formData.append("file", blob, "recording.webm");

    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/api/audio", {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
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
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.status === 401) return router.push("/login");
      if (!res.ok) throw new Error("Failed");
      const data = await res.json();

      if (isManual) {
        setWords((prev) => [...prev, ...data]);
      } else {
        setWords(data);
        setIndex(0);
      }
    } catch (e) {
      setAudioStatus("Ошибка загрузки слов");
    } finally {
      if (!isManual) setLoading(false);
    }
  };

  useEffect(() => { loadWords(); }, [level]);

  const handleNext = () => {
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
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ word_id: currentWord.id, rating: rating })
      });
      if (res.ok) handleNext();
    } catch (err) {
      console.error(err);
    }
  };

  const currentWord = words[index];

  return (
    <div className={`${styles.pageWrapper} bg-slate-50 min-h-screen font-sans flex flex-col`}>
      <Header />

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
              <p className="text-slate-500 font-medium animate-pulse">Загружаем слова...</p>
            </div>
          ) : !currentWord ? (
            <div className="w-full h-[400px] bg-white rounded-3xl shadow-xl flex flex-col items-center justify-center p-8 text-center border border-slate-100">
              <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mb-6">
                <span className="text-4xl">🎉</span>
              </div>
              <h3 className="text-xl font-bold text-slate-800 mb-2">На сегодня всё!</h3>
              <p className="text-slate-500">
                Нет слов для повторения на уровне <span className="font-bold text-blue-600">{level}</span>.
                <br />Отдохните или выберите другой уровень.
              </p>
            </div>
          ) : (
            <>
              <WordCard
                key={currentWord.id}
                word={currentWord}
                isRecording={isRecording}
                onToggleRecording={(e) => { e.stopPropagation(); isRecording ? stopRecording() : startRecording() }}
                audioStatus={audioStatus}
                onRate={handleRate}
              />
            </>
          )}
        </div>
      </main>
    </div>
  );
}
