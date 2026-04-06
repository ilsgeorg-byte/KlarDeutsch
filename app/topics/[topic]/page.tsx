"use client";

import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useWordsByTopic } from "../../lib/hooks";
import WordCard from "../../components/WordCard";
import Header from "../../components/Header";
import Footer from "../../components/Footer";
import { ChevronLeft, LayoutGrid, List as ListIcon, Loader2 } from "lucide-react";
import styles from "../../styles/Shared.module.css";

export default function TopicPage() {
    const params = useParams();
    const router = useRouter();
    const topic = params && typeof params.topic === 'string' ? decodeURIComponent(params.topic) : "";
    
    const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
    const [page, setPage] = useState(0);
    const limit = 20;

    const { words, total, isLoading, error } = useWordsByTopic(topic, page * limit, limit);

    const playAudio = (url: string) => {
        const audio = new Audio(url);
        audio.play().catch(err => console.error("Error playing audio:", err));
    };

    if (!topic) return null;

    return (
        <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-900">
            <Header />

            <main className="flex-grow container mx-auto px-4 py-8">
                {/* Хлебные крошки и заголовок */}
                <div className="mb-8">
                    <button 
                        onClick={() => router.back()}
                        className="flex items-center gap-2 text-slate-500 hover:text-blue-600 transition-colors mb-4"
                    >
                        <ChevronLeft size={20} />
                        <span>Назад</span>
                    </button>
                    
                    <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                        <div>
                            <h1 className="text-3xl md:text-4xl font-extrabold text-slate-900 dark:text-white mb-2">
                                Тема: <span className="text-blue-600">{topic}</span>
                            </h1>
                            <p className="text-slate-500 dark:text-slate-400">
                                Найдено слов: <span className="font-semibold text-slate-700 dark:text-slate-200">{total}</span>
                            </p>
                        </div>

                        <div className="flex bg-white dark:bg-slate-800 p-1 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm">
                            <button 
                                onClick={() => setViewMode("grid")}
                                className={`p-2 rounded-md transition-all ${viewMode === "grid" ? "bg-blue-50 text-blue-600 shadow-sm" : "text-slate-400 hover:text-slate-600"}`}
                            >
                                <LayoutGrid size={20} />
                            </button>
                            <button 
                                onClick={() => setViewMode("list")}
                                className={`p-2 rounded-md transition-all ${viewMode === "list" ? "bg-blue-50 text-blue-600 shadow-sm" : "text-slate-400 hover:text-slate-600"}`}
                            >
                                <ListIcon size={20} />
                            </button>
                        </div>
                    </div>
                </div>

                {isLoading ? (
                    <div className="flex flex-col items-center justify-center py-20">
                        <Loader2 className="animate-spin text-blue-600 mb-4" size={48} />
                        <p className="text-slate-500 font-medium">Загружаем слова из темы...</p>
                    </div>
                ) : error ? (
                    <div className="bg-red-50 border border-red-200 text-red-700 p-6 rounded-xl text-center">
                        <p className="font-bold text-lg mb-2">Упс! Ошибка загрузки</p>
                        <p>Не удалось получить слова для этой темы. Пожалуйста, попробуйте позже.</p>
                    </div>
                ) : words.length === 0 ? (
                    <div className="bg-white dark:bg-slate-800 border border-dashed border-slate-300 dark:border-slate-700 p-12 rounded-2xl text-center">
                        <p className="text-slate-500 text-lg">В этой теме пока нет слов.</p>
                    </div>
                ) : (
                    <div className={viewMode === "grid" 
                        ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" 
                        : "flex flex-col gap-4 max-w-4xl mx-auto"
                    }>
                        {words.map((word) => (
                            <WordCard 
                                key={word.id} 
                                word={word} 
                                onPlayAudio={playAudio}
                            />
                        ))}
                    </div>
                )}

                {/* Пагинация */}
                {total > limit && (
                    <div className="mt-12 flex justify-center gap-2">
                        {Array.from({ length: Math.ceil(total / limit) }).map((_, i) => (
                            <button
                                key={i}
                                onClick={() => {
                                    setPage(i);
                                    window.scrollTo({ top: 0, behavior: 'smooth' });
                                }}
                                className={`w-10 h-10 rounded-lg font-bold transition-all ${
                                    page === i 
                                    ? "bg-blue-600 text-white shadow-lg shadow-blue-200" 
                                    : "bg-white text-slate-600 hover:bg-slate-50 border border-slate-200"
                                }`}
                            >
                                {i + 1}
                            </button>
                        ))}
                    </div>
                )}
            </main>

            <Footer />
        </div>
    );
}
