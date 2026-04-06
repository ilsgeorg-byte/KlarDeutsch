"use client";

import React, { useState, useEffect } from "react";
import styles from "../styles/Shared.module.css";
import WordCard from "../components/WordCard";
import { Search, Loader2, BookOpen } from "lucide-react";
import { useWordSearch } from "../lib/hooks";

export default function DictionaryPage() {
    const [query, setQuery] = useState("");
    
    // Используем хук вместо ручного fetch
    // Debounce 300ms делаем на уровне query
    const [debouncedQuery, setDebouncedQuery] = useState("");

    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedQuery(query);
        }, 300);
        return () => clearTimeout(timer);
    }, [query]);

    const { results: words, isLoading, error } = useWordSearch(debouncedQuery, 50);

    const playAudio = (url: string) => {
        const audio = new Audio(url);
        audio.play().catch(e => console.error("Audio play error:", e));
    };

    return (
        <div className={`${styles.pageWrapper} bg-slate-50 dark:bg-gray-900 min-h-screen`}>

            <main className={styles.container} style={{ maxWidth: '800px', justifyContent: 'flex-start' }}>
                <h1 className={`${styles.pageTitle} text-slate-800 dark:text-white`} style={{ margin: 0, marginBottom: '10px' }}>Словарь</h1>
                <p className="text-slate-600 dark:text-gray-400" style={{ textAlign: 'center', marginBottom: '30px' }}>
                    Ищи слова, изучай примеры и слушай произношение
                </p>

                <div style={{ position: 'relative', marginBottom: '40px', width: '100%' }}>
                    <div style={{
                        position: 'absolute',
                        left: '16px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        color: '#94a3b8'
                    }}>
                        {isLoading ? <Loader2 className="animate-spin" size={20} /> : <Search size={20} />}
                    </div>
                    <input
                        type="text"
                        placeholder="Поиск слова (напр. 'Hund' или 'собака')..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        className="dark:bg-gray-800 dark:border-gray-600 dark:text-white"
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
                    />
                </div>

                {isLoading && (
                    <p className="text-slate-500 dark:text-gray-400" style={{ textAlign: 'center', marginTop: '20px' }}>
                        <Loader2 className="animate-spin inline mr-2" size={16} />
                        Поиск...
                    </p>
                )}

                {error && (
                    <p className="text-red-500" style={{ textAlign: 'center', marginTop: '20px' }}>
                        {error.message || "Ошибка при поиске"}
                    </p>
                )}

                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', width: '100%' }} className="dark">
                    {words.map((word) => (
                        <WordCard
                            key={word.id}
                            word={word}
                            onPlayAudio={playAudio}
                        />
                    ))}
                </div>

                {query.length > 0 && query.length < 2 && (
                    <p className="text-slate-500 dark:text-gray-400" style={{ textAlign: 'center', marginTop: '20px' }}>Введите минимум 2 символа для поиска</p>
                )}

                {query.length === 0 && (
                    <div className="text-slate-500 dark:text-gray-400" style={{ textAlign: 'center', marginTop: '40px' }}>
                        <BookOpen size={48} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
                        <p>Начни вводить слово выше, чтобы увидеть перевод и примеры</p>
                    </div>
                )}
            </main>
        </div>
    );
}
