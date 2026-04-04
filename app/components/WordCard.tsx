"use client";

import React from "react";
import { Volume2, BookOpen, Tag, Star, ArrowRightLeft, Layers, ExternalLink } from "lucide-react";
import Link from "next/link";

interface WordCardProps {
    word: {
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
    };
    onPlayAudio?: (url: string) => void;
    onToggleFavorite?: (wordId: number) => void;
}

export default function WordCard({ word, onPlayAudio, onToggleFavorite }: WordCardProps) {
    const renderWordWithArticle = (wordObj: any) => {
        let text = wordObj.de || "";
        
        if (wordObj.article) {
            const articleLower = wordObj.article.toLowerCase().trim();
            let colorClass = "";
            
            if (articleLower === "der") colorClass = "article-der";
            else if (articleLower === "die") colorClass = "article-die";
            else if (articleLower === "das") colorClass = "article-das";

            if (colorClass) {
                if (text.toLowerCase().startsWith(articleLower + " ")) {
                    text = text.slice(articleLower.length + 1).trim();
                }
                return <><span className={colorClass}>{wordObj.article}</span> {text}</>;
            }
        }

        // Fallback для старых слов
        const lowerText = text.toLowerCase();
        if (lowerText.startsWith("der ")) return <><span className="article-der">der</span> {text.slice(4)}</>;
        if (lowerText.startsWith("die ")) return <><span className="article-die">die</span> {text.slice(4)}</>;
        if (lowerText.startsWith("das ")) return <><span className="article-das">das</span> {text.slice(4)}</>;

        return <span className="font-bold">{text}</span>;
    };

    return (
        <div className="relative group overflow-hidden rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800 shadow-sm hover:shadow-2xl hover:shadow-indigo-500/10 transition-all duration-300 animate-fade-in p-7 md:p-8">
            
            {/* Декоративный фон для уровня */}
            <div className="absolute -top-6 -right-6 w-24 h-24 bg-indigo-500/5 rounded-full blur-2xl group-hover:bg-indigo-500/10 transition-colors" />

            {/* Заголовок и уровень */}
            <div className="flex justify-between items-start mb-4 relative z-10">
                <div className="flex items-center gap-2">
                    <span className="px-3 py-1 text-[11px] font-black uppercase tracking-widest rounded-full bg-indigo-50 text-indigo-600 border border-indigo-100 dark:bg-indigo-900/30 dark:text-indigo-400 dark:border-indigo-800">
                        {word.level}
                    </span>
                </div>
                
                <button
                    onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        onToggleFavorite?.(word.id);
                    }}
                    className={`p-2 rounded-full transition-all duration-200 ${word.is_favorite ? 'text-amber-500 bg-amber-50 dark:bg-amber-900/20' : 'text-slate-300 hover:text-amber-400 hover:bg-slate-50 dark:hover:bg-slate-800'}`}
                >
                    <Star size={22} fill={word.is_favorite ? "currentColor" : "none"} />
                </button>
            </div>

            {/* Основная часть ссылки */}
            <Link href={`/dictionary/${word.id}`} className="block group/link">
                <h3 className="text-2xl md:text-3xl font-extrabold text-slate-800 dark:text-white mb-2 group-hover/link:text-indigo-600 transition-colors tracking-tight">
                    {renderWordWithArticle(word)}
                </h3>

                <p className="text-xl text-slate-500 dark:text-slate-400 font-medium mb-6">
                    {word.ru}
                </p>

                {/* Грамматические формы */}
                {(word.plural || word.verb_forms) && (
                    <div className="flex flex-wrap gap-2 mb-6">
                        {word.plural && (
                            <span className="text-xs px-2.5 py-1 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-700 text-slate-500">
                                {word.plural === '—' ? (
                                    <span className="text-slate-400 dark:text-slate-500">Pl: <span className="font-medium">нет мн.ч.</span></span>
                                ) : (
                                    <>Pl: <span className="font-bold text-slate-700 dark:text-slate-300">{word.plural}</span></>
                                )}
                            </span>
                        )}
                        {word.verb_forms && (
                            <span className="text-xs px-2.5 py-1 rounded-lg bg-indigo-50/50 dark:bg-indigo-900/20 border border-indigo-100/50 dark:border-indigo-800 text-indigo-600 dark:text-indigo-400 italic">
                                {word.verb_forms}
                            </span>
                        )}
                    </div>
                )}

                {/* Лингвистический блок */}
                {(word.synonyms || word.antonyms) && (
                    <div className="grid grid-cols-1 gap-3 p-4 bg-slate-50/50 dark:bg-slate-800/40 rounded-2xl border border-slate-100/50 dark:border-slate-800/50 mb-6 text-[13px]">
                        {word.synonyms && (
                            <div className="flex gap-3">
                                <span className="text-slate-400 font-bold shrink-0">SYN:</span>
                                <span className="text-slate-600 dark:text-slate-300">{word.synonyms}</span>
                            </div>
                        )}
                        {word.antonyms && (
                            <div className="flex gap-3">
                                <span className="text-slate-400 font-bold shrink-0">ANT:</span>
                                <span className="text-slate-600 dark:text-slate-300">{word.antonyms}</span>
                            </div>
                        )}
                    </div>
                )}

                {/* Тема и Аудио */}
                <div className="flex items-center justify-between mt-auto pt-4 border-t border-slate-100 dark:border-slate-800/50">
                    <Link 
                        href={`/topics/${encodeURIComponent(word.topic)}`}
                        onClick={(e) => e.stopPropagation()}
                        className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-indigo-500 hover:text-white dark:hover:bg-indigo-600 transition-all duration-200"
                    >
                        <Tag size={14} />
                        {word.topic}
                    </Link>

                    {word.audio_url && (
                        <button
                            onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                onPlayAudio?.(word.audio_url!);
                            }}
                            className="flex items-center gap-2 p-2 px-4 rounded-full bg-indigo-600 text-white shadow-lg shadow-indigo-200 dark:shadow-none hover:bg-indigo-700 hover:-translate-y-0.5 transition-all duration-200 active:scale-95"
                        >
                            <Volume2 size={18} />
                            <span className="text-xs font-bold hidden sm:inline">Play</span>
                        </button>
                    )}
                </div>

                {/* Пример (один самый яркий) */}
                {((word.examples && word.examples.length > 0) || word.example_de) && (
                    <div className="mt-6">
                        <div className="p-4 rounded-2xl bg-indigo-50/30 dark:bg-indigo-900/10 border-l-4 border-indigo-500">
                            {word.examples && word.examples.length > 0 ? (
                                <>
                                    <p className="text-sm font-semibold italic text-slate-700 dark:text-slate-200 leading-relaxed mb-1">
                                        "{word.examples[0].de}"
                                    </p>
                                    <p className="text-xs text-slate-500 dark:text-slate-400">
                                        {word.examples[0].ru}
                                    </p>
                                </>
                            ) : (
                                <>
                                    <p className="text-sm font-semibold italic text-slate-700 dark:text-slate-200 leading-relaxed mb-1">
                                        "{word.example_de}"
                                    </p>
                                    {word.example_ru && (
                                        <p className="text-xs text-slate-500 dark:text-slate-400">{word.example_ru}</p>
                                    )}
                                </>
                            )}
                        </div>
                    </div>
                )}
            </Link>
        </div>
    );
}
