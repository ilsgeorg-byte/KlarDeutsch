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
    // Функция для определения цвета артикля
    const getArticleColor = (article: string | undefined) => {
        if (!article) return '#3b82f6'; // по умолчанию синий
        const lower = article.toLowerCase().trim();
        if (lower === 'der') return '#2563eb'; // синий
        if (lower === 'die') return '#ef4444'; // красный
        if (lower === 'das') return '#10b981'; // зеленый
        return '#3b82f6';
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
            onMouseOver={(e) => e.currentTarget.style.boxShadow = '0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01)'}
            onMouseOut={(e) => e.currentTarget.style.boxShadow = 'none'}
        >
            <div style={{
                position: 'absolute',
                top: '16px',
                right: '52px',
                display: 'flex',
                gap: '8px',
                zIndex: 5
            }}>
                <span style={{
                    fontSize: '0.76rem',
                    padding: '3px 10px',
                    borderRadius: '12px',
                    background: '#e0f2fe',
                    color: '#0369a1',
                    fontWeight: 'bold',
                    border: '1px solid #bae6fd'
                }}>
                    {word.level}
                </span>
            </div>

            {/* Favorite Star Button */}
            <button
                onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    onToggleFavorite?.(word.id);
                }}
                style={{
                    position: 'absolute',
                    top: '10px',
                    right: '10px',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    color: word.is_favorite ? '#f59e0b' : '#cbd5e1',
                    padding: '8px',
                    zIndex: 10,
                    transition: 'all 0.2s transform cubic-bezier(0.175, 0.885, 0.32, 1.275)'
                }}
                onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.15)'}
                onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
            >
                <Star size={24} fill={word.is_favorite ? '#f59e0b' : 'none'} />
            </button>

            <Link
                href={`/dictionary/${word.id}`}
                style={{
                    textDecoration: 'none',
                    color: 'inherit',
                    width: '100%',
                    padding: '24px',
                    display: 'block'
                }}
            >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', marginBottom: '8px', width: '100%' }}>
                    <div style={{ flex: 1 }}>
                        <h3 style={{ margin: 0, fontSize: '1.75rem', color: '#1e293b', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', fontWeight: '800' }}>
                            {word.article && <span style={{ color: getArticleColor(word.article), fontSize: '1.4rem' }}>{word.article}</span>}
                            <span>{word.de}</span>
                        </h3>
                    </div>
                </div>

                {/* Лингвистические данные: Множественное число или Формы глагола */}
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

                {/* Блок Синонимов, Антонимов и Словосочетаний */}
                {/* Блок Синонимов, Антонимов и Словосочетаний */}
                {(word.synonyms || word.antonyms || word.collocations) && (
                    <div style={{ background: '#f8fafc', padding: '12px 16px', borderRadius: '10px', marginBottom: '20px', border: '1px solid #f1f5f9', fontSize: '0.9rem' }}>
                        {word.synonyms && (
                            <div style={{ display: 'flex', gap: '8px', marginBottom: '6px', flexWrap: 'wrap' }}>
                                <span style={{ color: '#94a3b8', fontWeight: '600', display: 'flex', alignItems: 'center', minWidth: '95px' }}>Синонимы:</span>
                                <span style={{ color: '#475569', flex: 1 }}>{word.synonyms}</span>
                            </div>
                        )}
                        {word.antonyms && (
                            <div style={{ display: 'flex', gap: '8px', marginBottom: '6px', flexWrap: 'wrap' }}>
                                <span style={{ color: '#94a3b8', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '4px', minWidth: '95px' }}><ArrowRightLeft size={12} /> Антонимы:</span>
                                <span style={{ color: '#475569', flex: 1 }}>{word.antonyms}</span>
                            </div>
                        )}
                        {word.collocations && (
                            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                                <span style={{ color: '#94a3b8', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '4px', minWidth: '95px' }}><Layers size={12} /> Связки:</span>
                                <span style={{ color: '#0369a1', fontWeight: '500', flex: 1 }}>{word.collocations}</span>
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
                                background: '#f0f9ff',
                                border: '1px solid #bae6fd',
                                cursor: 'pointer',
                                color: '#0284c7',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px',
                                padding: '8px 16px',
                                borderRadius: '24px',
                                transition: 'all 0.2s',
                                fontWeight: '600',
                                fontSize: '0.9rem',
                                boxShadow: '0 2px 4px rgba(2, 132, 199, 0.05)'
                            }}
                            onMouseOver={(e) => {
                                e.currentTarget.style.background = '#e0f2fe';
                                e.currentTarget.style.transform = 'translateY(-1px)';
                                e.currentTarget.style.boxShadow = '0 4px 6px rgba(2, 132, 199, 0.1)';
                            }}
                            onMouseOut={(e) => {
                                e.currentTarget.style.background = '#f0f9ff';
                                e.currentTarget.style.transform = 'translateY(0)';
                                e.currentTarget.style.boxShadow = '0 2px 4px rgba(2, 132, 199, 0.05)';
                            }}
                        >
                            <Volume2 size={20} />
                            <span>Прослушать</span>
                        </button>
                    )}
                </div>

                {/* Примеры (поддержка массива из 3 штук или старого одиночного формата) */}
                {((word.examples && word.examples.length > 0) || word.example_de) && (
                    <div style={{ display: 'flex', flexDirection: 'col' as any, gap: '8px', width: '100%' }}>

                        {(word.examples && word.examples.length > 0) ? (
                            // Рендер массива примеров
                            word.examples.map((ex, idx) => (
                                <div key={idx} style={{
                                    background: '#f8fafc',
                                    padding: '12px 16px',
                                    borderRadius: '12px',
                                    borderLeft: '4px solid #3b82f6',
                                    width: '100%'
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginBottom: '4px' }}>
                                        <BookOpen size={16} style={{ marginTop: '2px', color: '#94a3b8', minWidth: '16px' }} />
                                        <p style={{ margin: 0, fontStyle: 'italic', color: '#1e293b', fontSize: '0.95rem', lineHeight: '1.4', fontWeight: '500' }}>
                                            {ex.de}
                                        </p>
                                    </div>
                                    <p style={{ margin: '4px 0 0 24px', color: '#64748b', fontSize: '0.85rem' }}>{ex.ru}</p>
                                </div>
                            ))
                        ) : (
                            // Рендер старого одиночного примера
                            <div style={{
                                background: '#f8fafc',
                                padding: '12px 16px',
                                borderRadius: '12px',
                                borderLeft: '4px solid #3b82f6',
                                width: '100%'
                            }}>
                                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginBottom: '4px' }}>
                                    <BookOpen size={16} style={{ marginTop: '2px', color: '#94a3b8', minWidth: '16px' }} />
                                    <p style={{ margin: 0, fontStyle: 'italic', color: '#1e293b', fontSize: '0.95rem', lineHeight: '1.4', fontWeight: '500' }}>
                                        {word.example_de}
                                    </p>
                                </div>
                                {word.example_ru && (
                                    <p style={{ margin: '4px 0 0 24px', color: '#64748b', fontSize: '0.85rem' }}>{word.example_ru}</p>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </Link>
        </div>
    );
}
