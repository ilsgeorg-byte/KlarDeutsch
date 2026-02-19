"use client";

import React from "react";
import styles from "../styles/Shared.module.css";
import { Volume2, BookOpen, Tag } from "lucide-react";

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
    };
    onPlayAudio?: (url: string) => void;
}

export default function WordCard({ word, onPlayAudio }: WordCardProps) {
    return (
        <div className={styles.card} style={{
            width: '100%',
            marginBottom: '16px',
            position: 'relative',
            textAlign: 'left',
            alignItems: 'flex-start',
            minHeight: 'auto',
            padding: 0,
            overflow: 'hidden'
        }}>
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

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '4px', width: '100%' }}>
                    <div style={{ flex: 1 }}>
                        <h3 style={{ margin: 0, fontSize: '1.5rem', color: '#1e293b', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            {word.article && <span style={{ color: '#3b82f6', fontSize: '1rem', fontWeight: 'bold' }}>{word.article}</span>}
                            <span>{word.de}</span>
                        </h3>
                    </div>
                </div>

                {word.verb_forms && (
                    <p style={{ margin: '0 0 8px 0', fontSize: '0.9rem', color: '#64748b', fontStyle: 'italic' }}>
                        ({word.verb_forms})
                    </p>
                )}

                <p style={{ fontSize: '1.1rem', color: '#475569', marginBottom: '12px', fontWeight: '500' }}>
                    {word.ru}
                </p>

                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '12px', color: '#94a3b8', fontSize: '0.85rem' }}>
                    <Tag size={14} />
                    <span>{word.topic}</span>
                </div>

                {(word.example_de || word.example_ru) && (
                    <div style={{
                        background: '#f8fafc',
                        padding: '12px',
                        borderRadius: '8px',
                        borderLeft: '4px solid #3498db',
                        width: '100%'
                    }}>
                        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginBottom: '4px' }}>
                            <BookOpen size={16} style={{ marginTop: '2px', color: '#64748b' }} />
                            <p style={{ margin: 0, fontStyle: 'italic', color: '#334155', fontSize: '0.95rem' }}>{word.example_de}</p>
                        </div>
                        {word.example_ru && (
                            <p style={{ margin: '4px 0 0 24px', color: '#64748b', fontSize: '0.85rem' }}>{word.example_ru}</p>
                        )}
                    </div>
                )}
            </Link>

            {word.audio_url && (
                <button
                    onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        onPlayAudio?.(word.audio_url!);
                    }}
                    style={{
                        position: 'absolute',
                        right: '12px',
                        top: '40px',
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        color: '#3498db',
                        display: 'flex',
                        alignItems: 'center',
                        padding: '8px',
                        borderRadius: '50%',
                        transition: 'background 0.2s',
                        zIndex: 10
                    }}
                >
                    <Volume2 size={20} />
                </button>
            )}
        </div>
    );
}
