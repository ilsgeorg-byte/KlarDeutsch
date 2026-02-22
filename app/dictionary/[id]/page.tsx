"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Loader2, Volume2, BookOpen, Tag, Star, ArrowRightLeft, Layers } from "lucide-react";
import styles from "../../styles/Shared.module.css";


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

export default function WordDetailPage() {
    const { id } = useParams();
    const router = useRouter();
    const [word, setWord] = useState<Word | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        const fetchWord = async () => {
            try {
                const token = localStorage.getItem("token");
                const headers: Record<string, string> = {};
                if (token) headers['Authorization'] = `Bearer ${token}`;

                const res = await fetch(`/api/words/${id}`, { headers });
                const data = await res.json();

                if (!res.ok) throw new Error(data.error || "Ошибка загрузки слова");
                setWord(data);
            } catch (err: any) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        if (id) fetchWord();
    }, [id]);

    const playAudio = (url: string) => {
        const audio = new Audio(url);
        audio.play().catch(e => console.error("Audio play error:", e));
    };

    const toggleFavorite = async () => {
        if (!word) return;
        try {
            const token = localStorage.getItem('token');
            if (!token) return alert("Пожалуйста, войдите в систему");

            const res = await fetch(`/api/words/${word.id}/favorite`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (res.ok) {
                setWord({ ...word, is_favorite: !word.is_favorite });
            }
        } catch (err) {
            console.error("Favorite error:", err);
        }
    };

        const renderWordWithArticle = (wordObj: any) => {
        let text = wordObj.de || "";
        
        if (wordObj.article) {
            const articleLower = wordObj.article.toLowerCase().trim();
            let colorClass = "";
            
            if (articleLower === "der") colorClass = "text-blue-500 font-bold";
            else if (articleLower === "die") colorClass = "text-red-500 font-bold";
            else if (articleLower === "das") colorClass = "text-green-500 font-bold";

            if (colorClass) {
                if (text.toLowerCase().startsWith(articleLower + " ")) {
                    text = text.slice(articleLower.length + 1).trim();
                }
                return <><span className={colorClass}>{wordObj.article}</span> {text}</>;
            }
        }

        if (text.toLowerCase().startsWith("der ")) {
            return <><span className="text-blue-500 font-bold">der</span> {text.slice(4)}</>;
        }
        if (text.toLowerCase().startsWith("die ")) {
            return <><span className="text-red-500 font-bold">die</span> {text.slice(4)}</>;
        }
        if (text.toLowerCase().startsWith("das ")) {
            return <><span className="text-green-500 font-bold">das</span> {text.slice(4)}</>;
        }

        return <span className="font-bold">{text}</span>;
    };


    // Определение цвета артикля
    const getArticleColor = (article: string | undefined) => {
        if (!article) return '#3b82f6';
        const lower = article.toLowerCase().trim();
        if (lower === 'der') return '#2563eb'; // синий
        if (lower === 'die') return '#ef4444'; // красный
        if (lower === 'das') return '#10b981'; // зеленый
        return '#3b82f6';
    };

    if (loading) {
        return (
            <div className={styles.pageWrapper}>

                <div className="flex-1 flex flex-col items-center justify-center p-8">
                    <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-4" />
                    <p className="text-slate-500 font-medium">Загружаем слово...</p>
                </div>
            </div>
        );
    }

    if (error || !word) {
        return (
            <div className={styles.pageWrapper}>

                <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
                    <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center text-red-500 mb-4">
                        <span className="text-2xl">😕</span>
                    </div>
                    <h2 className="text-xl font-bold text-slate-800 mb-2">Ой, что-то пошло не так</h2>
                    <p className="text-slate-500 mb-6">{error || "Слово не найдено"}</p>
                    <button onClick={() => router.back()} className="px-6 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors">
                        Вернуться назад
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className={`${styles.pageWrapper} bg-slate-50 min-h-screen font-sans flex flex-col`}>


            <main className="flex-1 flex flex-col items-center px-4 w-full pt-8 pb-12 max-w-3xl mx-auto">

                {/* Кнопки Назад и В избранное */}
                <div className="flex justify-between items-center w-full mb-6">
                    <button
                        onClick={() => router.back()}
                        className="flex items-center gap-2 text-slate-500 hover:text-blue-600 font-medium transition-colors"
                    >
                        <ArrowLeft size={20} />
                        Назад
                    </button>

                    <button
                        onClick={toggleFavorite}
                        className={`flex items-center gap-2 px-4 py-2 rounded-xl font-semibold transition-all shadow-sm border ${word.is_favorite ? 'bg-amber-50 text-amber-600 border-amber-200' : 'bg-white text-slate-500 border-slate-200 hover:bg-slate-50'}`}
                    >
                        <Star size={18} fill={word.is_favorite ? '#f59e0b' : 'none'} />
                        {word.is_favorite ? 'В избранном' : 'Добавить в избранное'}
                    </button>
                </div>

                {/* Основная карточка */}
                <div className="w-full bg-white rounded-3xl shadow-xl border border-slate-100 p-8 md:p-10 relative">

                    {/* Верхняя панель (Уровень и Тема) */}
                    <div className="flex justify-between items-center mb-8">
                        <span className="bg-blue-50 text-blue-600 px-4 py-1.5 rounded-full text-sm font-bold tracking-wide border border-blue-100">
                            Уровень {word.level}
                        </span>
                        <div className="flex items-center gap-1.5 text-slate-400 font-medium">
                            <Tag size={16} />
                            {word.topic}
                        </div>
                    </div>

                    {/* Слово и перевод */}
                    <div className="mb-10">
                        <h1 className="text-4xl md:text-5xl font-extrabold text-slate-800 mb-4 flex flex-wrap items-center gap-3">
                            {word.article && (
                                <span style={{ color: getArticleColor(word.article) }} className="mr-2 opacity-95">
                                    {renderWordWithArticle(word)}
                                </span>
                            )}
                            
                        </h1>

                        {/* Множественное число / Формы глагола */}
                        {(word.plural || word.verb_forms) && (
                            <div className="flex gap-3 mb-6 flex-wrap">
                                {word.plural && (
                                    <span className="bg-slate-100 text-slate-600 px-3 py-1.5 rounded-lg text-sm font-medium border border-slate-200">
                                        Pl: <span className="text-slate-800 font-bold">{word.plural}</span>
                                    </span>
                                )}
                                {word.verb_forms && (
                                    <span className="bg-slate-100 text-slate-600 px-3 py-1.5 rounded-lg text-sm font-medium border border-slate-200">
                                        {word.verb_forms}
                                    </span>
                                )}
                            </div>
                        )}

                        <p className="text-2xl md:text-3xl font-medium text-slate-600 pb-8 border-b border-slate-100">
                            {word.ru}
                        </p>
                    </div>

                    {/* Лингвистический блок (Синонимы, Антонимы, Связки) */}
                    {(word.synonyms || word.antonyms || word.collocations) && (
                        <div className="w-full bg-slate-50 rounded-2xl p-6 mb-8 border border-slate-100">
                            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                                <Layers size={16} /> Лингвистические данные
                            </h3>
                            <div className="space-y-3">
                                {word.synonyms && (
                                    <div className="flex flex-col sm:flex-row sm:items-baseline border-b border-slate-200/50 pb-3">
                                        <span className="w-32 text-slate-500 font-medium">Синонимы: </span>
                                        <span className="text-slate-800 flex-1">{word.synonyms}</span>
                                    </div>
                                )}
                                {word.antonyms && (
                                    <div className="flex flex-col sm:flex-row sm:items-baseline border-b border-slate-200/50 pb-3">
                                        <span className="w-32 text-slate-500 font-medium flex items-center gap-1.5"><ArrowRightLeft size={14} /> Антонимы:</span>
                                        <span className="text-slate-800 flex-1">{word.antonyms}</span>
                                    </div>
                                )}
                                {word.collocations && (
                                    <div className="flex flex-col sm:flex-row sm:items-baseline sm:gap-2">
                                        <span className="w-32 text-slate-500 font-medium">Словосочетания: </span>
                                        <span className="text-blue-700 font-medium flex-1">{word.collocations}</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Примеры */}
                    <div className="mb-8">
                        <h3 className="text-lg font-bold text-slate-700 mb-4 flex items-center gap-2">
                            <BookOpen size={20} className="text-blue-500" />
                            Примеры использования
                        </h3>

                        <div className="space-y-3">
                            {(word.examples && word.examples.length > 0) ? (
                                word.examples.map((ex, idx) => (
                                    <div key={idx} className="bg-blue-50/50 p-5 rounded-2xl border-l-4 border-blue-500">
                                        <p className="text-lg font-medium text-slate-800 mb-1 italic">"{ex.de}"</p>
                                        <p className="text-slate-500">{ex.ru}</p>
                                    </div>
                                ))
                            ) : (word.example_de) ? (
                                <div className="bg-blue-50/50 p-5 rounded-2xl border-l-4 border-blue-500">
                                    <p className="text-lg font-medium text-slate-800 mb-1 italic">"{word.example_de}"</p>
                                    <p className="text-slate-500">{word.example_ru}</p>
                                </div>
                            ) : (
                                <p className="text-slate-400 italic bg-slate-50 p-4 rounded-xl text-center">Примеров пока нет</p>
                            )}
                        </div>
                    </div>

                    {/* Кнопка озвучки */}
                    {word.audio_url && (
                        <div className="mt-8 flex justify-center">
                            <button
                                onClick={() => playAudio(word.audio_url!)}
                                className="flex items-center justify-center gap-3 w-full sm:w-auto px-8 py-4 bg-blue-50 hover:bg-blue-100 text-blue-600 rounded-2xl font-bold transition-colors border border-blue-200"
                            >
                                <Volume2 size={24} />
                                Прослушать произношение
                            </button>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
