"use client";

import React, { useState } from "react";
import styles from "../styles/Shared.module.css";
import { X, Plus, Info } from "lucide-react";

interface AddWordModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: (wordId: number) => void;
}

export default function AddWordModal({ isOpen, onClose, onSuccess }: AddWordModalProps) {
    const [formData, setFormData] = useState({
        de: "",
        ru: "",
        article: "",
        level: "A1",
        topic: "Личные слова",
        verb_forms: "",
        example_de: "",
        example_ru: ""
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            const token = localStorage.getItem("token");
            if (!token) throw new Error("Вы не авторизованы");

            const response = await fetch("/api/words/custom", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok) {
                onSuccess(data.word_id);
                setFormData({
                    de: "",
                    ru: "",
                    article: "",
                    level: "A1",
                    topic: "Личные слова",
                    verb_forms: "",
                    example_de: "",
                    example_ru: ""
                });
                onClose();
            } else {
                setError(data.error || "Ошибка при добавлении слова");
            }
        } catch (err: any) {
            setError(err.message || "Ошибка соединения");
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            backdropFilter: 'blur(4px)'
        }} onClick={onClose}>
            <div style={{
                backgroundColor: 'white',
                borderRadius: '24px',
                width: '100%',
                maxWidth: '600px',
                padding: '32px',
                position: 'relative',
                maxHeight: '90vh',
                overflowY: 'auto',
                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
            }} onClick={e => e.stopPropagation()}>
                <button onClick={onClose} style={{
                    position: 'absolute',
                    top: '20px',
                    right: '20px',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    color: '#94a3b8'
                }}>
                    <X size={24} />
                </button>

                <h2 style={{ fontSize: '1.75rem', fontWeight: 'bold', marginBottom: '8px', color: '#1e293b' }}>Добавить своё слово</h2>
                <p style={{ color: '#64748b', marginBottom: '24px' }}>Добавьте новое слово в свой словарь для изучения.</p>

                {error && (
                    <div style={{
                        padding: '12px 16px',
                        backgroundColor: '#fef2f2',
                        color: '#ef4444',
                        borderRadius: '12px',
                        marginBottom: '20px',
                        fontSize: '0.9rem',
                        border: '1px solid #fee2e2'
                    }}>
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                        <div>
                            <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '600', marginBottom: '6px', color: '#475569' }}>Артикль (необяз.)</label>
                            <select name="article" value={formData.article} onChange={handleChange} style={{
                                width: '100%', padding: '12px', borderRadius: '12px', border: '1px solid #e2e8f0', fontSize: '1rem'
                            }}>
                                <option value="">Без артикля</option>
                                <option value="der">der (m)</option>
                                <option value="die">die (f)</option>
                                <option value="das">das (n)</option>
                            </select>
                        </div>
                        <div>
                            <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '600', marginBottom: '6px', color: '#475569' }}>Уровень</label>
                            <select name="level" value={formData.level} onChange={handleChange} style={{
                                width: '100%', padding: '12px', borderRadius: '12px', border: '1px solid #e2e8f0', fontSize: '1rem'
                            }}>
                                <option value="A1">A1</option>
                                <option value="A2">A2</option>
                                <option value="B1">B1</option>
                                <option value="B2">B2</option>
                                <option value="C1">C1</option>
                            </select>
                        </div>
                    </div>

                    <div style={{ marginBottom: '16px' }}>
                        <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '600', marginBottom: '6px', color: '#475569' }}>Слово на немецком</label>
                        <input required type="text" name="de" value={formData.de} onChange={handleChange} placeholder="напр. Hund" style={{
                            width: '100%', padding: '12px', borderRadius: '12px', border: '1px solid #e2e8f0', fontSize: '1rem'
                        }} />
                    </div>

                    <div style={{ marginBottom: '16px' }}>
                        <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '600', marginBottom: '6px', color: '#475569' }}>Перевод на русский</label>
                        <input required type="text" name="ru" value={formData.ru} onChange={handleChange} placeholder="напр. собака" style={{
                            width: '100%', padding: '12px', borderRadius: '12px', border: '1px solid #e2e8f0', fontSize: '1rem'
                        }} />
                    </div>

                    <div style={{ marginBottom: '16px' }}>
                        <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '600', marginBottom: '6px', color: '#475569' }}>
                            Формы глагола <span style={{ fontWeight: 'normal', color: '#94a3b8' }}>(для глаголов)</span>
                        </label>
                        <input type="text" name="verb_forms" value={formData.verb_forms} onChange={handleChange} placeholder="напр. macht, machte, hat gemacht" style={{
                            width: '100%', padding: '12px', borderRadius: '12px', border: '1px solid #e2e8f0', fontSize: '1rem'
                        }} />
                    </div>

                    <div style={{ marginBottom: '16px' }}>
                        <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '600', marginBottom: '6px', color: '#475569' }}>Пример (нем.)</label>
                        <textarea name="example_de" value={formData.example_de} onChange={handleChange} rows={2} style={{
                            width: '100%', padding: '12px', borderRadius: '12px', border: '1px solid #e2e8f0', fontSize: '1rem', resize: 'none'
                        }} placeholder="напр. Der Hund spielt im Garten." />
                    </div>

                    <div style={{ marginBottom: '24px' }}>
                        <label style={{ display: 'block', fontSize: '0.9rem', fontWeight: '600', marginBottom: '6px', color: '#475569' }}>Пример (рус.)</label>
                        <textarea name="example_ru" value={formData.example_ru} onChange={handleChange} rows={2} style={{
                            width: '100%', padding: '12px', borderRadius: '12px', border: '1px solid #e2e8f0', fontSize: '1rem', resize: 'none'
                        }} placeholder="напр. Собака играет в саду." />
                    </div>

                    <button disabled={loading} type="submit" style={{
                        width: '100%',
                        padding: '14px',
                        backgroundColor: '#3b82f6',
                        color: 'white',
                        border: 'none',
                        borderRadius: '16px',
                        fontSize: '1.1rem',
                        fontWeight: 'bold',
                        cursor: loading ? 'not-allowed' : 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '10px',
                        opacity: loading ? 0.7 : 1,
                        boxShadow: '0 4px 6px -1px rgba(59, 130, 246, 0.4)'
                    }}>
                        {loading ? (
                            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        ) : <Plus size={20} />}
                        Добавить слово
                    </button>
                </form>
            </div>
        </div>
    );
}
