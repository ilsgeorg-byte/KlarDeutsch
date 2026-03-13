"use client";

import React, { useEffect, useState } from 'react';
import AdminLayout from './AdminLayout';
import { BookOpen, Users, FileText, TrendingUp, Loader2, AlertCircle } from 'lucide-react';

interface StatsData {
  words: { total: number; by_level: Record<string, number> };
  users: { total: number; active_today: number };
  diary: { total_entries: number; today: number };
  timestamp?: string;
}

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const res = await fetch('/api/admin/stats');
      if (!res.ok) throw new Error('Ошибка загрузки статистики');
      const data = await res.json();
      setStats(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <AdminLayout>
        <div className="adminLoading">
          <div className="adminLoadingSpinner" />
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      {error && (
        <div className="adminAlert adminAlertError">
          <AlertCircle size={20} />
          {error}
        </div>
      )}

      {/* Stats Grid */}
      <div className="statsGrid">
        {/* Words */}
        <div className="statCard">
          <div className="statCardIcon blue">
            <BookOpen size={28} />
          </div>
          <div className="statCardContent">
            <div className="statCardLabel">Всего слов</div>
            <div className="statCardValue">{stats?.words.total || 0}</div>
            <div className="statCardChange">
              {Object.keys(stats?.words.by_level || {}).length} уровней
            </div>
          </div>
        </div>

        {/* Users */}
        <div className="statCard">
          <div className="statCardIcon green">
            <Users size={28} />
          </div>
          <div className="statCardContent">
            <div className="statCardLabel">Пользователей</div>
            <div className="statCardValue">{stats?.users.total || 0}</div>
            <div className="statCardChange">
              {stats?.users.active_today || 0} активных сегодня
            </div>
          </div>
        </div>

        {/* Diary */}
        <div className="statCard">
          <div className="statCardIcon purple">
            <FileText size={28} />
          </div>
          <div className="statCardContent">
            <div className="statCardLabel">Записей в дневнике</div>
            <div className="statCardValue">{stats?.diary.total_entries || 0}</div>
            <div className="statCardChange">
              +{stats?.diary.today || 0} сегодня
            </div>
          </div>
        </div>

        {/* Growth */}
        <div className="statCard">
          <div className="statCardIcon orange">
            <TrendingUp size={28} />
          </div>
          <div className="statCardContent">
            <div className="statCardLabel">Активность</div>
            <div className="statCardValue">
              {stats?.users.active_today && stats?.users.total
                ? Math.round((stats.users.active_today / stats.users.total) * 100)
                : 0}%
            </div>
            <div className="statCardChange">
              онлайн сейчас
            </div>
          </div>
        </div>
      </div>

      {/* Words by Level */}
      <div className="adminCard">
        <div className="adminCardHeader">
          <h3 className="adminCardTitle">Слова по уровням</h3>
        </div>
        <table className="adminTable">
          <thead>
            <tr>
              <th>Уровень</th>
              <th>Количество</th>
              <th>Прогресс</th>
            </tr>
          </thead>
          <tbody>
            {['A1', 'A2', 'B1', 'B2', 'C1'].map((level) => {
              const count = stats?.words.by_level?.[level] || 0;
              const total = stats?.words.total || 1;
              const percentage = Math.round((count / total) * 100);
              
              return (
                <tr key={level}>
                  <td>
                    <span className="adminBadge adminBadgeBlue">{level}</span>
                  </td>
                  <td>{count}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{
                        flex: 1,
                        height: 8,
                        background: '#e2e8f0',
                        borderRadius: 4,
                        overflow: 'hidden',
                      }}>
                        <div style={{
                          width: `${percentage}%`,
                          height: '100%',
                          background: percentage > 0 ? '#3b82f6' : '#cbd5e1',
                          borderRadius: 4,
                          transition: 'width 0.3s',
                        }} />
                      </div>
                      <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                        {percentage}%
                      </span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Quick Actions */}
      <div className="adminCard">
        <div className="adminCardHeader">
          <h3 className="adminCardTitle">Быстрые действия</h3>
        </div>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <a
            href="/admin/words"
            className="adminBtn adminBtnPrimary"
          >
            <BookOpen size={18} />
            Добавить слово
          </a>
          <a
            href="/admin/users"
            className="adminBtn adminBtnSecondary"
          >
            <Users size={18} />
            Пользователи
          </a>
          <a
            href="/admin/diary"
            className="adminBtn adminBtnSecondary"
          >
            <FileText size={18} />
            Дневник
          </a>
          <a
            href="/admin/stats"
            className="adminBtn adminBtnSecondary"
          >
            <TrendingUp size={18} />
            Статистика
          </a>
        </div>
      </div>

      {/* System Info */}
      <div className="adminCard">
        <div className="adminCardHeader">
          <h3 className="adminCardTitle">Информация о системе</h3>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
          <div>
            <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: 4 }}>Версия</div>
            <div style={{ fontSize: '0.875rem', fontWeight: 600, color: '#1e293b' }}>1.0.0</div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: 4 }}>Последнее обновление</div>
            <div style={{ fontSize: '0.875rem', fontWeight: 600, color: '#1e293b' }}>
              {new Date(stats?.timestamp || Date.now()).toLocaleDateString('ru-RU')}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: 4 }}>Статус</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <div style={{
                width: 8,
                height: 8,
                background: '#22c55e',
                borderRadius: '50%',
              }} />
              <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#16a34a' }}>Работает</span>
            </div>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
}
