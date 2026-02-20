"use client";

import React, { useEffect, useState, useRef } from "react";
import styles from "./Trainer.module.css";
import Link from "next/link";

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
  const [loading, setLoading] = useState(true);
  const [audioStatus, setAudioStatus] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const [isRecording, setIsRecording] = useState(false);

  // Новые состояния для уровней
  const [currentLevel, setCurrentLevel] = useState("A1");
  const levels = ["A1", "A2", "B1", "B2", "C1"];

  useEffect(() => {
    const loadWords = async () => {
      setLoading(true);
      try {
        // Делаем запрос к Flask API с явным указанием URL, если локально
        // Если ты запускаешь npm run dev (Next.js на 3000), он должен проксировать на 5000
        const res = await fetch(`/api?action=words&level=${currentLevel}`);

        if (!res.ok) throw new Error("Failed to fetch");
        const data = await res.json();

        if (Array.isArray(data)) {
          setWords(data);
        } else {
          console.error("API returned non-array data:", data);
          setWords([]);
        }

        setIndex(0);
        setShowAnswer(false);
      } catch (e) {
        console.error("Fetch error:", e);
        setWords([]);
        setAudioStatus("Ошибка загрузки слов");
      } finally {
        setLoading(false);
      }
    };
    loadWords();
  }, [currentLevel]);

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
      mr.ondataavailable = (e) => { chunksRef.current.push(e.data); };
      mr.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        const fd = new FormData();
        fd.append("file", blob, "recording.webm");
        setLoading(true);
        setAudioStatus(null);
        try {
          const res = await fetch("/api?action=audio", { method: "POST", body: fd });
          const data = await res.json();
          if (res.ok) { setAudioStatus("✅ Аудио сохранено!"); }
          else { setAudioStatus("❌ Ошибка: " + (data.error || "неизвестно")); }
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

  return (
    <div className={styles.container}>
      {/* Шапка */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <Link href="/" className={styles.logo}>
            🇩🇪 KlarDeutsch
          </Link>
          <nav className={styles.nav}>
            <Link href="/" className={styles.navLink}>Главная</Link>
            <Link href="/dictionary" className={styles.navLink}>Словарь</Link>
            <Link href="/trainer" className={`${styles.navLink} ${styles.activeLink}`}>Тренажер</Link>
            <Link href="/audio" className={styles.navLink}>Записи</Link>
            <Link href="/profile" className={styles.navLink}>Дневник</Link>
          </nav>
        </div>
      </header>

      <main className={styles.main}>
        <h1 style={{ textAlign: 'center', marginBottom: '20px', color: '#1e293b' }}>Тренажер карточек</h1>

        {/* Кнопки переключения уровней */}
        <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginBottom: '30px', flexWrap: 'wrap' }}>
          {levels.map((level) => (
            <button
              key={level}
              onClick={() => setCurrentLevel(level)}
              style={{
                padding: '8px 16px',
                borderRadius: '8px',
                border: 'none',
                fontWeight: 'bold',
                cursor: 'pointer',
                backgroundColor: currentLevel === level ? '#3b82f6' : '#e5e7eb',
                color: currentLevel === level ? '#fff' : '#374151',
                transition: '0.2s',
                boxShadow: currentLevel === level ? '0 4px 6px rgba(59, 130, 246, 0.3)' : 'none'
              }}
            >
              {level}
            </button>
          ))}
        </div>

        {/* Основной контент */}
        {loading ? (
          <div className={styles.card}>
            <h2 className={styles.wordDe}>Загрузка...</h2>
          </div>
        ) : words.length === 0 ? (
          <div className={styles.card}>
            <h2 className={styles.wordDe} style={{ fontSize: '24px' }}>Слов для уровня {currentLevel} пока нет 😔</h2>
            <p style={{ color: '#64748b', marginTop: '10px' }}>Проверьте консоль браузера (F12) на наличие ошибок API</p>
          </div>
        ) : (
          <>
            <div
              className={`${styles.card} ${showAnswer ? styles.flipped : ""}`}
              onClick={() => setShowAnswer(!showAnswer)}
            >
              <div className={styles.cardFront}>
                <span className={styles.levelBadge}>Deutsch • {currentLevel}</span>
                <h2 className={styles.wordDe}>
                  {words[index]?.article && <span className={styles.article}>{words[index].article} </span>}
                  {words[index]?.de}
                </h2>
                <div className={styles.hint}>Нажми, чтобы показать перевод</div>
              </div>

              <div className={styles.cardBack}>
                <span className={styles.levelBadge}>Русский • {currentLevel}</span>
                <h3 className={styles.wordRu}>{words[index]?.ru}</h3>
                {words[index]?.example_de && (
                  <div className={styles.exampleBox}>
                    <p className={styles.exampleDe}>{words[index].example_de}</p>
                    <p className={styles.exampleRu}>{words[index].example_ru}</p>
                  </div>
                )}
              </div>
            </div>

            <div className={styles.controls}>
              <button className={styles.btnSecondary} onClick={(e) => { e.stopPropagation(); prevCard(); }}>
                ← Назад
              </button>
              <span style={{ color: '#64748b', fontWeight: 'bold' }}>
                {index + 1} / {words.length}
              </span>
              <button className={styles.btnPrimary} onClick={(e) => { e.stopPropagation(); nextCard(); }}>
                Дальше →
              </button>
            </div>

            <div className={styles.audioSection}>
              <h3 className={styles.audioTitle}>Произношение</h3>
              <p className={styles.audioDesc}>Запиши себя и послушай</p>

              <button
                className={`${styles.recordBtn} ${isRecording ? styles.recording : ""}`}
                onClick={isRecording ? stopRecording : startRecording}
              >
                {!isRecording ? "● Записать" : "■ Стоп"}
              </button>

              {audioStatus && (
                <div className={styles.audioStatus}>{audioStatus}</div>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
