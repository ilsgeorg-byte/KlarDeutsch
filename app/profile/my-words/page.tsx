"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Trash2, Upload, Plus, BookOpen, Filter, ChevronDown } from "lucide-react";
import styles from "../../styles/Shared.module.css";
import UploadWordsModal from "../../components/UploadWordsModal";

interface Word {
    id: number;
    de: string;
    ru: string;
    article?: string;
    verb_forms?: string;
    plural?: string;
    level: string;
    topic: string;
    example_de?: string;
    example_ru?: string;
    examples?: { de: string; ru: string }[];
    synonyms?: string;
    antonyms?: string;
    collocations?: string;
    audio_url?: string;
    is_favorite?: boolean;
}

interface WordsResponse {
    data: Word[];
    total: number;
    skip: number;
    limit: number;
}

const ITEMS_PER_PAGE = 20;

export default function MyWordsPage() {
    const router = useRouter();
    const [words, setWords] = useState<Word[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [total, setTotal] = useState(0);
    const [currentPage, setCurrentPage] = useState(1);
    const [selectedLevel, setSelectedLevel] = useState<string>("all");
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
    const [deletingId, setDeletingId] = useState<number | null>(null);
    const [showLevelDropdown, setShowLevelDropdown] = useState(false);

    const loadWords = useCallback(async (page: number, level: string) => {
        setLoading(true);
        setError(null);
        try {
            const token = localStorage.getItem("token");
            if (!token) {
                router.push("/login");
                return;
            }

            const params = new URLSearchParams({
                page: String(page),
                limit: String(ITEMS_PER_PAGE),
            });
            if (level !== "all") {
                params.set("level", level);
            }

            const response = await fetch(`/api/words/my-words?${params.toString()}`, {
                headers: { Authorization: `Bearer ${token}` },
            });

            if (response.status === 401) {
                localStorage.removeItem("token");
                router.push("/login");
                return;
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }

            const data: WordsResponse = await response.json();
            setWords(data.data);
            setTotal(data.total);
        } catch (err) {
            console.error("Failed to load words:", err);
            setError(err instanceof Error ? err.message : "Неизвестная ошибка");
        } finally {
            setLoading(false);
        }
    }, [router]);

    useEffect(() => {
        loadWords(currentPage, selectedLevel);
    }, [currentPage, selectedLevel, loadWords]);

    const handleDelete = async (id: number) => {
        if (!confirm("Вы уверены, что хотите удалить это слово?")) return;

        setDeletingId(id);
        try {
            const token = localStorage.getItem("token");
            const response = await fetch(`/api/words/my-words?id=${id}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` },
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || "Ошибка при удалении");
            }

            // Обновляем список
            setWords(words.filter(w => w.id !== id));
            setTotal(total - 1);
        } catch (err) {
            console.error("Delete error:", err);
            alert("Ошибка при удалении слова");
        } finally {
            setDeletingId(null);
        }
    };

    const handleLevelSelect = (level: string) => {
        setSelectedLevel(level);
        setCurrentPage(1);
        setShowLevelDropdown(false);
    };

    const totalPages = Math.ceil(total / ITEMS_PER_PAGE);

    const renderWordWithArticle = (word: Word) => {
        let text = word.de;

        if (word.article) {
            const articleLower = word.article.toLowerCase().trim();
            let colorClass = "";

            if (articleLower === "der") colorClass = "text-blue-500";
            else if (articleLower === "die") colorClass = "text-red-500";
            else if (articleLower === "das") colorClass = "text-green-500";

            if (colorClass) {
                if (text.toLowerCase().startsWith(articleLower + " ")) {
                    text = text.slice(articleLower.length + 1).trim();
                }
                return (
                    <>
                        <span className={`${colorClass} font-extrabold`}>{word.article}</span>{" "}
                        <span className="text-gray-900 dark:text-white font-extrabold">{text}</span>
                    </>
                );
            }
        }

        return <span className="text-gray-900 dark:text-white font-extrabold">{text}</span>;
    };

    const levelColors: Record<string, string> = {
        A1: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
        A2: "bg-lime-100 text-lime-700 dark:bg-lime-900/30 dark:text-lime-400",
        B1: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
        B2: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
        C1: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
    };

    return (
        <div className={styles.pageWrapper}>
            <main className={`${styles.container} max-w-5xl mx-auto px-6 py-12 w-full`}>
                {/* Заголовок */}
                <header className="mb-8">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <BookOpen className="text-blue-600 dark:text-blue-400" size={32} />
                            <div>
                                <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white">
                                    Мои слова
                                </h1>
                                <p className="text-gray-500 dark:text-gray-400 text-sm">
                                    Ваши личные слова ({total})
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={() => setIsUploadModalOpen(true)}
                            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors shadow-lg shadow-blue-600/30"
                        >
                            <Plus size={20} />
                            Добавить
                        </button>
                    </div>

                    {/* Фильтр по уровням */}
                    <div className="relative">
                        <button
                            onClick={() => setShowLevelDropdown(!showLevelDropdown)}
                            className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                        >
                            <Filter size={18} />
                            Уровень: {selectedLevel === "all" ? "Все" : selectedLevel}
                            <ChevronDown size={16} className={`transition-transform ${showLevelDropdown ? "rotate-180" : ""}`} />
                        </button>

                        {showLevelDropdown && (
                            <div className="absolute top-full left-0 mt-2 w-48 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl z-10 overflow-hidden">
                                <button
                                    onClick={() => handleLevelSelect("all")}
                                    className={`w-full text-left px-4 py-2 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                                        selectedLevel === "all" ? "bg-blue-50 dark:bg-blue-900/20 text-blue-600" : "text-gray-700 dark:text-gray-300"
                                    }`}
                                >
                                    Все уровни
                                </button>
                                {["A1", "A2", "B1", "B2", "C1"].map(level => (
                                    <button
                                        key={level}
                                        onClick={() => handleLevelSelect(level)}
                                        className={`w-full text-left px-4 py-2 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center gap-2 ${
                                            selectedLevel === level ? "bg-blue-50 dark:bg-blue-900/20 text-blue-600" : "text-gray-700 dark:text-gray-300"
                                        }`}
                                    >
                                        <span className={`text-xs px-2 py-0.5 rounded-full font-bold uppercase ${levelColors[level]}`}>
                                            {level}
                                        </span>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </header>

                {/* Контент */}
                {loading ? (
                    <div className="flex justify-center items-center h-64">
                        <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                    </div>
                ) : error ? (
                    <div className="bg-white dark:bg-gray-800 p-12 rounded-3xl shadow-sm text-center">
                        <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
                            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </div>
                        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Ошибка загрузки</h3>
                        <p className="text-gray-500 dark:text-gray-400 mb-6">{error}</p>
                        <button
                            onClick={() => loadWords(currentPage, selectedLevel)}
                            className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition-colors"
                        >
                            Попробовать снова
                        </button>
                    </div>
                ) : words.length === 0 ? (
                    <div className="bg-white dark:bg-gray-800 p-12 rounded-3xl shadow-sm text-center">
                        <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center mx-auto mb-4">
                            <BookOpen size={32} />
                        </div>
                        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                            Пока нет слов
                        </h3>
                        <p className="text-gray-500 dark:text-gray-400 mb-6">
                            Добавьте свои первые слова для изучения
                        </p>
                        <button
                            onClick={() => setIsUploadModalOpen(true)}
                            className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition-colors inline-flex items-center gap-2"
                        >
                            <Plus size={20} />
                            Добавить первое слово
                        </button>
                    </div>
                ) : (
                    <>
                        {/* Список слов */}
                        <div className="space-y-3">
                            {words.map((word) => (
                                <div
                                    key={word.id}
                                    onClick={() => router.push(`/dictionary/${word.id}`)}
                                    className="bg-white dark:bg-gray-800 p-4 rounded-2xl border border-gray-100 dark:border-gray-700 hover:border-blue-200 dark:hover:border-blue-600 transition-all flex items-center justify-between gap-4 cursor-pointer"
                                >
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="font-bold text-lg text-gray-900 dark:text-white truncate">
                                                {renderWordWithArticle(word)}
                                            </span>
                                            <span className={`text-xs px-2 py-0.5 rounded-full font-bold uppercase ${levelColors[word.level]}`}>
                                                {word.level}
                                            </span>
                                        </div>
                                        <div className="text-gray-600 dark:text-gray-300 text-sm">
                                            {word.ru}
                                        </div>
                                        {word.topic && (
                                            <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                                                📁 {word.topic}
                                            </div>
                                        )}
                                        {word.verb_forms && (
                                            <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                                                🔤 {word.verb_forms}
                                            </div>
                                        )}
                                    </div>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleDelete(word.id);
                                        }}
                                        disabled={deletingId === word.id}
                                        className="p-2 text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors disabled:opacity-50"
                                        title="Удалить слово"
                                    >
                                        {deletingId === word.id ? (
                                            <div className="w-5 h-5 border-2 border-red-600 border-t-transparent rounded-full animate-spin"></div>
                                        ) : (
                                            <Trash2 size={20} />
                                        )}
                                    </button>
                                </div>
                            ))}
                        </div>

                        {/* Пагинация */}
                        {totalPages > 1 && (
                            <div className="flex justify-center items-center gap-2 mt-8">
                                <button
                                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                    disabled={currentPage === 1}
                                    className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                                >
                                    Назад
                                </button>
                                <span className="text-gray-600 dark:text-gray-400 font-medium">
                                    Страница {currentPage} из {totalPages}
                                </span>
                                <button
                                    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                    disabled={currentPage === totalPages}
                                    className="px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                                >
                                    Вперёд
                                </button>
                            </div>
                        )}
                    </>
                )}
            </main>

            {/* Модальное окно загрузки */}
            <UploadWordsModal
                isOpen={isUploadModalOpen}
                onClose={() => setIsUploadModalOpen(false)}
                onSuccess={() => {
                    loadWords(currentPage, selectedLevel);
                }}
            />
        </div>
    );
}
