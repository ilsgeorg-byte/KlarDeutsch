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

  // Добавляем состояние для текущего уровня
  const [currentLevel, setCurrentLevel] = useState("A1");
  const levels = ["A1", "A2", "B1", "B2", "C1"];

  const [audioStatus, setAudioStatus] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const [isRecording, setIsRecording] = useState(false);

  // Загружаем слова при изменении currentLevel
  useEffect(() => {
    const loadWords = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api?action=words&level=${currentLevel}`);
        if (!res.ok) throw new Error("Failed to fetch");
        const data = await res.json();
        setWords(data);
        setIndex(0); // Сбрасываем к первому слову при смене уровня
        setShowAnswer(false);
      } catch (e) {
        console.error(e);
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
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !== "inactive"
    ) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const current = words[index];

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
            <Link href="/trainer" className={`${styles.navLink} ${styles.activeLink}`}>Тренажер</Link>
            <Link href="/audio" className={styles.navLink}>Записи</Link>
          </nav>
        </div>
      </header>

      <main className={styles.main}>

        {/* Кнопки переключения уровней */}
        <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginBottom: '20px', flexWrap: 'wrap' }}>
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
                transition: '0.2s'
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
            <h2 className={styles.wordDe}>Слов для уровня {currentLevel} пока нет 😔</h2>
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
                  {current.article && <span className={styles.article}>{current.article} </span>}
                  {current.de}
                </h2>
              </div>

              {showAnswer ? (
                <div className={styles.cardBack}>
                  <span className={styles.levelBadge}>Русский • {currentLevel}</span>
                  <h3 className={styles.wordRu}>{current.ru}</h3>
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
              <button className={styles.btnSecondary} onClick={(e) => { e.stopPropagation(); prevCard(); }}>
                ← Назад
              </button>
              <span style={{ color: '#666', alignSelf: 'center' }}>
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
