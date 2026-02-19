"use client";

import React from "react";
import styles from "../styles/Shared.module.css";
import { Volume2, BookOpen, Tag } from "lucide-react";

interface WordCardProps {
    word: {
        id: number;
        de: string;
        ru: string;
        article?: string;
        level: string;
        topic: string;
        example_de?: string;
        example_ru?: string;
        audio_url?: string;
    };
    onPlayAudio?: (url: string) => void;
}

export default function WordCard({ word, onPlayAudio }: WordCardProps) {
    return (
        <div className={styles.card} style={{ width: '100%', marginBottom: '16px', position: 'relative' }}>
            <div style={{ position: 'absolute', top: '12px', right: '12px', display: 'flex', gap: '8px' }}>
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

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                <h3 style={{ margin: 0, fontSize: '1.5rem', color: '#1e293b' }}>
                    {word.article && <span style={{ color: '#64748b', fontSize: '1rem', marginRight: '4px' }}>{word.article}</span>}
                    {word.de}
                </h3>
                {word.audio_url && (
                    <button
                        onClick={() => onPlayAudio?.(word.audio_url!)}
                        style={{
                            background: 'none',
                            border: 'none',
                            cursor: 'pointer',
                            color: '#3498db',
                            display: 'flex',
                            alignItems: 'center'
                        }}
                    >
                        <Volume2 size={20} />
                    </button>
                )}
            </div>

            <p style={{ fontSize: '1.1rem', color: '#475569', marginBottom: '16px', fontWeight: '500' }}>
                {word.ru}
            </p>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '16px', color: '#64748b', fontSize: '0.85rem' }}>
                <Tag size={14} />
                <span>{word.topic}</span>
            </div>

            {(word.example_de || word.example_ru) && (
                <div style={{
                    background: '#f8fafc',
                    padding: '12px',
                    borderRadius: '8px',
                    borderLeft: '4px solid #3498db'
                }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginBottom: '4px' }}>
                        <BookOpen size={16} style={{ marginTop: '2px', color: '#64748b' }} />
                        <p style={{ margin: 0, fontStyle: 'italic', color: '#334155' }}>{word.example_de}</p>
                    </div>
                    {word.example_ru && (
                        <p style={{ margin: '4px 0 0 24px', color: '#64748b', fontSize: '0.9rem' }}>{word.example_ru}</p>
                    )}
                </div>
            )}
        </div>
    );
}
