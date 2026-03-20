"use client";

import React, { useState } from "react";
import { X, Plus, Loader2 } from "lucide-react";

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
    const [success, setSuccess] = useState(false);

    if (!isOpen) return null;

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        setSuccess(false);
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
                setSuccess(true);
                setTimeout(() => {
                    resetForm();
                    onSuccess(data.word_id);
                    onClose();
                }, 1500);
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
        setError("");
        setSuccess(false);
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
                width: "100%", maxWidth: "480px",
                padding: "28px 28px 24px",
                position: "relative",
                boxShadow: "0 24px 48px rgba(0,0,0,0.18)",
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
                    Добавить слово
                </h2>
                <p style={{ color: "#94a3b8", fontSize: "0.85rem", margin: "0 0 18px" }}>
                    Быстрое добавление личного слова
                </p>

                {error && (
                    <div style={{
                        padding: "10px 14px", background: "#fef2f2", color: "#dc2626",
                        borderRadius: "10px", marginBottom: "14px", fontSize: "0.85rem",
                        border: "1px solid #fecaca",
                    }}>{error}</div>
                )}

                {success && (
                    <div style={{
                        padding: "10px 14px", background: "#f0fdf4", color: "#16a34a",
                        borderRadius: "10px", marginBottom: "14px", fontSize: "0.85rem",
                        border: "1px solid #bbf7d0",
                    }}>✓ Слово успешно добавлено!</div>
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
                    }}>
                        {loading
                            ? <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
                            : <Plus size={18} />}
                        Добавить слово
                    </button>
                </form>

                {/* Подсказка про расширенное добавление */}
                <div style={{
                    marginTop: "16px",
                    padding: "12px",
                    background: "#f8fafc",
                    borderRadius: "12px",
                    border: "1px solid #e2e8f0",
                    textAlign: "center",
                }}>
                    <p style={{ fontSize: "0.8rem", color: "#64748b", margin: "0 0 8px" }}>
                        Хотите добавить слово с примерами и формами?
                    </p>
                    <a
                        href="/profile/my-words"
                        style={{
                            fontSize: "0.8rem",
                            color: "#3b82f6",
                            fontWeight: 600,
                            textDecoration: "none",
                        }}
                        onClick={(e) => {
                            e.preventDefault();
                            onClose();
                            window.location.href = "/profile/my-words";
                        }}
                    >
                        Перейти в профиль →
                    </a>
                </div>

                <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            </div>
        </div>
    );
}
