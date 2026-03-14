"use client";

import React, { useEffect, useState } from 'react';
import AdminLayout from '../AdminLayout';
import { Plus, Search, Edit, Trash2, Filter, Loader2, AlertCircle, CheckCircle } from 'lucide-react';

interface Word {
  id: number;
  level: string;
  topic: string;
  de: string;
  ru: string;
  article?: string;
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
    setEditingWord(null);
    setFormData({ de: '', ru: '', article: '', level: 'A1', topic: '' });
    setShowModal(false);
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
  });

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
    setFormData({ de: '', ru: '', article: '', level: 'A1', topic: '' });
    setShowModal(true);
  };

  const openEditModal = (word: Word) => {
    setEditingWord(word);
    setFormData({
      de: word.de,
      ru: word.ru,
      article: word.article || '',
      level: word.level,
      topic: word.topic,
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    console.log('Form submit:', { editingWord, formData });

    try {
      // Определяем метод и URL
      const method = editingWord ? 'PUT' : 'POST';
      const url = '/api/admin/words';

      // Добавляем ID для обновления
      const body = editingWord
        ? { ...formData, id: editingWord.id }
        : formData;

      console.log('Sending request:', { method, url, body });

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      console.log('Response status:', res.status);

      const data = await res.json();
      console.log('Response data:', data);

      if (!res.ok) throw new Error(data.error || 'Ошибка сохранения');

      setSuccess(editingWord ? 'Слово обновлено' : 'Слово добавлено');
      
      // Закрываем модальное окно
      closeModal();
      
      await loadWords();

      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      console.error('Form submit error:', err);
      setError(err.message);
      setTimeout(() => setError(''), 3000);
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
                <label className="adminFormLabel">Артикль</label>
                <input
                  type="text"
                  value={formData.article}
                  onChange={(e) => setFormData({ ...formData, article: e.target.value })}
                  className="adminFormInput"
                  placeholder="der, die, das"
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
              
              <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
                <button type="submit" className="adminBtn adminBtnPrimary" style={{ flex: 1 }}>
                  {editingWord ? 'Сохранить' : 'Добавить'}
                </button>
                <button
                  type="button"
                  onClick={closeModal}
                  className="adminBtn adminBtnSecondary"
                >
                  Отмена
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}
