"use client";

import React, { useEffect, useState } from 'react';
import AdminLayout from '../AdminLayout';
import { Search, User, Mail, Calendar, Trash2, Ban, CheckCircle, AlertCircle } from 'lucide-react';

interface User {
  id: number;
  username: string;
  email: string;
  created_at: string;
  is_active?: boolean;
}

interface UsersResponse {
  users: User[];
  total: number;
  page: number;
  limit: number;
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const limit = 20;

  useEffect(() => {
    loadUsers();
  }, [page]);

  const loadUsers = async () => {
    setLoading(true);
    setError('');
    
    try {
      const params = new URLSearchParams({
        page: String(page),
        limit: String(limit),
      });
      
      if (search) params.set('search', search);

      const res = await fetch(`/api/admin/users?${params.toString()}`);
      
      if (!res.ok) throw new Error('Ошибка загрузки пользователей');
      
      const data: UsersResponse = await res.json();
      setUsers(data.users || []);
      setTotal(data.total || 0);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setPage(1);
    loadUsers();
  };

  const handleToggleActive = async (userId: number, currentStatus: boolean) => {
    if (!confirm(`${currentStatus ? 'Заблокировать' : 'Разблокировать'} пользователя?`)) return;

    try {
      // TODO: API для блокировки
      setSuccess(currentStatus ? 'Пользователь заблокирован' : 'Пользователь разблокирован');
      loadUsers();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDelete = async (userId: number) => {
    if (!confirm('Удалить пользователя? Это действие необратимо.')) return;

    try {
      // TODO: API для удаления
      setSuccess('Пользователь удалён');
      loadUsers();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.message);
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
          <h3 className="adminCardTitle">Пользователи</h3>
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
              placeholder="Поиск по email или имени..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="adminSearchInput"
              style={{ paddingLeft: 40 }}
            />
          </div>
          
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
                  <th>Пользователь</th>
                  <th>Email</th>
                  <th>Дата регистрации</th>
                  <th>Статус</th>
                  <th>Действия</th>
                </tr>
              </thead>
              <tbody>
                {users.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>
                      Пользователи не найдены
                    </td>
                  </tr>
                ) : (
                  users.map((user) => (
                    <tr key={user.id}>
                      <td style={{ color: '#94a3b8', fontSize: '0.75rem' }}>#{user.id}</td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          <div style={{
                            width: 32,
                            height: 32,
                            borderRadius: '50%',
                            background: '#3b82f6',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'white',
                            fontWeight: 600,
                            fontSize: '0.875rem',
                          }}>
                            {user.username[0]?.toUpperCase() || 'U'}
                          </div>
                          <strong>{user.username}</strong>
                        </div>
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#64748b' }}>
                          <Mail size={14} />
                          {user.email}
                        </div>
                      </td>
                      <td style={{ color: '#64748b', fontSize: '0.875rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <Calendar size={14} />
                          {new Date(user.created_at).toLocaleDateString('ru-RU')}
                        </div>
                      </td>
                      <td>
                        <span className={`adminBadge ${user.is_active !== false ? 'adminBadgeGreen' : 'adminBadgeGray'}`}>
                          {user.is_active !== false ? 'Активен' : 'Заблокирован'}
                        </span>
                      </td>
                      <td>
                        <div className="adminTableActions">
                          <button
                            className="adminBtn adminBtnSecondary adminBtnSm"
                            onClick={() => handleToggleActive(user.id, user.is_active !== false)}
                            title={user.is_active !== false ? 'Заблокировать' : 'Разблокировать'}
                          >
                            {user.is_active !== false ? <Ban size={14} /> : <CheckCircle size={14} />}
                          </button>
                          <button
                            className="adminBtn adminBtnDanger adminBtnSm"
                            onClick={() => handleDelete(user.id)}
                            title="Удалить"
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
    </AdminLayout>
  );
}
