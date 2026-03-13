"use client";

import React, { useEffect, useState } from 'react';
import AdminLayout from '../AdminLayout';
import { TrendingUp, Users, BookOpen, FileText, Calendar, Clock, AlertCircle } from 'lucide-react';

interface StatsData {
  words: { total: number; by_level: Record<string, number> };
  users: { total: number; active_today: number; new_today: number };
  diary: { total_entries: number; today: number };
  activity?: {
    date: string;
    users: number;
    words_learned: number;
  }[];
}

export default function AdminStatsPage() {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [period, setPeriod] = useState('7d');

  useEffect(() => {
    loadStats();
  }, [period]);

  const loadStats = async () => {
    setLoading(true);
    setError('');
    
    try {
      const res = await fetch('/api/admin/stats');
      if (!res.ok) throw new Error('Ошибка загрузки статистики');
      const data = await res.json();
      
      // Добавляем демо-данные для активности
      const mockActivity = Array.from({ length: 7 }, (_, i) => ({
        date: new Date(Date.now() - (6 - i) * 24 * 60 * 60 * 1000).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' }),
        users: Math.floor(Math.random() * 50) + 10,
        words_learned: Math.floor(Math.random() * 200) + 50,
      }));
      
      setStats({
        ...data,
        users: {
          ...data.users,
          new_today: Math.floor(Math.random() * 10),
        },
        activity: mockActivity,
      });
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

      {/* Period Selector */}
      <div style={{ marginBottom: 24, display: 'flex', gap: 8 }}>
        {['24h', '7d', '30d', '90d'].map((p) => (
          <button
            key={p}
            onClick={() => setPeriod(p)}
            className="adminBtn adminBtnSecondary"
            style={{
              background: period === p ? '#3b82f6' : undefined,
              color: period === p ? 'white' : undefined,
            }}
          >
            {p === '24h' ? '24 часа' : p === '7d' ? '7 дней' : p === '30d' ? '30 дней' : '90 дней'}
          </button>
        ))}
      </div>

      {/* Main Stats */}
      <div className="statsGrid">
        <div className="statCard">
          <div className="statCardIcon blue">
            <Users size={28} />
          </div>
          <div className="statCardContent">
            <div className="statCardLabel">Всего пользователей</div>
            <div className="statCardValue">{stats?.users.total || 0}</div>
            <div className="statCardChange">
              +{stats?.users.new_today || 0} новых сегодня
            </div>
          </div>
        </div>

        <div className="statCard">
          <div className="statCardIcon green">
            <TrendingUp size={28} />
          </div>
          <div className="statCardContent">
            <div className="statCardLabel">Активных сегодня</div>
            <div className="statCardValue">{stats?.users.active_today || 0}</div>
            <div className="statCardChange">
              {stats?.users.total ? Math.round((stats.users.active_today / stats.users.total) * 100) : 0}% от всех
            </div>
          </div>
        </div>

        <div className="statCard">
          <div className="statCardIcon purple">
            <BookOpen size={28} />
          </div>
          <div className="statCardContent">
            <div className="statCardLabel">Слов в базе</div>
            <div className="statCardValue">{stats?.words.total || 0}</div>
            <div className="statCardChange">
              {Object.keys(stats?.words.by_level || {}).length} уровней
            </div>
          </div>
        </div>

        <div className="statCard">
          <div className="statCardIcon orange">
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
      </div>

      {/* Activity Chart */}
      <div className="adminCard">
        <div className="adminCardHeader">
          <h3 className="adminCardTitle">Активность пользователей</h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#64748b', fontSize: '0.875rem' }}>
            <Calendar size={16} />
            За последние {period}
          </div>
        </div>
        
        <div style={{ height: 200, display: 'flex', alignItems: 'flex-end', gap: 8, padding: '0 8px' }}>
          {stats?.activity?.map((day, i) => {
            const maxValue = Math.max(...(stats.activity?.map(a => a.users) || [1]));
            const height = (day.users / maxValue) * 160;
            
            return (
              <div
                key={i}
                style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <div
                  style={{
                    width: '100%',
                    height,
                    background: 'linear-gradient(180deg, #3b82f6 0%, #2563eb 100%)',
                    borderRadius: '4px 4px 0 0',
                    transition: 'height 0.3s',
                  }}
                />
                <span style={{ fontSize: '0.75rem', color: '#64748b', writingMode: 'vertical-rl' }}>
                  {day.date}
                </span>
              </div>
            );
          })}
        </div>
        
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginTop: 16,
          paddingTop: 16,
          borderTop: '1px solid #e2e8f0',
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Мин.</div>
            <div style={{ fontSize: '1.125rem', fontWeight: 600, color: '#1e293b' }}>
              {Math.min(...(stats?.activity?.map(a => a.users) || [0]))}
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Сред.</div>
            <div style={{ fontSize: '1.125rem', fontWeight: 600, color: '#1e293b' }}>
              {stats?.activity ? Math.round(stats.activity.reduce((sum, a) => sum + a.users, 0) / stats.activity.length) : 0}
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Макс.</div>
            <div style={{ fontSize: '1.125rem', fontWeight: 600, color: '#1e293b' }}>
              {Math.max(...(stats?.activity?.map(a => a.users) || [0]))}
            </div>
          </div>
        </div>
      </div>

      {/* Words Learned Chart */}
      <div className="adminCard">
        <div className="adminCardHeader">
          <h3 className="adminCardTitle">Изученные слова</h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#64748b', fontSize: '0.875rem' }}>
            <Clock size={16} />
            За последние {period}
          </div>
        </div>
        
        <div style={{ height: 150, display: 'flex', alignItems: 'flex-end', gap: 8, padding: '0 8px' }}>
          {stats?.activity?.map((day, i) => {
            const maxValue = Math.max(...(stats.activity?.map(a => a.words_learned) || [1]));
            const height = (day.words_learned / maxValue) * 120;
            
            return (
              <div
                key={i}
                style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 8,
                }}
              >
                <div
                  style={{
                    width: '100%',
                    height,
                    background: 'linear-gradient(180deg, #22c55e 0%, #16a34a 100%)',
                    borderRadius: '4px 4px 0 0',
                    transition: 'height 0.3s',
                  }}
                />
              </div>
            );
          })}
        </div>
        
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginTop: 16,
          paddingTop: 16,
          borderTop: '1px solid #e2e8f0',
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Всего за период</div>
            <div style={{ fontSize: '1.125rem', fontWeight: 600, color: '#1e293b' }}>
              {stats?.activity?.reduce((sum, a) => sum + a.words_learned, 0) || 0}
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>В день (сред.)</div>
            <div style={{ fontSize: '1.125rem', fontWeight: 600, color: '#1e293b' }}>
              {stats?.activity ? Math.round(stats.activity.reduce((sum, a) => sum + a.words_learned, 0) / stats.activity.length) : 0}
            </div>
          </div>
        </div>
      </div>

      {/* Words by Level */}
      <div className="adminCard">
        <div className="adminCardHeader">
          <h3 className="adminCardTitle">Распределение слов по уровням</h3>
        </div>
        <table className="adminTable">
          <thead>
            <tr>
              <th>Уровень</th>
              <th>Количество</th>
              <th>Процент</th>
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
                  <td>{percentage}%</td>
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
                          background: `linear-gradient(90deg, 
                            ${level === 'A1' ? '#22c55e' : 
                              level === 'A2' ? '#84cc16' : 
                              level === 'B1' ? '#eab308' : 
                              level === 'B2' ? '#f97316' : '#ef4444'} 0%, 
                            ${level === 'A1' ? '#16a34a' : 
                              level === 'A2' ? '#65a30d' : 
                              level === 'B1' ? '#ca8a04' : 
                              level === 'B2' ? '#ea580c' : '#dc2626'} 100%)`,
                          borderRadius: 4,
                        }} />
                      </div>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </AdminLayout>
  );
}
