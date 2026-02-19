"use client";

import React, { useState, useEffect, useCallback } from "react";
import styles from "../styles/Shared.module.css";
import Header from "../components/Header";
import WordCard from "../components/WordCard";
import { Search, Loader2, Plus, BookOpen } from "lucide-react";
import AddWordModal from "../components/AddWordModal";

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
    is_favorite?: boolean;
}

export default function DictionaryPage() {
    const [query, setQuery] = useState("");
    const [words, setWords] = useState<Word[]>([]);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState("");
    const [isModalOpen, setIsModalOpen] = useState(false);

    const searchWords = useCallback(async (searchQuery: string) => {
        if (searchQuery.length < 2) {
            setWords([]);
            setMessage("");
            return;
        }

        setLoading(true);
        try {
            const token = localStorage.getItem("token");
            const response = await fetch(`/api/words/search?q=${encodeURIComponent(searchQuery)}`, {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });
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

    const toggleFavorite = async (wordId: number) => {
        try {
            const token = localStorage.getItem('token');
            if (!token) {
                alert("Пожалуйста, войдите в систему, чтобы добавлять слова в избранное");
                return;
            }

            const response = await fetch(`/api/words/${wordId}/favorite`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                setWords(prevWords =>
                    prevWords.map(w => w.id === wordId ? { ...w, is_favorite: !w.is_favorite } : w)
                );
            }
        } catch (err) {
            console.error("Favorite error:", err);
        }
    };

    return (
        <div className={styles.pageWrapper}>
            <Header />

            <main className={styles.container} style={{ maxWidth: '800px', justifyContent: 'flex-start' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', marginBottom: '10px' }}>
                    <h1 className={styles.pageTitle} style={{ margin: 0 }}>Словарь</h1>
                    <button
                        onClick={() => setIsModalOpen(true)}
                        style={{
                            padding: '10px 20px',
                            backgroundColor: '#3b82f6',
                            color: 'white',
                            border: 'none',
                            borderRadius: '12px',
                            fontWeight: 'bold',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            boxShadow: '0 4px 6px -1px rgba(59, 130, 246, 0.3)',
                            transition: 'all 0.2s'
                        }}
                    >
                        <Plus size={20} />
                        Добавить слово
                    </button>
                </div>
                <p style={{ textAlign: 'center', color: '#64748b', marginBottom: '30px' }}>
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
                    />
                </div>

                {message && (
                    <p style={{ textAlign: 'center', color: '#94a3b8', marginTop: '20px' }}>{message}</p>
                )}

                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', width: '100%' }}>
                    {words.map((word) => (
                        <WordCard
                            key={word.id}
                            word={word}
                            onPlayAudio={playAudio}
                            onToggleFavorite={toggleFavorite}
                        />
                    ))}
                </div>

                {query.length > 0 && query.length < 2 && (
                    <p style={{ textAlign: 'center', color: '#94a3b8', marginTop: '20px' }}>Введите минимум 2 символа для поиска</p>
                )}

                {query.length === 0 && (
                    <div style={{ textAlign: 'center', marginTop: '40px', color: '#94a3b8' }}>
                        <BookOpen size={48} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
                        <p>Начни вводить слово выше, чтобы увидеть перевод и примеры</p>
                    </div>
                )}

                <AddWordModal
                    isOpen={isModalOpen}
                    onClose={() => setIsModalOpen(false)}
                    onSuccess={(id) => {
                        searchWords(query);
                    }}
                />
            </main>
        </div>
    );
}
