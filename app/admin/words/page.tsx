"use client";

import React, { useEffect, useState } from 'react';
import AdminLayout from '../AdminLayout';
import { Plus, Search, Edit, Trash2, Filter, Loader2, AlertCircle, CheckCircle, Sparkles } from 'lucide-react';

interface Word {
  id: number;
  level: string;
  topic: string;
  de: string;
  ru: string;
  article?: string;
  verb_forms?: string;
  plural?: string;
  example_de?: string;
  example_ru?: string;
  synonyms?: string;
  antonyms?: string;
  collocations?: string;
  is_favorite?: boolean;
}

interface WordsResponse {
  data: Word[];
  total: number;
  skip: number;
  limit: number;
}

export default function AdminWordsPage() {
  const [words, setWords] = useState<Word[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Filters
  const [search, setSearch] = useState('');
  const [levelFilter, setLevelFilter] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const limit = 20;

  // Функция для закрытия модального окна со сбросом состояний
  const closeModal = () => {
    console.log('closeModal called');
    setEditingWord(null);
    setFormData({ 
      de: '', ru: '', article: '', level: 'A1', topic: '',
      verb_forms: '', plural: '', example_de: '', example_ru: '',
      synonyms: '', antonyms: '', collocations: ''
    });
    setShowModal(false);
    setAiError('');

    // Принудительно проверяем через setTimeout
    setTimeout(() => {
      console.log('After closeModal:', { showModal: false, editingWord: null });
    }, 100);
  };

  // Заполнение с помощью ИИ
  const handleAiEnrich = async () => {
    if (!formData.de || !formData.ru) {
      setAiError('Введите немецкое слово и перевод');
      return;
    }

    setAiLoading(true);
    setAiError('');

    try {
      const token = localStorage.getItem('token');
      const resp = await fetch('/api/words/ai-enrich', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ de: formData.de, ru: formData.ru }),
      });

      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || 'Ошибка AI');

      setFormData(prev => ({
        ...prev,
        article: data.article || prev.article,
        level: data.level || prev.level,
        topic: data.topic || prev.topic,
        verb_forms: data.verb_forms || prev.verb_forms,
        plural: data.plural || prev.plural,
        example_de: data.examples?.[0]?.de || prev.example_de,
        example_ru: data.examples?.[0]?.ru || prev.example_ru,
        synonyms: data.synonyms || prev.synonyms,
        antonyms: data.antonyms || prev.antonyms,
        collocations: data.collocations || prev.collocations,
      }));

      setSuccess('ИИ заполнил данные!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setAiError(err.message || 'Не удалось получить данные от AI');
    } finally {
      setAiLoading(false);
    }
  };

  // Modal
  const [showModal, setShowModal] = useState(false);
  const [editingWord, setEditingWord] = useState<Word | null>(null);
  const [formData, setFormData] = useState({
    de: '',
    ru: '',
    article: '',
    level: 'A1',
    topic: '',
    verb_forms: '',
    plural: '',
    example_de: '',
    example_ru: '',
    synonyms: '',
    antonyms: '',
    collocations: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState('');

  useEffect(() => {
    loadWords();
  }, [page, levelFilter]);

  const loadWords = async () => {
    setLoading(true);
    setError('');
    
    try {
      const params = new URLSearchParams({
        page: String(page),
        limit: String(limit),
      });
      
      if (levelFilter) params.set('level', levelFilter);
      if (search) params.set('search', search);

      const res = await fetch(`/api/admin/words?${params.toString()}`);
      
      if (!res.ok) throw new Error('Ошибка загрузки слов');
      
      const data: WordsResponse = await res.json();
      setWords(data.data || []);
      setTotal(data.total || 0);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setPage(1);
    loadWords();
  };

  const openAddModal = () => {
    setEditingWord(null);
    setFormData({ 
      de: '', ru: '', article: '', level: 'A1', topic: '',
      verb_forms: '', plural: '', example_de: '', example_ru: '',
      synonyms: '', antonyms: '', collocations: ''
    });
    setShowModal(true);
  };

  const openEditModal = (word: Word) => {
    setEditingWord(word);
    setFormData({
      de: word.de,
      ru: word.ru,
      article: word.article || '',
      level: word.level,
      topic: word.topic || '',
      verb_forms: word.verb_forms || '',
      plural: word.plural || '',
      example_de: word.example_de || '',
      example_ru: word.example_ru || '',
      synonyms: word.synonyms || '',
      antonyms: word.antonyms || '',
      collocations: word.collocations || '',
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    console.log('=== handleSubmit called ===');

    // Предотвращаем повторную отправку
    if (isSubmitting) {
      console.log('Already submitting, ignoring');
      return;
    }

    console.log('Form submit:', { editingWord, formData });
    setIsSubmitting(true);

    try {
      // Определяем метод и URL
      const method = editingWord ? 'PUT' : 'POST';
      const url = '/api/admin/words';  // Всегда один URL

      // Добавляем ID для обновления
      const body = editingWord
        ? { ...formData, id: editingWord.id }
        : formData;

      console.log('Sending request:', { method, url, body });
      console.log('editingWord:', editingWord);
      console.log('formData:', formData);

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      console.log('Response status:', res.status);

      const data = await res.json();
      console.log('Response data:', data);

      if (!res.ok) {
        console.error('Server error:', data);
        throw new Error(data.error || 'Ошибка сохранения');
      }

      setSuccess(editingWord ? 'Слово обновлено' : 'Слово добавлено');

      console.log('Calling closeModal...');
      closeModal();
      console.log('closeModal returned');

      console.log('Reloading words...');
      await loadWords();
      console.log('Words reloaded');

      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      console.error('Form submit error:', err);
      console.error('Error name:', err.name);
      console.error('Error message:', err.message);
      console.error('Error stack:', err.stack);
      setError(err.message);
      setTimeout(() => setError(''), 3000);
    } finally {
      setIsSubmitting(false);
      console.log('=== handleSubmit finished ===');
    }
  };

  const handleDelete = async (wordId: number) => {
    if (!confirm('Удалить это слово?')) return;

    try {
      const res = await fetch(`/api/admin/words?id=${wordId}`, {
        method: 'DELETE',
      });

      const data = await res.json();

      if (!res.ok) throw new Error(data.error || 'Ошибка удаления');

      setSuccess('Слово удалено');
      loadWords();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.message);
      setTimeout(() => setError(''), 3000);
    }
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <AdminLayout>
      {error && (
        <div className="adminAlert adminAlertError">
          <AlertCircle size={20} />
          {error}
        </div>
      )}
      
      {success && (
        <div className="adminAlert adminAlertSuccess">
          <CheckCircle size={20} />
          {success}
        </div>
      )}

      <div className="adminCard">
        <div className="adminCardHeader">
          <h3 className="adminCardTitle">Управление словами</h3>
          <button className="adminBtn adminBtnPrimary" onClick={openAddModal}>
            <Plus size={18} />
            Добавить слово
          </button>
        </div>

        {/* Search & Filters */}
        <div className="adminSearchBar">
          <div style={{ position: 'relative', flex: 1 }}>
            <Search
              size={18}
              style={{
                position: 'absolute',
                left: 12,
                top: '50%',
                transform: 'translateY(-50%)',
                color: '#9ca3af',
              }}
            />
            <input
              type="text"
              placeholder="Поиск слов..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="adminSearchInput"
              style={{ paddingLeft: 40 }}
            />
          </div>
          
          <select
            value={levelFilter}
            onChange={(e) => { setLevelFilter(e.target.value); setPage(1); }}
            className="adminFormSelect"
            style={{ minWidth: 120 }}
          >
            <option value="">Все уровни</option>
            <option value="A1">A1</option>
            <option value="A2">A2</option>
            <option value="B1">B1</option>
            <option value="B2">B2</option>
            <option value="C1">C1</option>
          </select>
          
          <button className="adminBtn adminBtnSecondary" onClick={handleSearch}>
            <Search size={18} />
          </button>
        </div>

        {/* Table */}
        {loading ? (
          <div className="adminLoading">
            <div className="adminLoadingSpinner" />
          </div>
        ) : (
          <>
            <table className="adminTable">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Уровень</th>
                  <th>Немецкий</th>
                  <th>Русский</th>
                  <th>Тема</th>
                  <th>Действия</th>
                </tr>
              </thead>
              <tbody>
                {words.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>
                      Слова не найдены
                    </td>
                  </tr>
                ) : (
                  words.map((word) => (
                    <tr key={word.id}>
                      <td style={{ color: '#94a3b8', fontSize: '0.75rem' }}>#{word.id}</td>
                      <td>
                        <span className="adminBadge adminBadgeBlue">{word.level}</span>
                      </td>
                      <td>
                        <strong>{word.article && <span style={{ color: '#3b82f6' }}>{word.article} </span>}
                        {word.de}</strong>
                      </td>
                      <td>{word.ru}</td>
                      <td style={{ color: '#64748b' }}>{word.topic || '—'}</td>
                      <td>
                        <div className="adminTableActions">
                          <button
                            className="adminBtn adminBtnSecondary adminBtnSm"
                            onClick={() => openEditModal(word)}
                          >
                            <Edit size={14} />
                          </button>
                          <button
                            className="adminBtn adminBtnDanger adminBtnSm"
                            onClick={() => handleDelete(word.id)}
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="adminPagination">
                <button
                  className="adminPaginationBtn"
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  ← Назад
                </button>
                
                <span style={{ fontSize: '0.875rem', color: '#64748b' }}>
                  Страница {page} из {totalPages}
                </span>
                
                <button
                  className="adminPaginationBtn"
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  Вперёд →
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={closeModal}
        >
          <div
            style={{
              background: 'white',
              borderRadius: 12,
              padding: 32,
              width: '100%',
              maxWidth: 500,
              maxHeight: '90vh',
              overflow: 'auto',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: 24 }}>
              {editingWord ? 'Редактировать слово' : 'Новое слово'}
            </h3>

            <form onSubmit={handleSubmit} className="adminForm">
              <div className="adminFormGroup">
                <label className="adminFormLabel">Немецкое слово *</label>
                <input
                  type="text"
                  value={formData.de}
                  onChange={(e) => setFormData({ ...formData, de: e.target.value })}
                  className="adminFormInput"
                  required
                />
              </div>

              <div className="adminFormGroup">
                <label className="adminFormLabel">Русский перевод *</label>
                <input
                  type="text"
                  value={formData.ru}
                  onChange={(e) => setFormData({ ...formData, ru: e.target.value })}
                  className="adminFormInput"
                  required
                />
              </div>

              {/* Кнопка ИИ */}
              {!editingWord && (
                <button
                  type="button"
                  onClick={handleAiEnrich}
                  disabled={aiLoading || !formData.de || !formData.ru}
                  style={{
                    width: '100%',
                    padding: '10px',
                    marginBottom: '16px',
                    background: aiLoading 
                      ? 'linear-gradient(135deg, #6b7280, #4b5563)'
                      : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '8px',
                    fontSize: '0.9rem',
                    fontWeight: 600,
                    cursor: aiLoading || !formData.de || !formData.ru ? 'not-allowed' : 'pointer',
                    opacity: aiLoading || !formData.de || !formData.ru ? 0.6 : 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                  }}
                >
                  {aiLoading ? <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> : <Sparkles size={16} />}
                  {aiLoading ? 'ИИ анализирует...' : 'Заполнить с помощью ИИ'}
                </button>
              )}

              {aiError && (
                <div style={{
                  padding: '8px 12px',
                  background: '#fef2f2',
                  color: '#dc2626',
                  borderRadius: '8px',
                  marginBottom: '16px',
                  fontSize: '0.82rem',
                }}>{aiError}</div>
              )}

              <div className="adminFormGroup">
                <label className="adminFormLabel">Артикль</label>
                <input
                  type="text"
                  value={formData.article}
                  onChange={(e) => setFormData({ ...formData, article: e.target.value })}
                  className="adminFormInput"
                  placeholder="der, die, das"
                />
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div className="adminFormGroup">
                  <label className="adminFormLabel">Уровень *</label>
                  <select
                    value={formData.level}
                    onChange={(e) => setFormData({ ...formData, level: e.target.value })}
                    className="adminFormSelect"
                    required
                  >
                    <option value="A1">A1</option>
                    <option value="A2">A2</option>
                    <option value="B1">B1</option>
                    <option value="B2">B2</option>
                    <option value="C1">C1</option>
                  </select>
                </div>

                <div className="adminFormGroup">
                  <label className="adminFormLabel">Тема</label>
                  <input
                    type="text"
                    value={formData.topic}
                    onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                    className="adminFormInput"
                    placeholder="Например: Еда"
                  />
                </div>
              </div>

              <div className="adminFormGroup">
                <label className="adminFormLabel">Формы глагола</label>
                <input
                  type="text"
                  value={formData.verb_forms}
                  onChange={(e) => setFormData({ ...formData, verb_forms: e.target.value })}
                  className="adminFormInput"
                  placeholder="напр. machen, machte, hat gemacht"
                />
              </div>

              <div className="adminFormGroup">
                <label className="adminFormLabel">Множественное число</label>
                <input
                  type="text"
                  value={formData.plural}
                  onChange={(e) => setFormData({ ...formData, plural: e.target.value })}
                  className="adminFormInput"
                  placeholder="напр. die Häuser"
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div className="adminFormGroup">
                  <label className="adminFormLabel">Пример (немецкий)</label>
                  <input
                    type="text"
                    value={formData.example_de}
                    onChange={(e) => setFormData({ ...formData, example_de: e.target.value })}
                    className="adminFormInput"
                    placeholder="Der Apfel ist rot."
                  />
                </div>

                <div className="adminFormGroup">
                  <label className="adminFormLabel">Пример (русский)</label>
                  <input
                    type="text"
                    value={formData.example_ru}
                    onChange={(e) => setFormData({ ...formData, example_ru: e.target.value })}
                    className="adminFormInput"
                    placeholder="Яблоко красное."
                  />
                </div>
              </div>

              <div className="adminFormGroup">
                <label className="adminFormLabel">Синонимы</label>
                <input
                  type="text"
                  value={formData.synonyms}
                  onChange={(e) => setFormData({ ...formData, synonyms: e.target.value })}
                  className="adminFormInput"
                  placeholder="напр. groß, riesig"
                />
              </div>

              <div className="adminFormGroup">
                <label className="adminFormLabel">Антонимы</label>
                <input
                  type="text"
                  value={formData.antonyms}
                  onChange={(e) => setFormData({ ...formData, antonyms: e.target.value })}
                  className="adminFormInput"
                  placeholder="напр. klein, winzig"
                />
              </div>

              <div className="adminFormGroup">
                <label className="adminFormLabel">Коллокации</label>
                <input
                  type="text"
                  value={formData.collocations}
                  onChange={(e) => setFormData({ ...formData, collocations: e.target.value })}
                  className="adminFormInput"
                  placeholder="напр. einen Apfel essen"
                />
              </div>
              
              <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
                <button
                  type="submit"
                  className="adminBtn adminBtnPrimary"
                  style={{ flex: 1, opacity: isSubmitting ? 0.7 : 1, cursor: isSubmitting ? 'not-allowed' : 'pointer' }}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Сохранение...' : (editingWord ? 'Сохранить' : 'Добавить')}
                </button>
                <button
                  type="button"
                  onClick={closeModal}
                  className="adminBtn adminBtnSecondary"
                  disabled={isSubmitting}
                >
                  Отмена
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </AdminLayout>
  );
}
