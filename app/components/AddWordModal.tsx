"use client";

import React, { useState } from "react";
import { X, Plus, Sparkles, Loader2, ChevronDown } from "lucide-react";

interface Example {
    de: string;
    ru: string;
}

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
    const [examples, setExamples] = useState<Example[]>([]);
    const [selectedExample, setSelectedExample] = useState<number | null>(null);

    const [loading, setLoading] = useState(false);
    const [aiLoading, setAiLoading] = useState(false);
    const [error, setError] = useState("");
    const [aiError, setAiError] = useState("");
    const [aiDone, setAiDone] = useState(false);

    if (!isOpen) return null;

    const canEnrich = formData.de.trim().length > 0 && formData.ru.trim().length > 0;

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
        // Если меняют слово — сбрасываем AI-результаты
        if (e.target.name === "de" || e.target.name === "ru") {
            setAiDone(false);
            setExamples([]);
            setSelectedExample(null);
        }
    };

    const handleAiEnrich = async () => {
        setAiLoading(true);
        setAiError("");
        setAiDone(false);
        try {
            const token = localStorage.getItem("token");
            const resp = await fetch("/api/words/ai-enrich", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ de: formData.de, ru: formData.ru })
            });
            const data = await resp.json();
            if (!resp.ok) throw new Error(data.error || "Ошибка AI");

            setFormData(prev => ({
                ...prev,
                article: data.article || prev.article,
                level: data.level || prev.level,
                verb_forms: data.verb_forms || prev.verb_forms,
                example_de: data.examples?.[0]?.de || prev.example_de,
                example_ru: data.examples?.[0]?.ru || prev.example_ru,
            }));
            setExamples(data.examples || []);
            setSelectedExample(0);
            setAiDone(true);
        } catch (err: any) {
            setAiError(err.message || "Не удалось получить данные от AI");
        } finally {
            setAiLoading(false);
        }
    };

    const handleSelectExample = (idx: number) => {
        setSelectedExample(idx);
        setFormData(prev => ({
            ...prev,
            example_de: examples[idx].de,
            example_ru: examples[idx].ru,
        }));
    };

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
                resetForm();
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

    const resetForm = () => {
        setFormData({ de: "", ru: "", article: "", level: "A1", topic: "Личные слова", verb_forms: "", example_de: "", example_ru: "" });
        setExamples([]);
        setSelectedExample(null);
        setAiDone(false);
        setError("");
        setAiError("");
    };

    const handleClose = () => { resetForm(); onClose(); };

    /* ─── Стили ─── */
    const input: React.CSSProperties = {
        width: "100%", padding: "10px 12px", borderRadius: "10px",
        border: "1.5px solid #e2e8f0", fontSize: "0.95rem",
        outline: "none", boxSizing: "border-box", background: "#fff",
        transition: "border-color .15s",
    };
    const label: React.CSSProperties = {
        display: "block", fontSize: "0.82rem", fontWeight: 600,
        marginBottom: "5px", color: "#475569",
    };

    return (
        <div style={{
            position: "fixed", inset: 0,
            backgroundColor: "rgba(15,23,42,0.55)",
            display: "flex", alignItems: "center", justifyContent: "center",
            zIndex: 1000, backdropFilter: "blur(5px)",
        }} onClick={handleClose}>
            <div style={{
                backgroundColor: "#fff",
                borderRadius: "20px",
                width: "100%", maxWidth: "540px",
                padding: "28px 28px 24px",
                position: "relative",
                boxShadow: "0 24px 48px rgba(0,0,0,0.18)",
                overflow: "hidden",          /* no scrollbar */
            }} onClick={e => e.stopPropagation()}>

                {/* Закрыть */}
                <button onClick={handleClose} style={{
                    position: "absolute", top: 16, right: 16,
                    background: "#f1f5f9", border: "none", borderRadius: "50%",
                    width: 32, height: 32, cursor: "pointer",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    color: "#64748b",
                }}>
                    <X size={16} />
                </button>

                {/* Заголовок */}
                <h2 style={{ fontSize: "1.4rem", fontWeight: 700, margin: "0 0 4px", color: "#1e293b" }}>
                    Добавить своё слово
                </h2>
                <p style={{ color: "#94a3b8", fontSize: "0.85rem", margin: "0 0 18px" }}>
                    Введите слово и перевод, затем ИИ заполнит остальное.
                </p>

                {error && (
                    <div style={{
                        padding: "10px 14px", background: "#fef2f2", color: "#dc2626",
                        borderRadius: "10px", marginBottom: "14px", fontSize: "0.85rem",
                        border: "1px solid #fecaca",
                    }}>{error}</div>
                )}

                <form onSubmit={handleSubmit}>

                    {/* Немецкое слово + перевод */}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "12px" }}>
                        <div>
                            <label style={label}>Слово на немецком *</label>
                            <input required style={input} type="text" name="de"
                                value={formData.de} onChange={handleChange} placeholder="напр. machen" />
                        </div>
                        <div>
                            <label style={label}>Перевод на русский *</label>
                            <input required style={input} type="text" name="ru"
                                value={formData.ru} onChange={handleChange} placeholder="напр. делать" />
                        </div>
                    </div>

                    {/* Кнопка AI */}
                    <button type="button" onClick={handleAiEnrich}
                        disabled={!canEnrich || aiLoading}
                        style={{
                            width: "100%", padding: "10px", marginBottom: "14px",
                            background: aiDone
                                ? "linear-gradient(135deg, #10b981, #059669)"
                                : "linear-gradient(135deg, #6366f1, #8b5cf6)",
                            color: "#fff", border: "none", borderRadius: "12px",
                            fontSize: "0.9rem", fontWeight: 600, cursor: canEnrich && !aiLoading ? "pointer" : "not-allowed",
                            opacity: canEnrich ? 1 : 0.45,
                            display: "flex", alignItems: "center", justifyContent: "center", gap: "8px",
                            transition: "opacity .2s, background .3s",
                        }}>
                        {aiLoading ? <Loader2 size={16} style={{ animation: "spin 1s linear infinite" }} /> : <Sparkles size={16} />}
                        {aiLoading ? "ИИ анализирует..." : aiDone ? "✓ Данные заполнены" : "Заполнить с помощью ИИ"}
                    </button>

                    {aiError && (
                        <div style={{
                            padding: "8px 12px", background: "#fef2f2", color: "#dc2626",
                            borderRadius: "8px", marginBottom: "12px", fontSize: "0.82rem",
                        }}>{aiError}</div>
                    )}

                    {/* Артикль + Уровень */}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "12px" }}>
                        <div>
                            <label style={label}>Артикль</label>
                            <select name="article" value={formData.article} onChange={handleChange} style={input}>
                                <option value="">Без артикля</option>
                                <option value="der">der (m)</option>
                                <option value="die">die (f)</option>
                                <option value="das">das (n)</option>
                            </select>
                        </div>
                        <div>
                            <label style={label}>Уровень</label>
                            <select name="level" value={formData.level} onChange={handleChange} style={input}>
                                {["A1", "A2", "B1", "B2", "C1"].map(l => <option key={l}>{l}</option>)}
                            </select>
                        </div>
                    </div>

                    {/* Формы глагола */}
                    <div style={{ marginBottom: "12px" }}>
                        <label style={label}>
                            Формы глагола <span style={{ fontWeight: 400, color: "#94a3b8" }}>(для глаголов)</span>
                        </label>
                        <input type="text" name="verb_forms" style={input}
                            value={formData.verb_forms} onChange={handleChange}
                            placeholder="напр. machen, machte, hat gemacht" />
                    </div>

                    {/* Примеры от AI */}
                    {examples.length > 0 && (
                        <div style={{ marginBottom: "12px" }}>
                            <label style={label}>Выберите пример</label>
                            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                                {examples.map((ex, i) => (
                                    <div key={i} onClick={() => handleSelectExample(i)}
                                        style={{
                                            padding: "10px 12px", borderRadius: "10px", cursor: "pointer",
                                            border: `1.5px solid ${selectedExample === i ? "#6366f1" : "#e2e8f0"}`,
                                            background: selectedExample === i ? "#eef2ff" : "#f8fafc",
                                            transition: "all .15s",
                                        }}>
                                        <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "#1e293b" }}>{ex.de}</div>
                                        <div style={{ fontSize: "0.8rem", color: "#64748b", marginTop: "2px" }}>{ex.ru}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Пример вручную (ред.) */}
                    {examples.length === 0 && (
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "14px" }}>
                            <div>
                                <label style={label}>Пример (нем.)</label>
                                <input type="text" name="example_de" style={input}
                                    value={formData.example_de} onChange={handleChange}
                                    placeholder="напр. Er macht das gut." />
                            </div>
                            <div>
                                <label style={label}>Пример (рус.)</label>
                                <input type="text" name="example_ru" style={input}
                                    value={formData.example_ru} onChange={handleChange}
                                    placeholder="напр. Он делает это хорошо." />
                            </div>
                        </div>
                    )}

                    {/* Кнопка сохранить */}
                    <button disabled={loading} type="submit" style={{
                        width: "100%", padding: "13px",
                        background: "linear-gradient(135deg, #3b82f6, #2563eb)",
                        color: "#fff", border: "none", borderRadius: "14px",
                        fontSize: "1rem", fontWeight: 700, cursor: loading ? "not-allowed" : "pointer",
                        display: "flex", alignItems: "center", justifyContent: "center", gap: "8px",
                        opacity: loading ? 0.7 : 1,
                        boxShadow: "0 4px 14px rgba(59,130,246,0.4)",
                        transition: "opacity .2s",
                        marginTop: examples.length > 0 ? "14px" : 0,
                    }}>
                        {loading
                            ? <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
                            : <Plus size={18} />}
                        Добавить слово
                    </button>
                </form>

                {/* spin-keyframe */}
                <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            </div>
        </div>
    );
}
