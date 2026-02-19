"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Header from "../../components/Header";
import styles from "../../styles/Shared.module.css";
import { ArrowLeft, Volume2, BookOpen, Tag, Info } from "lucide-react";

interface Word {
    id: number;
    de: string;
    ru: string;
    article?: string;
    verb_forms?: string;
    level: string;
    topic: string;
    example_de?: string;
    example_ru?: string;
    audio_url?: string;
}

export default function WordDetailPage() {
    const params = useParams();
    const router = useRouter();
    const [word, setWord] = useState<Word | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        const fetchWord = async () => {
            try {
                const response = await fetch(`/api/words/${params.id}`);
                if (!response.ok) throw new Error("Слово не найдено");
                const data = await response.json();
                setWord(data);
            } catch (err) {
                console.error("Fetch error:", err);
                setError("Не удалось загрузить информацию о слове");
            } finally {
                setLoading(false);
            }
        };

        if (params.id) {
            fetchWord();
        }
    }, [params.id]);

    const playAudio = (url: string) => {
        const audio = new Audio(url);
        audio.play().catch(e => console.error("Audio play error:", e));
    };

    if (loading) return (
        <div className={styles.pageWrapper}>
            <Header />
            <div className={styles.container} style={{ textAlign: 'center' }}>
                <p>Загрузка...</p>
            </div>
        </div>
    );

    if (error || !word) return (
        <div className={styles.pageWrapper}>
            <Header />
            <div className={styles.container} style={{ textAlign: 'center' }}>
                <p style={{ color: '#ef4444' }}>{error || "Слово не найдено"}</p>
                <button onClick={() => router.back()} className={styles.btnPrev} style={{ marginTop: '20px', padding: '10px 20px' }}>
                    Вернуться назад
                </button>
            </div>
        </div>
    );

    return (
        <div className={styles.pageWrapper}>
            <Header />

            <main className={styles.container} style={{ maxWidth: '700px', justifyContent: 'flex-start' }}>
                <button
                    onClick={() => router.back()}
                    style={{
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        color: '#64748b',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        marginBottom: '30px',
                        padding: 0,
                        fontSize: '1rem'
                    }}
                >
                    <ArrowLeft size={20} />
                    Назад к словарю
                </button>

                <div className={styles.card} style={{ width: '100%', minHeight: 'auto', padding: '40px', alignItems: 'flex-start', textAlign: 'left', cursor: 'default' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', marginBottom: '20px' }}>
                        <span style={{
                            fontSize: '0.9rem',
                            padding: '4px 12px',
                            borderRadius: '16px',
                            background: '#e0f2fe',
                            color: '#0369a1',
                            fontWeight: 'bold'
                        }}>
                            Уровень {word.level}
                        </span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#94a3b8', fontSize: '0.9rem' }}>
                            <Tag size={16} />
                            <span>{word.topic}</span>
                        </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '10px', width: '100%' }}>
                        <h1 style={{ margin: 0, fontSize: '3rem', color: '#1e293b' }}>
                            {word.article && <span style={{ color: '#3b82f6', fontSize: '1.5rem', marginRight: '10px', fontWeight: 'bold' }}>{word.article}</span>}
                            {word.de}
                        </h1>
                        {word.audio_url && (
                            <button
                                onClick={() => playAudio(word.audio_url!)}
                                style={{
                                    background: '#f1f5f9',
                                    border: 'none',
                                    cursor: 'pointer',
                                    color: '#3498db',
                                    padding: '12px',
                                    borderRadius: '50%',
                                    display: 'flex',
                                    alignItems: 'center',
                                    boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
                                }}
                            >
                                <Volume2 size={24} />
                            </button>
                        )}
                    </div>

                    {word.verb_forms && (
                        <div style={{
                            marginBottom: '24px',
                            padding: '12px 16px',
                            background: '#fdf2f8',
                            borderRadius: '12px',
                            borderLeft: '4px solid #db2777',
                            width: '100%'
                        }}>
                            <p style={{ margin: 0, color: '#be185d', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <Info size={18} />
                                Формы глагола:
                            </p>
                            <p style={{ margin: '4px 0 0 26px', fontSize: '1.1rem', color: '#1e293b', fontStyle: 'italic' }}>
                                {word.verb_forms}
                            </p>
                        </div>
                    )}

                    <p style={{ fontSize: '1.8rem', color: '#475569', marginBottom: '40px', fontWeight: '500', borderBottom: '2px solid #f1f5f9', width: '100%', paddingBottom: '20px' }}>
                        {word.ru}
                    </p>

                    <h2 style={{ fontSize: '1.2rem', color: '#1e293b', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <BookOpen size={20} color="#3498db" />
                        Пример использования
                    </h2>

                    <div style={{
                        background: '#f8fafc',
                        padding: '24px',
                        borderRadius: '16px',
                        borderLeft: '6px solid #3498db',
                        width: '100%',
                        boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.02)'
                    }}>
                        <p style={{ margin: 0, fontStyle: 'italic', color: '#1e293b', fontSize: '1.2rem', lineHeight: '1.5' }}>
                            {word.example_de}
                        </p>
                        {word.example_ru && (
                            <p style={{ margin: '12px 0 0 0', color: '#64748b', fontSize: '1rem' }}>
                                {word.example_ru}
                            </p>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
