"use client";

import React, { useEffect, useState } from 'react';
import AdminLayout from './AdminLayout';
import { BookOpen, Users, FileText, TrendingUp, Loader2, AlertCircle, CheckCircle, XCircle, RefreshCw, Trash2 } from 'lucide-react';

interface StatsData {
  words: { total: number; by_level: Record<string, number> };
  users: { total: number; active_today: number };
  diary: { total_entries: number; today: number };
  timestamp?: string;
}

interface CheckStatus {
  running: boolean;
  lastRun: string | null;
  totalChecked: number;
  errorsFound: number;
  translationsAdded: number;
  examplesAdded: number;
  pluralAdded: number;
  synonymsAdded: number;
  antonymsAdded: number;
  collocationsAdded: number;
  greetingConstructions: number;
  message: string;
  progress: { current: number; total: number };
}

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [checkStatus, setCheckStatus] = useState<CheckStatus | null>(null);
  const [checking, setChecking] = useState(false);
  const [checkLimit, setCheckLimit] = useState(500);
  
  // Состояние для конструкций приветствий
  const [greetings, setGreetings] = useState<any[]>([]);
  const [loadingGreetings, setLoadingGreetings] = useState(false);

  useEffect(() => {
    loadStats();
    loadCheckStatus();
    loadGreetings();

    // Обновляем статус проверки каждые 2 секунды если запущена
    const interval = setInterval(() => {
      if (checkStatus?.running) {
        loadCheckStatus();
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [checkStatus?.running]);

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

  const loadCheckStatus = async () => {
    try {
      const res = await fetch('/api/admin/check-words');
      if (!res.ok) throw new Error('Ошибка загрузки статуса проверки');
      const data = await res.json();
      setCheckStatus(data);
    } catch (err: any) {
      console.error('Load check status error:', err);
    }
  };

  const loadGreetings = async () => {
    try {
      setLoadingGreetings(true);
      const res = await fetch('/api/admin/greetings');
      if (!res.ok) throw new Error('Ошибка загрузки конструкций');
      const data = await res.json();
      setGreetings(data.words || []);
    } catch (err: any) {
      console.error('Load greetings error:', err);
    } finally {
      setLoadingGreetings(false);
    }
  };

  const deleteGreetings = async () => {
    if (!confirm(`Удалить ${greetings.length} конструкций приветствий? Это действие необратимо!`)) {
      return;
    }
    
    try {
      const res = await fetch('/api/admin/greetings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ deleteAll: true }),
      });
      
      if (!res.ok) throw new Error('Ошибка удаления');
      
      const data = await res.json();
      alert(`Удалено ${data.deletedCount} конструкций`);
      setGreetings([]);
      loadGreetings(); // Обновить список
    } catch (err: any) {
      setError(err.message);
    }
  };

  const startCheck = async () => {
    setChecking(true);
    try {
      const res = await fetch('/api/admin/check-words', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ limit: checkLimit }),
      });
      
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.error || 'Ошибка запуска проверки');
      }
      
      const data = await res.json();
      if (data.status === 'already_running') {
        setError('Проверка уже запущена');
      } else {
        setChecking(false);
        loadCheckStatus();
      }
    } catch (err: any) {
      setError(err.message);
      setChecking(false);
    }
  };

  const resetCheck = async (all = false) => {
    if (!confirm(all ? 'Сбросить ВСЕ проверенные слова?' : 'Сбросить последние 500 проверенных слов?')) {
      return;
    }
    
    try {
      const res = await fetch('/api/admin/check-words', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ all }),
      });
      
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.error || 'Ошибка сброса');
      }
      
      const data = await res.json();
      setCheckStatus(data);
      loadCheckStatus();
    } catch (err: any) {
      setError(err.message);
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

      {/* AI Проверка слов */}
      <div className="adminCard">
        <div className="adminCardHeader">
          <h3 className="adminCardTitle">🤖 AI проверка слов</h3>
        </div>
        <div style={{ marginBottom: 16 }}>
          <p style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: 12 }}>
            Проверка слов через ИИ: поиск ошибок, добавление переводов, удаление конструкций приветствий
          </p>
          
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 16, flexWrap: 'wrap' }}>
            <select
              value={checkLimit}
              onChange={(e) => setCheckLimit(Number(e.target.value))}
              className="adminInput"
              style={{ width: 'auto', minWidth: 150 }}
              disabled={checking || checkStatus?.running}
            >
              <option value={100}>100 слов</option>
              <option value={500}>500 слов</option>
              <option value={1000}>1000 слов</option>
              <option value={5000}>5000 слов</option>
            </select>

            <button
              onClick={startCheck}
              disabled={checking || checkStatus?.running}
              className="adminBtn adminBtnPrimary"
              style={{ opacity: (checking || checkStatus?.running) ? 0.6 : 1 }}
            >
              {checking || checkStatus?.running ? (
                <>
                  <RefreshCw size={18} className="animate-spin" />
                  Проверка...
                </>
              ) : (
                <>
                  <CheckCircle size={18} />
                  Запустить проверку
                </>
              )}
            </button>

            <button
              onClick={() => resetCheck(false)}
              disabled={checking || checkStatus?.running}
              className="adminBtn adminBtnSecondary"
              style={{ opacity: (checking || checkStatus?.running) ? 0.6 : 1 }}
            >
              <Trash2 size={18} />
              Сбросить 500
            </button>

            <button
              onClick={() => resetCheck(true)}
              disabled={checking || checkStatus?.running}
              className="adminBtn adminBtnDanger"
              style={{ opacity: (checking || checkStatus?.running) ? 0.6 : 1 }}
            >
              <Trash2 size={18} />
              Сбросить все
            </button>
          </div>

          {checkStatus && (
            <div style={{
              padding: 16,
              background: checkStatus.running ? '#eff6ff' : '#f8fafc',
              borderRadius: 8,
              border: `1px solid ${checkStatus.running ? '#3b82f6' : '#e2e8f0'}`,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                {checkStatus.running ? (
                  <RefreshCw size={20} className="animate-spin" style={{ color: '#3b82f6' }} />
                ) : checkStatus.errorsFound > 0 ? (
                  <AlertCircle size={20} style={{ color: '#f59e0b' }} />
                ) : (
                  <CheckCircle size={20} style={{ color: '#22c55e' }} />
                )}
                <span style={{ fontWeight: 600, color: '#1e293b' }}>{checkStatus.message}</span>
              </div>

              {checkStatus.lastRun && (
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))',
                  gap: 12,
                }}>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Проверено</div>
                    <div style={{ fontSize: '1.125rem', fontWeight: 700, color: '#1e293b' }}>
                      {checkStatus.totalChecked}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Ошибки</div>
                    <div style={{ fontSize: '1.125rem', fontWeight: 700, color: checkStatus.errorsFound > 0 ? '#dc2626' : '#22c55e' }}>
                      {checkStatus.errorsFound}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Переводов</div>
                    <div style={{ fontSize: '1.125rem', fontWeight: 700, color: '#2563eb' }}>
                      +{checkStatus.translationsAdded}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Примеров</div>
                    <div style={{ fontSize: '1.125rem', fontWeight: 700, color: '#16a34a' }}>
                      +{checkStatus.examplesAdded}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Мн.число</div>
                    <div style={{ fontSize: '1.125rem', fontWeight: 700, color: '#ea580c' }}>
                      +{checkStatus.pluralAdded}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Синонимы</div>
                    <div style={{ fontSize: '1.125rem', fontWeight: 700, color: '#9333ea' }}>
                      +{checkStatus.synonymsAdded}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Антонимы</div>
                    <div style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0891b2' }}>
                      +{checkStatus.antonymsAdded}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Коллокации</div>
                    <div style={{ fontSize: '1.125rem', fontWeight: 700, color: '#db2777' }}>
                      +{checkStatus.collocationsAdded}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Приветствия</div>
                    <div style={{ fontSize: '1.125rem', fontWeight: 700, color: '#f59e0b' }}>
                      {checkStatus.greetingConstructions}
                    </div>
                  </div>
                </div>
              )}

              {checkStatus.lastRun && (
                <div style={{ marginTop: 12, fontSize: '0.75rem', color: '#64748b' }}>
                  Последняя проверка: {new Date(checkStatus.lastRun).toLocaleString('ru-RU')}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Конструкции приветствий */}
      <div className="adminCard">
        <div className="adminCardHeader">
          <h3 className="adminCardTitle">⚠️ Конструкции приветствий</h3>
        </div>
        <div style={{ marginBottom: 16 }}>
          <p style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: 12 }}>
            Эти фразы не являются отдельными словами и должны быть удалены из базы
          </p>

          {loadingGreetings ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#64748b' }}>
              <RefreshCw size={16} className="animate-spin" />
              Загрузка...
            </div>
          ) : greetings.length > 0 ? (
            <>
              <div style={{ 
                padding: 12, 
                background: '#fef3c7', 
                borderRadius: 8, 
                border: '1px solid #fcd34d',
                marginBottom: 12,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#92400e' }}>
                  <AlertCircle size={20} />
                  <span style={{ fontWeight: 600 }}>Найдено {greetings.length} конструкций для удаления</span>
                </div>
              </div>

              <div style={{ 
                maxHeight: 300, 
                overflow: 'auto', 
                marginBottom: 12,
                border: '1px solid #e2e8f0',
                borderRadius: 8,
              }}>
                <table className="adminTable" style={{ marginBottom: 0 }}>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Немецкий</th>
                      <th>Русский</th>
                      <th>Уровень</th>
                    </tr>
                  </thead>
                  <tbody>
                    {greetings.slice(0, 10).map((word) => (
                      <tr key={word.id}>
                        <td>#{word.id}</td>
                        <td style={{ fontWeight: 600, color: '#dc2626' }}>{word.de}</td>
                        <td>{word.ru}</td>
                        <td><span className="adminBadge adminBadgeBlue">{word.level}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {greetings.length > 10 && (
                  <div style={{ padding: 8, textAlign: 'center', color: '#64748b', fontSize: '0.75rem' }}>
                    Показано 10 из {greetings.length}
                  </div>
                )}
              </div>

              <button
                onClick={deleteGreetings}
                className="adminBtn adminBtnDanger"
              >
                <Trash2 size={18} />
                Удалить все {greetings.length} конструкций
              </button>
            </>
          ) : (
            <div style={{ 
              padding: 16, 
              background: '#f0fdf4', 
              borderRadius: 8, 
              border: '1px solid #86efac',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}>
              <CheckCircle size={20} style={{ color: '#16a34a' }} />
              <span style={{ fontWeight: 600, color: '#16a34a' }}>Конструкции не найдены</span>
            </div>
          )}
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
