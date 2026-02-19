"use client";

import React from "react";
import styles from "../styles/Shared.module.css";
import { Volume2, BookOpen, Tag, Star } from "lucide-react";

import Link from "next/link";

interface WordCardProps {
    word: {
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
    };
    onPlayAudio?: (url: string) => void;
    onToggleFavorite?: (wordId: number) => void;
}

export default function WordCard({ word, onPlayAudio, onToggleFavorite }: WordCardProps) {
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
            border: '1px solid #e2e8f0'
        }}>
            <div style={{
                position: 'absolute',
                top: '12px',
                right: '48px',
                display: 'flex',
                gap: '8px',
                zIndex: 5
            }}>
                <span style={{
                    fontSize: '0.75rem',
                    padding: '2px 8px',
                    borderRadius: '12px',
                    background: '#e0f2fe',
                    color: '#0369a1',
                    fontWeight: 'bold'
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
                    top: '8px',
                    right: '8px',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    color: word.is_favorite ? '#f59e0b' : '#94a3b8',
                    padding: '8px',
                    zIndex: 10,
                    transition: 'transform 0.2s'
                }}
                className="fav-btn"
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
                        <h3 style={{ margin: 0, fontSize: '1.5rem', color: '#1e293b', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                            {word.article && <span style={{ color: '#3b82f6', fontSize: '1.1rem', fontWeight: 'bold' }}>{word.article}</span>}
                            <span>{word.de}</span>
                        </h3>
                    </div>
                </div>

                {word.verb_forms && (
                    <p style={{ margin: '0 0 12px 0', fontSize: '0.95rem', color: '#64748b', fontStyle: 'italic' }}>
                        ({word.verb_forms})
                    </p>
                )}

                <p style={{ fontSize: '1.2rem', color: '#1e293b', marginBottom: '16px', fontWeight: '500' }}>
                    {word.ru}
                </p>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#94a3b8', fontSize: '0.85rem' }}>
                        <Tag size={14} />
                        <span>{word.topic}</span>
                    </div>

                    {/* Prominent Audio Button inside the card but not blocking navigation */}
                    {word.audio_url && (
                        <button
                            onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                onPlayAudio?.(word.audio_url!);
                            }}
                            style={{
                                background: '#f1f5f9',
                                border: 'none',
                                cursor: 'pointer',
                                color: '#3498db',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px',
                                padding: '8px 16px',
                                borderRadius: '20px',
                                transition: 'all 0.2s',
                                fontWeight: '600',
                                fontSize: '0.9rem'
                            }}
                            onMouseOver={(e) => {
                                e.currentTarget.style.background = '#e2e8f0';
                                e.currentTarget.style.transform = 'scale(1.05)';
                            }}
                            onMouseOut={(e) => {
                                e.currentTarget.style.background = '#f1f5f9';
                                e.currentTarget.style.transform = 'scale(1)';
                            }}
                        >
                            <Volume2 size={20} />
                            <span>Прослушать</span>
                        </button>
                    )}
                </div>

                {(word.example_de || word.example_ru) && (
                    <div style={{
                        background: '#f8fafc',
                        padding: '16px',
                        borderRadius: '12px',
                        borderLeft: '4px solid #3498db',
                        width: '100%'
                    }}>
                        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginBottom: '6px' }}>
                            <BookOpen size={18} style={{ marginTop: '2px', color: '#64748b' }} />
                            <p style={{ margin: 0, fontStyle: 'italic', color: '#334155', fontSize: '1rem', lineHeight: '1.4' }}>{word.example_de}</p>
                        </div>
                        {word.example_ru && (
                            <p style={{ margin: '6px 0 0 26px', color: '#64748b', fontSize: '0.9rem' }}>{word.example_ru}</p>
                        )}
                    </div>
                )}
            </Link>
        </div>
    );
}
