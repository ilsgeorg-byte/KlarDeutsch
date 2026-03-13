"use client";

import React, { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Lock, Mail, Loader2, AlertCircle } from 'lucide-react';

function AdminLoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirect = searchParams?.get('redirect') || '/admin';
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await fetch('/api/admin/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || 'Ошибка входа');
      }

      // Сохраняем данные пользователя
      localStorage.setItem('admin_user', JSON.stringify(data.user));
      
      // Редирект
      router.push(redirect);
    } catch (err: any) {
      setError(err.message || 'Неверный email или пароль');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: 20,
    }}>
      <div style={{
        background: 'white',
        borderRadius: 16,
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
        padding: 40,
        width: '100%',
        maxWidth: 420,
      }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            width: 64,
            height: 64,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderRadius: 16,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px',
          }}>
            <Lock size={32} color="white" />
          </div>
          <h1 style={{
            fontSize: '1.5rem',
            fontWeight: 700,
            color: '#1e293b',
            margin: 0,
          }}>
            Admin Panel
          </h1>
          <p style={{
            fontSize: '0.875rem',
            color: '#64748b',
            marginTop: 8,
          }}>
            KlarDeutsch - Вход в систему
          </p>
        </div>

        {error && (
          <div style={{
            background: '#fee2e2',
            border: '1px solid #fecaca',
            borderRadius: 8,
            padding: 12,
            marginBottom: 20,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            color: '#991b1b',
            fontSize: '0.875rem',
          }}>
            <AlertCircle size={18} />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 20 }}>
            <label style={{
              display: 'block',
              fontSize: '0.875rem',
              fontWeight: 500,
              color: '#374151',
              marginBottom: 8,
            }}>
              Email
            </label>
            <div style={{ position: 'relative' }}>
              <Mail
                size={20}
                style={{
                  position: 'absolute',
                  left: 12,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: '#9ca3af',
                }}
              />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@klardeutsch.com"
                required
                style={{
                  width: '100%',
                  padding: '12px 12px 12px 44px',
                  border: '1px solid #d1d5db',
                  borderRadius: 8,
                  fontSize: '0.875rem',
                  boxSizing: 'border-box',
                }}
              />
            </div>
          </div>

          <div style={{ marginBottom: 24 }}>
            <label style={{
              display: 'block',
              fontSize: '0.875rem',
              fontWeight: 500,
              color: '#374151',
              marginBottom: 8,
            }}>
              Пароль
            </label>
            <div style={{ position: 'relative' }}>
              <Lock
                size={20}
                style={{
                  position: 'absolute',
                  left: 12,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: '#9ca3af',
                }}
              />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                style={{
                  width: '100%',
                  padding: '12px 12px 12px 44px',
                  border: '1px solid #d1d5db',
                  borderRadius: 8,
                  fontSize: '0.875rem',
                  boxSizing: 'border-box',
                }}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: 14,
              background: loading ? '#93c5fd' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
              borderRadius: 8,
              fontSize: '0.875rem',
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
            }}
          >
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Вход...
              </>
            ) : (
              'Войти'
            )}
          </button>
        </form>

        <div style={{
          marginTop: 24,
          paddingTop: 24,
          borderTop: '1px solid #e5e7eb',
          textAlign: 'center',
        }}>
          <a
            href="/"
            style={{
              fontSize: '0.875rem',
              color: '#6b7280',
              textDecoration: 'none',
            }}
          >
            ← Вернуться на главную
          </a>
        </div>
      </div>
    </div>
  );
}

export default function AdminLoginPage() {
  return (
    <Suspense fallback={<div>Загрузка...</div>}>
      <AdminLoginForm />
    </Suspense>
  );
}
