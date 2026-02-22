"use client";

import React from "react";
import styles from "../styles/Shared.module.css";
import { Volume2, BookOpen, Tag, Star, ArrowRightLeft, Layers } from "lucide-react";
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
    const getArticleColor = (article: string | undefined) => {
        if (!article) return '#3b82f6';
        const lower = article.toLowerCase().trim();
        if (lower === 'der') return '#2563eb';
        if (lower === 'die') return '#ef4444';
        if (lower === 'das') return '#10b981';
        return '#3b82f6';
    };

    // УМНАЯ ФУНКЦИЯ ПОКРАСКИ (Использует и базу, и старые данные)
       const renderWordWithArticle = (wordObj: any) => {
        let text = wordObj.de || "";
        
        // Если ИИ заполнил колонку article в базе
        if (wordObj.article) {
            const articleLower = wordObj.article.toLowerCase().trim();
            let colorClass = "";
            
            if (articleLower === "der") colorClass = "text-blue-500 font-bold";
            else if (articleLower === "die") colorClass = "text-red-500 font-bold";
            else if (articleLower === "das") colorClass = "text-green-500 font-bold";

            if (colorClass) {
                // Если в колонке de тоже есть этот артикль в начале, отрезаем его, чтобы не было "der der Baum"
                if (text.toLowerCase().startsWith(articleLower + " ")) {
                    text = text.slice(articleLower.length + 1).trim();
                }
                return <><span className={colorClass}>{wordObj.article}</span> {text}</>;
            }
        }

        // Если колонки article нет (старые слова), ищем артикль прямо внутри слова de
        if (text.toLowerCase().startsWith("der ")) {
            return <><span className="text-blue-500 font-bold">der</span> {text.slice(4)}</>;
        }
        if (text.toLowerCase().startsWith("die ")) {
            return <><span className="text-red-500 font-bold">die</span> {text.slice(4)}</>;
        }
        if (text.toLowerCase().startsWith("das ")) {
            return <><span className="text-green-500 font-bold">das</span> {text.slice(4)}</>;
        }

        // Если артикля вообще нет (глаголы, прилагательные, или не заполнен)
        return <span className="font-bold">{text}</span>;
    };


    return (
        <div className={styles.card} style={{
            width: '100%',
            marginBottom: '16px',
            position: 'relative',
            textAlign: 'left',
            alignItems: 'flex-start',
            minHeight: 'auto',
            padding: 0,
            overflow: 'hidden',
            border: '1px solid #e2e8f0',
            borderRadius: '16px',
            background: '#ffffff',
            transition: 'box-shadow 0.2s',
        }}
            onMouseOver={(e) => e.currentTarget.style.boxShadow = '0 10px 25px -5px rgba(0, 0, 0, 0.05)'}
            onMouseOut={(e) => e.currentTarget.style.boxShadow = 'none'}
        >
            <div style={{ position: 'absolute', top: '16px', right: '52px', display: 'flex', gap: '8px', zIndex: 5 }}>
                <span style={{
                    fontSize: '0.76rem', padding: '3px 10px', borderRadius: '12px',
                    background: '#e0f2fe', color: '#0369a1', fontWeight: 'bold', border: '1px solid #bae6fd'
                }}>
                    {word.level}
                </span>
            </div>

            <button
                onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    onToggleFavorite?.(word.id);
                }}
                style={{
                    position: 'absolute', top: '10px', right: '10px', background: 'none', border: 'none',
                    cursor: 'pointer', color: word.is_favorite ? '#f59e0b' : '#cbd5e1', padding: '8px',
                    zIndex: 10, transition: 'transform 0.2s'
                }}
                onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.15)'}
                onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
            >
                <Star size={24} fill={word.is_favorite ? '#f59e0b' : 'none'} />
            </button>

            <Link
                href={`/dictionary/${word.id}`}
                style={{ textDecoration: 'none', color: 'inherit', width: '100%', padding: '24px', display: 'block' }}
            >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', marginBottom: '8px', width: '100%' }}>
                    <div style={{ flex: 1 }}>
                        <h3 style={{ margin: 0, fontSize: '1.75rem', color: '#1e293b', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', fontWeight: '800' }}>
                            {/* Здесь мы вызываем умную функцию, передавая весь объект word */}
                            <span>{renderWordWithArticle(word)}</span>
                        </h3>
                    </div>
                </div>

                {(word.plural || word.verb_forms) && (
                    <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
                        {word.plural && (
                            <span style={{ fontSize: '0.85rem', color: '#64748b', background: '#f1f5f9', padding: '2px 8px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                                Pl: <span style={{ fontWeight: '600', color: '#475569' }}>{word.plural}</span>
                            </span>
                        )}
                        {word.verb_forms && (
                            <span style={{ fontSize: '0.85rem', color: '#64748b', background: '#f1f5f9', padding: '2px 8px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                                {word.verb_forms}
                            </span>
                        )}
                    </div>
                )}

                <p style={{ fontSize: '1.25rem', color: '#334155', marginBottom: '20px', fontWeight: '500' }}>
                    {word.ru}
                </p>

                {/* БЛОК ЛИНГВИСТИКИ */}
                {(word.synonyms || word.antonyms || word.collocations) && (
                    <div style={{
                        background: '#f8fafc', padding: '12px 16px', borderRadius: '10px',
                        marginBottom: '20px', border: '1px solid #f1f5f9', fontSize: '0.9rem',
                        display: 'flex', flexDirection: 'column', gap: '8px'
                    }}>
                        {word.synonyms && (
                            <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                                <span style={{ color: '#94a3b8', fontWeight: '600', whiteSpace: 'nowrap' }}>Синонимы:</span>
                                <span style={{ color: '#475569', lineHeight: '1.4' }}>{word.synonyms}</span>
                            </div>
                        )}
                        {word.antonyms && (
                            <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                                <span style={{ color: '#94a3b8', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '4px', whiteSpace: 'nowrap' }}>
                                    <ArrowRightLeft size={12} /> Антонимы:
                                </span>
                                <span style={{ color: '#475569', lineHeight: '1.4' }}>{word.antonyms}</span>
                            </div>
                        )}
                        {word.collocations && (
                            <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                                <span style={{ color: '#94a3b8', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '4px', whiteSpace: 'nowrap' }}>
                                    <Layers size={12} /> Связки:
                                </span>
                                <span style={{ color: '#0369a1', fontWeight: '500', lineHeight: '1.4' }}>{word.collocations}</span>
                            </div>
                        )}
                    </div>
                )}

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#94a3b8', fontSize: '0.85rem', fontWeight: '500' }}>
                        <Tag size={16} color="#cbd5e1" />
                        <span>{word.topic}</span>
                    </div>

                    {word.audio_url && (
                        <button
                            onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                onPlayAudio?.(word.audio_url!);
                            }}
                            style={{
                                background: '#f0f9ff', border: '1px solid #bae6fd', cursor: 'pointer',
                                color: '#0284c7', display: 'flex', alignItems: 'center', gap: '8px',
                                padding: '8px 16px', borderRadius: '24px', transition: 'all 0.2s',
                                fontWeight: '600', fontSize: '0.9rem'
                            }}
                            onMouseOver={(e) => { e.currentTarget.style.background = '#e0f2fe'; e.currentTarget.style.transform = 'translateY(-1px)'; }}
                            onMouseOut={(e) => { e.currentTarget.style.background = '#f0f9ff'; e.currentTarget.style.transform = 'translateY(0)'; }}
                        >
                            <Volume2 size={20} />
                            <span>Прослушать</span>
                        </button>
                    )}
                </div>

                {((word.examples && word.examples.length > 0) || word.example_de) && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', width: '100%' }}>
                        {(word.examples && word.examples.length > 0) ? (
                            word.examples.map((ex, idx) => (
                                <div key={idx} style={{ background: '#f8fafc', padding: '12px 16px', borderRadius: '12px', borderLeft: '4px solid #3b82f6', width: '100%' }}>
                                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginBottom: '4px' }}>
                                        <BookOpen size={16} style={{ marginTop: '2px', color: '#94a3b8', minWidth: '16px' }} />
                                        <p style={{ margin: 0, fontStyle: 'italic', color: '#1e293b', fontSize: '0.95rem', lineHeight: '1.4', fontWeight: '500' }}>{ex.de}</p>
                                    </div>
                                    <p style={{ margin: '4px 0 0 24px', color: '#64748b', fontSize: '0.85rem' }}>{ex.ru}</p>
                                </div>
                            ))
                        ) : (
                            <div style={{ background: '#f8fafc', padding: '12px 16px', borderRadius: '12px', borderLeft: '4px solid #3b82f6', width: '100%' }}>
                                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginBottom: '4px' }}>
                                    <BookOpen size={16} style={{ marginTop: '2px', color: '#94a3b8', minWidth: '16px' }} />
                                    <p style={{ margin: 0, fontStyle: 'italic', color: '#1e293b', fontSize: '0.95rem', lineHeight: '1.4', fontWeight: '500' }}>{word.example_de}</p>
                                </div>
                                {word.example_ru && <p style={{ margin: '4px 0 0 24px', color: '#64748b', fontSize: '0.85rem' }}>{word.example_ru}</p>}
                            </div>
                        )}
                    </div>
                )}
            </Link>
        </div>
    );
}
