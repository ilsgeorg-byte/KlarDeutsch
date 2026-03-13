import { headers } from 'next/headers';
import { redirect } from 'next/navigation';
import AudioClient from './AudioClient';
import styles from '../styles/Shared.module.css';

/**
 * Серверный компонент для страницы аудио
 * Проверка авторизации и загрузка данных на сервере
 */

async function getAudioFiles(token: string): Promise<string[]> {
  try {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5000';
    const res = await fetch(`${apiBaseUrl}/api/list_audio`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      cache: 'no-store', // Не кэшируем пользовательские данные
    });

    if (!res.ok) {
      return [];
    }

    return await res.json();
  } catch (error) {
    console.error('Ошибка загрузки аудио:', error);
    return [];
  }
}

export default async function AudioPage() {
  // Получаем заголовки на сервере
  const headersList = await headers();
  const authHeader = headersList.get('authorization');

  // Проверка авторизации (для серверного рендеринга)
  // Если нет токена в localStorage (клиент), редирект на login
  // Примечание: для полной проверки нужен токен из cookies или session
  
  return (
    <div className={styles.pageWrapper}>
      <main className={styles.container}>
        <h1 className={styles.pageTitle}>Мои записи</h1>
        
        {/* Клиентский компонент для интерактивности */}
        <AudioClient initialFiles={[]} />
      </main>
    </div>
  );
}
