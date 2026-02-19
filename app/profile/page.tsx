"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Header from "../components/Header";
import { BookOpen, CheckCircle, TrendingUp, Award, Layers, Star } from "lucide-react";
import styles from "../styles/Shared.module.css";

interface Stats {
    total_words: { [key: string]: number };
    user_progress: { [key: string]: number };
    detailed: Array<{
        level: string;
        status: string;
        count: number;
    }>;
}

interface Word {
    id: number;
    de: string;
    ru: string;
    article?: string;
    level: string;
    topic: string;
}

export default function ProfilePage() {
    const [stats, setStats] = useState<Stats | null>(null);
    const [favorites, setFavorites] = useState<Word[]>([]);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        const fetchData = async () => {
            const token = localStorage.getItem("token");
            if (!token) {
                router.push("/login");
                return;
            }

            try {
                // Fetch Stats
                const statsRes = await fetch("/api/trainer/stats", {
                    headers: { "Authorization": `Bearer ${token}` }
                });
                if (statsRes.status === 401) {
                    router.push("/login");
                    return;
                }
                if (statsRes.ok) {
                    const data = await statsRes.json();
                    setStats(data);
                }

                // Fetch Favorites
                const favsRes = await fetch("/api/favorites", {
                    headers: { "Authorization": `Bearer ${token}` }
                });
                if (favsRes.ok) {
                    const data = await favsRes.json();
                    setFavorites(data.words || []);
                }
            } catch (err) {
                console.error("Failed to fetch data:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [router]);

    const totalWordsInDb = stats ? Object.values(stats.total_words).reduce((a, b) => a + b, 0) : 0;
    const knownWords = stats?.user_progress["known"] || 0;
    const learningWords = stats?.user_progress["learning"] || 0;

    return (
        <div className={styles.pageWrapper}>
            <Header />

            <main className="max-w-5xl mx-auto px-6 py-12 w-full">
                <header className="mb-12">
                    <h1 className="text-4xl font-extrabold text-gray-900 mb-2">Ваш профиль</h1>
                    <p className="text-gray-500 text-lg">Статистика и избранные слова в KlarDeutsch</p>
                </header>

                {loading ? (
                    <div className="flex justify-center items-center h-64">
                        <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                    </div>
                ) : !stats ? (
                    <div className="bg-white p-12 rounded-3xl shadow-sm text-center">
                        <p className="text-gray-500">Не удалось загрузить данные. Попробуйте обновить страницу.</p>
                    </div>
                ) : (
                    <div className="flex flex-col gap-12">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">

                            {/* Карточки основных показателей */}
                            <div className="bg-white p-8 rounded-3xl shadow-sm border border-gray-100 flex flex-col items-center text-center">
                                <div className="w-16 h-16 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mb-4">
                                    <Layers size={32} />
                                </div>
                                <span className="text-sm font-medium text-gray-400 mb-1 uppercase tracking-wider">Всего в базе</span>
                                <span className="text-4xl font-black text-gray-900">{totalWordsInDb}</span>
                                <span className="text-xs text-gray-400 mt-2">слов всех уровней</span>
                            </div>

                            <div className="bg-white p-8 rounded-3xl shadow-sm border border-gray-100 flex flex-col items-center text-center">
                                <div className="w-16 h-16 bg-green-50 text-green-600 rounded-2xl flex items-center justify-center mb-4">
                                    <CheckCircle size={32} />
                                </div>
                                <span className="text-sm font-medium text-gray-400 mb-1 uppercase tracking-wider">Выучено</span>
                                <span className="text-4xl font-black text-gray-900">{knownWords}</span>
                                <span className="text-xs text-gray-400 mt-2">помечено как "знаю"</span>
                            </div>

                            <div className="bg-white p-8 rounded-3xl shadow-sm border border-gray-100 flex flex-col items-center text-center">
                                <div className="w-16 h-16 bg-orange-50 text-orange-600 rounded-2xl flex items-center justify-center mb-4">
                                    <TrendingUp size={32} />
                                </div>
                                <span className="text-sm font-medium text-gray-400 mb-1 uppercase tracking-wider">В процессе</span>
                                <span className="text-4xl font-black text-gray-900">{learningWords}</span>
                                <span className="text-xs text-gray-400 mt-2">активно тренируются</span>
                            </div>
                        </div>

                        {/* Секция избранных слов */}
                        <div className="bg-white p-8 rounded-3xl shadow-sm border border-gray-100">
                            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
                                <Star className="text-yellow-500" fill="#f59e0b" /> Избранные слова ({favorites.length})
                            </h2>

                            {favorites.length === 0 ? (
                                <p className="text-gray-500 py-4">У вас пока нет избранных слов. Добавляйте их в словаре!</p>
                            ) : (
                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                    {favorites.map((word) => (
                                        <button
                                            key={word.id}
                                            onClick={() => router.push(`/dictionary/${word.id}`)}
                                            className="p-4 border border-gray-100 rounded-2xl hover:border-blue-200 hover:bg-blue-50/30 transition-all text-left flex flex-col gap-1"
                                        >
                                            <div className="flex items-center gap-2">
                                                {word.article && <span className="text-xs font-bold text-blue-600 uppercase">{word.article}</span>}
                                                <span className="font-bold text-gray-900">{word.de}</span>
                                            </div>
                                            <span className="text-sm text-gray-500">{word.ru}</span>
                                            <div className="mt-2 flex items-center gap-2">
                                                <span className="text-[10px] bg-gray-100 px-2 py-0.5 rounded-full font-bold uppercase">{word.level}</span>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Детализация по уровням */}
                        <div className="mt-4">
                            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
                                <BookOpen className="text-blue-600" /> Прогресс по уровням
                            </h2>
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                                {["A1", "A2", "B1", "B2", "C1"].map((lvl) => {
                                    const total = stats.total_words[lvl] || 0;
                                    const userLvlStats = stats.detailed.filter(d => d.level === lvl);
                                    const known = userLvlStats.find(d => d.status === 'known')?.count || 0;
                                    const learning = userLvlStats.find(d => d.status === 'learning')?.count || 0;
                                    const percent = total > 0 ? Math.round(((known) / total) * 100) : 0;

                                    return (
                                        <div key={lvl} className="bg-white p-6 rounded-3xl shadow-sm border border-gray-100">
                                            <div className="flex justify-between items-center mb-4">
                                                <span className="px-3 py-1 bg-gray-900 text-white text-xs font-bold rounded-lg">{lvl}</span>
                                                <span className="text-sm font-bold text-blue-600">{percent}%</span>
                                            </div>

                                            <div className="w-full bg-gray-100 h-2 rounded-full mb-6 overflow-hidden">
                                                <div
                                                    className="bg-blue-600 h-full rounded-full transition-all duration-1000"
                                                    style={{ width: `${percent}%` }}
                                                ></div>
                                            </div>

                                            <div className="flex flex-col gap-2">
                                                <div className="flex justify-between text-sm">
                                                    <span className="text-gray-500">Выучено</span>
                                                    <span className="font-semibold text-gray-900">{known} / {total}</span>
                                                </div>
                                                <div className="flex justify-between text-sm">
                                                    <span className="text-gray-500">Тренируется</span>
                                                    <span className="font-semibold text-orange-600">{learning}</span>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Секция достижений (мокап) */}
                        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 p-10 rounded-3xl text-white shadow-xl flex flex-col md:flex-row items-center justify-between gap-8">
                            <div>
                                <h3 className="text-3xl font-bold mb-2 flex items-center gap-2">
                                    <Award size={32} className="text-yellow-400" /> KlarDeutsch Star
                                </h3>
                                <p className="text-blue-100 text-lg">Вы на правильном пути! Сохраняйте ударный режим.</p>
                            </div>
                            <div className="text-center bg-white/10 backdrop-blur-md px-8 py-6 rounded-2xl border border-white/20">
                                <span className="block text-5xl font-black mb-1">7</span>
                                <span className="text-xs uppercase tracking-widest font-bold text-blue-200">Дней подряд</span>
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
