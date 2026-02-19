"use client";

import React, { useState, useEffect, useCallback } from "react";
import styles from "../styles/Shared.module.css";
import Header from "../components/Header";
import WordCard from "../components/WordCard";
import { Search, Loader2 } from "lucide-react";

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

export default function DictionaryPage() {
    const [query, setQuery] = useState("");
    const [words, setWords] = useState<Word[]>([]);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState("");

    const searchWords = useCallback(async (searchQuery: string) => {
        if (searchQuery.length < 2) {
            setWords([]);
            setMessage("");
            return;
        }

        setLoading(true);
        try {
            const response = await fetch(`/api/words/search?q=${encodeURIComponent(searchQuery)}`);
            const data = await response.json();

            if (data.data) {
                setWords(data.data);
                if (data.data.length === 0) {
                    setMessage("Ничего не найдено");
                } else {
                    setMessage("");
                }
            } else {
                setMessage("Ошибка при поиске");
            }
        } catch (error) {
            console.error("Search error:", error);
            setMessage("Ошибка соединения с сервером");
        } finally {
            setLoading(false);
        }
    }, []);

    // Debounce search
    useEffect(() => {
        const timer = setTimeout(() => {
            searchWords(query);
        }, 300);
        return () => clearTimeout(timer);
    }, [query, searchWords]);

    const playAudio = (url: string) => {
        const audio = new Audio(url);
        audio.play().catch(e => console.error("Audio play error:", e));
    };

    return (
        <div className={styles.pageWrapper}>
            <Header />

            <main className={styles.container} style={{ maxWidth: '800px', justifyContent: 'flex-start' }}>
                <h1 className={styles.pageTitle} style={{ marginBottom: '10px' }}>Словарь</h1>
                <p style={{ textAlign: 'center', color: '#64748b', marginBottom: '30px' }}>
                    Ищи слова, изучай примеры и слушай произношение
                </p>

                <div style={{ position: 'relative', marginBottom: '40px' }}>
                    <div style={{
                        position: 'absolute',
                        left: '16px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        color: '#94a3b8'
                    }}>
                        {loading ? <Loader2 className="animate-spin" size={20} /> : <Search size={20} />}
                    </div>
                    <input
                        type="text"
                        placeholder="Поиск слова (напр. 'Hund' или 'собака')..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        style={{
                            width: '100%',
                            padding: '16px 16px 16px 48px',
                            borderRadius: '16px',
                            border: '2px solid #e2e8f0',
                            fontSize: '1.1rem',
                            outline: 'none',
                            transition: 'border-color 0.2s, box-shadow 0.2s',
                            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)'
                        }}
                        onFocus={(e) => {
                            e.currentTarget.style.borderColor = '#3b82f6';
                            e.currentTarget.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.1)';
                        }}
                        onBlur={(e) => {
                            e.currentTarget.style.borderColor = '#e2e8f0';
                            e.currentTarget.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.05)';
                        }}
                    />
                </div>

                {message && (
                    <p style={{ textAlign: 'center', color: '#94a3b8', marginTop: '20px' }}>{message}</p>
                )}

                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {words.map((word) => (
                        <WordCard key={word.id} word={word} onPlayAudio={playAudio} />
                    ))}
                </div>

                {query.length > 0 && query.length < 2 && (
                    <p style={{ textAlign: 'center', color: '#94a3b8' }}>Введите минимум 2 символа для поиска</p>
                )}

                {query.length === 0 && (
                    <div style={{ textAlign: 'center', marginTop: '40px', color: '#94a3b8' }}>
                        <BookOpen size={48} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
                        <p>Начни вводить слово выше, чтобы увидеть перевод и примеры</p>
                    </div>
                )}
            </main>
        </div>
    );
}

// Simple fallback for BookOpen if lucide-react doesn't have it (though it should)
function BookOpen({ size, style }: { size?: number, style?: React.CSSProperties }) {
    return (
        <svg
            xmlns="http://www.w3.org/2000/svg"
            width={size || 24}
            height={size || 24}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={style}
        >
            <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
            <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
        </svg>
    );
}
