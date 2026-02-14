"use client";

import React, { useEffect, useState, useRef } from "react";
import styles from "./Trainer.module.css";

// ... (типы те же) ...
type Word = {
  id: number;
  level: string;
  topic: string;
  de: string;
  ru: string;
  article: string | null;
  example_de: string;
  example_ru: string;
  audio_url: string | null;
};

export default function TrainerPage() {
  const [words, setWords] = useState<Word[]>([]);
  const [index, setIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [loading, setLoading] = useState(false);
  const [audioStatus, setAudioStatus] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const [isRecording, setIsRecording] = useState(false);

  useEffect(() => {
    const loadWords = async () => {
      try {
        const res = await fetch("/api?action=words&level=A1");
        if (!res.ok) throw new Error("Failed to fetch");
        const data = await res.json();
        setWords(data);
      } catch (e) {
        console.error(e);
        setAudioStatus("Ошибка загрузки слов");
      }
    };
    loadWords();
  }, []);

  // ... (функции nextCard, prevCard, startRecording, stopRecording те же) ...
  const nextCard = () => {
    if (words.length === 0) return;
    setShowAnswer(false);
    setAudioStatus(null);
    setIndex((prev) => (prev + 1) % words.length);
  };

  const prevCard = () => {
    if (words.length === 0) return;
    setShowAnswer(false);
    setAudioStatus(null);
    setIndex((prev) => (prev - 1 + words.length) % words.length);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunksRef.current = [];
      mr.ondataavailable = (e) => {
        chunksRef.current.push(e.data);
      };
      mr.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        const fd = new FormData();
        fd.append("file", blob, "recording.webm");
        setLoading(true);
        setAudioStatus(null);
        try {
          const res = await fetch("/api?action=audio", {
            method: "POST",
            body: fd,
          });
          const data = await res.json();
          if (res.ok) {
            setAudioStatus("✅ Аудио сохранено!");
          } else {
            setAudioStatus("❌ Ошибка: " + (data.error || "неизвестно"));
          }
        } catch (e) {
          console.error(e);
          setAudioStatus("❌ Ошибка отправки");
        } finally {
          setLoading(false);
        }
      };
      mr.start();
      mediaRecorderRef.current = mr;
      setIsRecording(true);
    } catch (e) {
      console.error(e);
      setAudioStatus("Не удалось получить доступ к микрофону");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const current = words[index];

  return (
    <div className={styles.pageWrapper}>
      {/* Шапка */}
       <header className={styles.header}>
        <a href="/" className={styles.logo}>
          <span>🇩🇪</span> KlarDeutsch
        </a>
        <nav className={styles.nav}>
          <a href="/" className={styles.navLink}>Главная</a>
          {/* Ссылка на текущую страницу (Тренажер) */}
          <a href="/trainer" className={`${styles.navLink} ${styles.navLinkActive}`}>Тренажер</a>
          {/* Добавленная ссылка на страницу аудио */}
          <a href="/audio" className={styles.navLink}>Записи</a>
        </nav>
      </header>

      {/* Основной контент */}
      <main className={styles.container}>
        {words.length === 0 ? (
          <h1 className={styles.pageTitle}>Загрузка...</h1>
        ) : (
          <>
            <div className={styles.card} onClick={() => setShowAnswer(!showAnswer)}>
              <div style={{ width: '100%' }}>
                <span className={styles.label}>Deutsch</span>
                <h2 className={styles.germanWord}>
                  {current.article && <span className={styles.article}>{current.article}</span>}
                  {current.de}
                </h2>
              </div>

              {showAnswer ? (
                <div className={styles.answer}>
                  <span className={styles.label}>Русский</span>
                  <p className={styles.russianWord}>{current.ru}</p>
                  
                  <div className={styles.exampleBox}>
                    <p className={styles.exampleDe}>{current.example_de}</p>
                    <p className={styles.exampleRu}>{current.example_ru}</p>
                  </div>
                </div>
              ) : (
                <div className={styles.hint}>Нажми, чтобы показать перевод</div>
              )}
            </div>

            <div className={styles.controls}>
              <button 
                className={`${styles.btn} ${styles.btnPrev}`} 
                onClick={(e) => { e.stopPropagation(); prevCard(); }}
              >
                ← Назад
              </button>
              <button 
                className={`${styles.btn} ${styles.btnNext}`} 
                onClick={(e) => { e.stopPropagation(); nextCard(); }}
              >
                Дальше →
              </button>
            </div>

            <div className={styles.recorder}>
              <h3 className={styles.recorderTitle}>Произношение</h3>
              <p style={{ color: '#94a3b8', fontSize: '0.85rem', margin: 0 }}>Запиши себя и послушай</p>
              
              {!isRecording ? (
                <button 
                  className={styles.recordBtn} 
                  onClick={startRecording}
                  disabled={loading}
                >
                  ● Записать
                </button>
              ) : (
                <button 
                  className={`${styles.recordBtn} ${styles.recording}`} 
                  onClick={stopRecording}
                >
                  ■ Стоп
                </button>
              )}

              {loading && <p style={{ marginTop: 10, color: '#94a3b8', fontSize: '0.9rem' }}>Сохранение...</p>}
              
              {audioStatus && (
                <div className={`${styles.status} ${audioStatus.includes("✅") ? styles.statusSuccess : styles.statusError}`}>
                  {audioStatus}
                </div>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
