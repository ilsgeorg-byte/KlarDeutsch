"use client";

import React, { useEffect, useState } from 'react';
import AdminLayout from '../AdminLayout';
import { FileText, Search, Eye, Trash2, AlertCircle, CheckCircle } from 'lucide-react';

interface DiaryEntry {
  id: number;
  user_id: number;
  username: string;
  original_text: string;
  corrected_text: string;
  explanation: string;
  created_at: string;
}

export default function AdminDiaryPage() {
  const [entries, setEntries] = useState<DiaryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const limit = 20;

  // Modal
  const [selectedEntry, setSelectedEntry] = useState<DiaryEntry | null>(null);

  useEffect(() => {
    loadEntries();
  }, [page]);

  const loadEntries = async () => {
    setLoading(true);
    setError('');
    
    try {
      // TODO: API для получения записей дневника
      // Заглушка для демонстрации
      setEntries([]);
      setTotal(0);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (entryId: number) => {
    if (!confirm('Удалить эту запись?')) return;

    try {
      // TODO: API для удаления
      setSuccess('Запись удалена');
      loadEntries();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.message);
    }
  };

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
          <h3 className="adminCardTitle">Дневник пользователей</h3>
          <div style={{ fontSize: '0.875rem', color: '#64748b' }}>
            Всего: <strong>{total}</strong>
          </div>
        </div>

        {/* Search */}
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
              placeholder="Поиск записей..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="adminSearchInput"
              style={{ paddingLeft: 40 }}
            />
          </div>
        </div>

        {/* Info */}
        <div style={{
          background: '#f8fafc',
          border: '1px solid #e2e8f0',
          borderRadius: 8,
          padding: 16,
          marginBottom: 20,
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          color: '#475569',
          fontSize: '0.875rem',
        }}>
          <FileText size={20} />
          <span>
            Здесь будет отображаться дневник пользователей для модерации.
            API для дневника находится в разработке.
          </span>
        </div>

        {/* Table */}
        {loading ? (
          <div className="adminLoading">
            <div className="adminLoadingSpinner" />
          </div>
        ) : entries.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 60, color: '#94a3b8' }}>
            <FileText size={48} style={{ margin: '0 auto 16px', opacity: 0.5 }} />
            <p style={{ margin: 0 }}>Записей не найдено</p>
          </div>
        ) : (
          <>
            <table className="adminTable">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Пользователь</th>
                  <th>Оригинал</th>
                  <th>Исправлено</th>
                  <th>Дата</th>
                  <th>Действия</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => (
                  <tr key={entry.id}>
                    <td style={{ color: '#94a3b8', fontSize: '0.75rem' }}>#{entry.id}</td>
                    <td>{entry.username}</td>
                    <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {entry.original_text}
                    </td>
                    <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {entry.corrected_text}
                    </td>
                    <td style={{ color: '#64748b', fontSize: '0.875rem' }}>
                      {new Date(entry.created_at).toLocaleDateString('ru-RU')}
                    </td>
                    <td>
                      <div className="adminTableActions">
                        <button
                          className="adminBtn adminBtnSecondary adminBtnSm"
                          onClick={() => setSelectedEntry(entry)}
                        >
                          <Eye size={14} />
                        </button>
                        <button
                          className="adminBtn adminBtnDanger adminBtnSm"
                          onClick={() => handleDelete(entry.id)}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </div>

      {/* View Modal */}
      {selectedEntry && (
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
          onClick={() => setSelectedEntry(null)}
        >
          <div
            style={{
              background: 'white',
              borderRadius: 12,
              padding: 32,
              width: '100%',
              maxWidth: 600,
              maxHeight: '90vh',
              overflow: 'auto',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: 24 }}>
              Запись дневника #{selectedEntry.id}
            </h3>
            
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: 8 }}>Пользователь</div>
              <div style={{ fontSize: '0.875rem', fontWeight: 600 }}>{selectedEntry.username}</div>
            </div>
            
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: 8 }}>Оригинальный текст</div>
              <div style={{
                background: '#fef3c7',
                border: '1px solid #fde68a',
                borderRadius: 8,
                padding: 16,
                fontSize: '0.875rem',
                lineHeight: 1.6,
              }}>
                {selectedEntry.original_text}
              </div>
            </div>
            
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: 8 }}>Исправленный текст</div>
              <div style={{
                background: '#dcfce7',
                border: '1px solid #bbf7d0',
                borderRadius: 8,
                padding: 16,
                fontSize: '0.875rem',
                lineHeight: 1.6,
              }}>
                {selectedEntry.corrected_text}
              </div>
            </div>
            
            {selectedEntry.explanation && (
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: 8 }}>Объяснение</div>
                <div style={{
                  background: '#f3f4f6',
                  border: '1px solid #e5e7eb',
                  borderRadius: 8,
                  padding: 16,
                  fontSize: '0.875rem',
                  lineHeight: 1.6,
                }}>
                  {selectedEntry.explanation}
                </div>
              </div>
            )}
            
            <div style={{ display: 'flex', gap: 12 }}>
              <button
                className="adminBtn adminBtnSecondary"
                onClick={() => setSelectedEntry(null)}
                style={{ flex: 1 }}
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}
