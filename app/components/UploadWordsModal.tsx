"use client";

import React, { useState, useRef } from "react";
import { X, Upload, Plus, Sparkles, Loader2, FileText, CheckCircle, AlertCircle } from "lucide-react";

interface Example {
    de: string;
    ru: string;
}

interface UploadResult {
    status: string;
    added: number;
    skipped: number;
    total: number;
    errors?: string[];
}

interface UploadWordsModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

export default function UploadWordsModal({ isOpen, onClose, onSuccess }: UploadWordsModalProps) {
    const [activeTab, setActiveTab] = useState<'single' | 'bulk'>('single');
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Состояние для одиночного добавления
    const [singleFormData, setSingleFormData] = useState({
        de: "",
        ru: "",
        article: "",
        level: "A1",
        topic: "Личные слова",
        verb_forms: "",
        example_de: "",
        example_ru: ""
    });
    const [singleExamples, setSingleExamples] = useState<Example[]>([]);
    const [selectedExample, setSelectedExample] = useState<number | null>(null);
    const [singleLoading, setSingleLoading] = useState(false);
    const [singleAiLoading, setSingleAiLoading] = useState(false);
    const [singleError, setSingleError] = useState("");
    const [singleAiError, setSingleAiError] = useState("");
    const [singleSuccess, setSingleSuccess] = useState(false);

    // Состояние для массовой загрузки
    const [bulkLoading, setBulkLoading] = useState(false);
    const [bulkError, setBulkError] = useState("");
    const [bulkResult, setBulkResult] = useState<UploadResult | null>(null);
    const [dragActive, setDragActive] = useState(false);

    if (!isOpen) return null;

    const canEnrich = singleFormData.de.trim().length > 0 && singleFormData.ru.trim().length > 0;

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        setSingleFormData({ ...singleFormData, [e.target.name]: e.target.value });
        // Если меняют слово — сбрасываем AI-результаты
        if (e.target.name === "de" || e.target.name === "ru") {
            setSingleExamples([]);
            setSelectedExample(null);
            setSingleAiError("");
        }
    };

    const handleAiEnrich = async () => {
        setSingleAiLoading(true);
        setSingleAiError("");
        try {
            const token = localStorage.getItem("token");
            const resp = await fetch("/api/words/ai-enrich", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ de: singleFormData.de, ru: singleFormData.ru })
            });
            const data = await resp.json();
            if (!resp.ok) throw new Error(data.error || "Ошибка AI");

            setSingleFormData(prev => ({
                ...prev,
                article: data.article || prev.article,
                level: data.level || prev.level,
                verb_forms: data.verb_forms || prev.verb_forms,
                example_de: data.examples?.[0]?.de || prev.example_de,
                example_ru: data.examples?.[0]?.ru || prev.example_ru,
            }));
            setSingleExamples(data.examples || []);
            setSelectedExample(0);
        } catch (err: any) {
            setSingleAiError(err.message || "Не удалось получить данные от AI");
        } finally {
            setSingleAiLoading(false);
        }
    };

    const handleSelectExample = (idx: number) => {
        setSelectedExample(idx);
        setSingleFormData(prev => ({
            ...prev,
            example_de: singleExamples[idx].de,
            example_ru: singleExamples[idx].ru,
        }));
    };

    const handleSingleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSingleLoading(true);
        setSingleError("");
        setSingleSuccess(false);

        try {
            const token = localStorage.getItem("token");
            if (!token) throw new Error("Вы не авторизованы");

            const response = await fetch("/api/words/custom", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(singleFormData)
            });
            const data = await response.json();

            if (response.ok) {
                setSingleSuccess(true);
                setTimeout(() => {
                    resetSingleForm();
                    onSuccess();
                    onClose();
                }, 1500);
            } else {
                setSingleError(data.error || "Ошибка при добавлении слова");
            }
        } catch (err: any) {
            setSingleError(err.message || "Ошибка соединения");
        } finally {
            setSingleLoading(false);
        }
    };

    const resetSingleForm = () => {
        setSingleFormData({
            de: "", ru: "", article: "", level: "A1", topic: "Личные слова",
            verb_forms: "", example_de: "", example_ru: ""
        });
        setSingleExamples([]);
        setSelectedExample(null);
        setSingleError("");
        setSingleAiError("");
        setSingleSuccess(false);
    };

    // Обработка загрузки файла
    const handleFileUpload = async (file: File) => {
        setBulkLoading(true);
        setBulkError("");
        setBulkResult(null);

        try {
            const token = localStorage.getItem("token");
            if (!token) throw new Error("Вы не авторизованы");

            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/words/bulk-upload', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Ошибка при загрузке файла');
            }

            setBulkResult(data);
            if (data.added > 0) {
                onSuccess();
            }
        } catch (err: any) {
            setBulkError(err.message || 'Ошибка загрузки файла');
        } finally {
            setBulkLoading(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const file = e.dataTransfer.files[0];
            const validTypes = ['text/csv', 'application/json', 'text/plain'];
            const validExtensions = ['.csv', '.json', '.txt'];
            const hasValidExtension = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));

            if (validTypes.includes(file.type) || hasValidExtension) {
                handleFileUpload(file);
            } else {
                setBulkError('Пожалуйста, загрузите файл в формате CSV или JSON');
            }
        }
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
    };

    const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            handleFileUpload(e.target.files[0]);
        }
    };

    const handleClose = () => {
        resetSingleForm();
        setBulkResult(null);
        setBulkError("");
        onClose();
    };

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

    const tabStyle = (isActive: boolean): React.CSSProperties => ({
        flex: 1,
        padding: "12px 16px",
        background: isActive ? "#fff" : "#f1f5f9",
        border: "none",
        borderBottom: isActive ? "2px solid #3b82f6" : "none",
        fontWeight: isActive ? 600 : 400,
        color: isActive ? "#1e293b" : "#64748b",
        cursor: "pointer",
        transition: "all 0.2s",
        fontSize: "0.9rem",
    });

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
                width: "100%", maxWidth: "600px",
                maxHeight: "90vh",
                overflow: "auto",
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
                <div style={{ padding: "28px 28px 20px" }}>
                    <h2 style={{ fontSize: "1.4rem", fontWeight: 700, margin: "0 0 4px", color: "#1e293b" }}>
                        Добавить свои слова
                    </h2>
                    <p style={{ color: "#94a3b8", fontSize: "0.85rem", margin: "0" }}>
                        Добавьте одно слово или загрузите список из файла
                    </p>
                </div>

                {/* Табы */}
                <div style={{
                    display: "flex",
                    borderBottom: "1px solid #e2e8f0",
                    marginBottom: "20px",
                }}>
                    <button
                        style={tabStyle(activeTab === 'single')}
                        onClick={() => setActiveTab('single')}
                    >
                        <Plus size={16} style={{ marginRight: "6px", display: "inline" }} />
                        Одно слово
                    </button>
                    <button
                        style={tabStyle(activeTab === 'bulk')}
                        onClick={() => setActiveTab('bulk')}
                    >
                        <Upload size={16} style={{ marginRight: "6px", display: "inline" }} />
                        Загрузить из файла
                    </button>
                </div>

                <div style={{ padding: "0 28px 28px" }}>
                    {/* ─── Одиночное добавление ─── */}
                    {activeTab === 'single' && (
                        <form onSubmit={handleSingleSubmit}>
                            {singleError && (
                                <div style={{
                                    padding: "10px 14px", background: "#fef2f2", color: "#dc2626",
                                    borderRadius: "10px", marginBottom: "14px", fontSize: "0.85rem",
                                    border: "1px solid #fecaca",
                                    display: "flex", alignItems: "center", gap: "8px",
                                }}>
                                    <AlertCircle size={16} />
                                    {singleError}
                                </div>
                            )}

                            {singleSuccess && (
                                <div style={{
                                    padding: "10px 14px", background: "#f0fdf4", color: "#16a34a",
                                    borderRadius: "10px", marginBottom: "14px", fontSize: "0.85rem",
                                    border: "1px solid #bbf7d0",
                                    display: "flex", alignItems: "center", gap: "8px",
                                }}>
                                    <CheckCircle size={16} />
                                    Слово успешно добавлено!
                                </div>
                            )}

                            {/* Немецкое слово + перевод */}
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "12px" }}>
                                <div>
                                    <label style={label}>Слово на немецком *</label>
                                    <input required style={input} type="text" name="de"
                                        value={singleFormData.de} onChange={handleChange} placeholder="напр. machen" />
                                </div>
                                <div>
                                    <label style={label}>Перевод на русский *</label>
                                    <input required style={input} type="text" name="ru"
                                        value={singleFormData.ru} onChange={handleChange} placeholder="напр. делать" />
                                </div>
                            </div>

                            {/* Кнопка AI */}
                            <button type="button" onClick={handleAiEnrich}
                                disabled={!canEnrich || singleAiLoading}
                                style={{
                                    width: "100%", padding: "10px", marginBottom: "14px",
                                    background: singleExamples.length > 0
                                        ? "linear-gradient(135deg, #10b981, #059669)"
                                        : "linear-gradient(135deg, #6366f1, #8b5cf6)",
                                    color: "#fff", border: "none", borderRadius: "12px",
                                    fontSize: "0.9rem", fontWeight: 600, cursor: canEnrich && !singleAiLoading ? "pointer" : "not-allowed",
                                    opacity: canEnrich ? 1 : 0.45,
                                    display: "flex", alignItems: "center", justifyContent: "center", gap: "8px",
                                    transition: "opacity .2s, background .3s",
                                }}>
                                {singleAiLoading ? <Loader2 size={16} style={{ animation: "spin 1s linear infinite" }} /> : <Sparkles size={16} />}
                                {singleAiLoading ? "ИИ анализирует..." : singleExamples.length > 0 ? "✓ Данные заполнены" : "Заполнить с помощью ИИ"}
                            </button>

                            {singleAiError && (
                                <div style={{
                                    padding: "8px 12px", background: "#fef2f2", color: "#dc2626",
                                    borderRadius: "8px", marginBottom: "12px", fontSize: "0.82rem",
                                }}>{singleAiError}</div>
                            )}

                            {/* Артикль + Уровень */}
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "12px" }}>
                                <div>
                                    <label style={label}>Артикль</label>
                                    <select name="article" value={singleFormData.article} onChange={handleChange} style={input}>
                                        <option value="">Без артикля</option>
                                        <option value="der">der (m)</option>
                                        <option value="die">die (f)</option>
                                        <option value="das">das (n)</option>
                                    </select>
                                </div>
                                <div>
                                    <label style={label}>Уровень</label>
                                    <select name="level" value={singleFormData.level} onChange={handleChange} style={input}>
                                        {["A1", "A2", "B1", "B2", "C1"].map(l => <option key={l}>{l}</option>)}
                                    </select>
                                </div>
                            </div>

                            {/* Тема */}
                            <div style={{ marginBottom: "12px" }}>
                                <label style={label}>Тема</label>
                                <input type="text" name="topic" style={input}
                                    value={singleFormData.topic} onChange={handleChange}
                                    placeholder="напр. Глаголы" />
                            </div>

                            {/* Формы глагола */}
                            <div style={{ marginBottom: "12px" }}>
                                <label style={label}>
                                    Формы глагола <span style={{ fontWeight: 400, color: "#94a3b8" }}>(для глаголов)</span>
                                </label>
                                <input type="text" name="verb_forms" style={input}
                                    value={singleFormData.verb_forms} onChange={handleChange}
                                    placeholder="напр. machen, machte, hat gemacht" />
                            </div>

                            {/* Примеры от AI */}
                            {singleExamples.length > 0 && (
                                <div style={{ marginBottom: "12px" }}>
                                    <label style={label}>Выберите пример</label>
                                    <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                                        {singleExamples.map((ex, i) => (
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

                            {/* Примеры вручную (если AI не использовался) */}
                            {singleExamples.length === 0 && (
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "14px" }}>
                                    <div>
                                        <label style={label}>Пример (нем.)</label>
                                        <input type="text" name="example_de" style={input}
                                            value={singleFormData.example_de} onChange={handleChange}
                                            placeholder="напр. Er macht das gut." />
                                    </div>
                                    <div>
                                        <label style={label}>Пример (рус.)</label>
                                        <input type="text" name="example_ru" style={input}
                                            value={singleFormData.example_ru} onChange={handleChange}
                                            placeholder="напр. Он делает это хорошо." />
                                    </div>
                                </div>
                            )}

                            {/* Кнопка сохранить */}
                            <button disabled={singleLoading} type="submit" style={{
                                width: "100%", padding: "13px",
                                background: "linear-gradient(135deg, #3b82f6, #2563eb)",
                                color: "#fff", border: "none", borderRadius: "14px",
                                fontSize: "1rem", fontWeight: 700, cursor: singleLoading ? "not-allowed" : "pointer",
                                display: "flex", alignItems: "center", justifyContent: "center", gap: "8px",
                                opacity: singleLoading ? 0.7 : 1,
                                boxShadow: "0 4px 14px rgba(59,130,246,0.4)",
                                transition: "opacity .2s",
                            }}>
                                {singleLoading
                                    ? <Loader2 size={18} style={{ animation: "spin 1s linear infinite" }} />
                                    : <Plus size={18} />}
                                Добавить слово
                            </button>
                        </form>
                    )}

                    {/* ─── Массовая загрузка ─── */}
                    {activeTab === 'bulk' && (
                        <div>
                            {bulkError && (
                                <div style={{
                                    padding: "10px 14px", background: "#fef2f2", color: "#dc2626",
                                    borderRadius: "10px", marginBottom: "14px", fontSize: "0.85rem",
                                    border: "1px solid #fecaca",
                                    display: "flex", alignItems: "center", gap: "8px",
                                }}>
                                    <AlertCircle size={16} />
                                    {bulkError}
                                </div>
                            )}

                            {bulkResult && (
                                <div style={{
                                    padding: "16px", background: bulkResult.added > 0 ? "#f0fdf4" : "#fff7ed",
                                    borderRadius: "12px", marginBottom: "16px",
                                    border: `1px solid ${bulkResult.added > 0 ? "#bbf7d0" : "#fed7aa"}`,
                                }}>
                                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
                                        {bulkResult.added > 0 ? (
                                            <CheckCircle size={20} className="text-green-600" style={{ color: "#16a34a" }} />
                                        ) : (
                                            <AlertCircle size={20} style={{ color: "#ea580c" }} />
                                        )}
                                        <span style={{ fontWeight: 600, color: "#1e293b" }}>
                                            {bulkResult.added > 0 ? 'Загрузка завершена!' : 'Загрузка завершена с ошибками'}
                                        </span>
                                    </div>
                                    <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px" }}>
                                        <div style={{ textAlign: "center" }}>
                                            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#3b82f6" }}>
                                                {bulkResult.total}
                                            </div>
                                            <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Всего</div>
                                        </div>
                                        <div style={{ textAlign: "center" }}>
                                            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#16a34a" }}>
                                                {bulkResult.added}
                                            </div>
                                            <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Добавлено</div>
                                        </div>
                                        <div style={{ textAlign: "center" }}>
                                            <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "#f59e0b" }}>
                                                {bulkResult.skipped}
                                            </div>
                                            <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Пропущено</div>
                                        </div>
                                    </div>
                                    {bulkResult.errors && bulkResult.errors.length > 0 && (
                                        <div style={{
                                            marginTop: "12px",
                                            padding: "10px",
                                            background: "#fef2f2",
                                            borderRadius: "8px",
                                            fontSize: "0.8rem",
                                            color: "#dc2626",
                                            maxHeight: "150px",
                                            overflow: "auto",
                                        }}>
                                            <div style={{ fontWeight: 600, marginBottom: "6px" }}>Ошибки:</div>
                                            {bulkResult.errors.map((error, idx) => (
                                                <div key={idx}>• {error}</div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Drag & Drop зона */}
                            <div
                                onDragEnter={handleDragOver}
                                onDragOver={handleDragOver}
                                onDragLeave={handleDragLeave}
                                onDrop={handleDrop}
                                style={{
                                    border: `2px dashed ${dragActive ? "#3b82f6" : "#cbd5e1"}`,
                                    borderRadius: "16px",
                                    padding: "40px 20px",
                                    textAlign: "center",
                                    background: dragActive ? "#eff6ff" : "#f8fafc",
                                    transition: "all 0.2s",
                                    cursor: "pointer",
                                }}
                                onClick={() => fileInputRef.current?.click()}
                            >
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".csv,.json"
                                    onChange={handleFileInput}
                                    style={{ display: "none" }}
                                />
                                <Upload size={48} style={{ color: dragActive ? "#3b82f6" : "#94a3b8", marginBottom: "16px" }} />
                                <div style={{ fontSize: "1rem", fontWeight: 600, color: "#1e293b", marginBottom: "8px" }}>
                                    {dragActive ? "Отпустите файл здесь" : "Перетащите файл сюда"}
                                </div>
                                <div style={{ fontSize: "0.85rem", color: "#64748b", marginBottom: "16px" }}>
                                    или нажмите для выбора файла
                                </div>
                                <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
                                    Поддерживаются форматы: CSV, JSON (макс. 500 слов)
                                </div>
                            </div>

                            {bulkLoading && (
                                <div style={{
                                    display: "flex",
                                    alignItems: "center",
                                    justifyContent: "center",
                                    gap: "10px",
                                    marginTop: "20px",
                                    padding: "16px",
                                    background: "#f1f5f9",
                                    borderRadius: "12px",
                                }}>
                                    <Loader2 size={20} style={{ animation: "spin 1s linear infinite" }} />
                                    <span style={{ fontWeight: 500, color: "#475569" }}>Загрузка слов...</span>
                                </div>
                            )}

                            {/* Информация о формате */}
                            <div style={{
                                marginTop: "20px",
                                padding: "16px",
                                background: "#f8fafc",
                                borderRadius: "12px",
                                border: "1px solid #e2e8f0",
                            }}>
                                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
                                    <FileText size={18} style={{ color: "#3b82f6" }} />
                                    <span style={{ fontWeight: 600, color: "#1e293b" }}>Формат файла</span>
                                </div>
                                <div style={{ fontSize: "0.85rem", color: "#64748b", lineHeight: 1.6 }}>
                                    <div style={{ marginBottom: "8px" }}>
                                        <strong>CSV:</strong> de,ru,article,level,topic,verb_forms,example_de,example_ru
                                    </div>
                                    <div>
                                        <strong>JSON:</strong> [{"{"} "de": "слово", "ru": "перевод", "level": "A1" {"}"}], ...
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            </div>
        </div>
    );
}
