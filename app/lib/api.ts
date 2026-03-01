/**
 * API клиент для KlarDeutsch
 * 
 * Единый экземпляр axios с автоматической подстановкой токена авторизации
 * и обработкой ошибок
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

// Базовый URL API (берётся из переменных окружения или по умолчанию)
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api';

// Ключ для хранения токена в localStorage
const TOKEN_KEY = 'klardeutsch_token';

/**
 * Получает токен из localStorage
 */
export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Сохраняет токен в localStorage
 */
export function setToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(TOKEN_KEY, token);
}

/**
 * Удаляет токен из localStorage
 */
export function removeToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(TOKEN_KEY);
}

/**
 * Создаёт экземпляр axios с настроенными интерсепторами
 */
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 секунд
});

/**
 * Интерсептор для добавления токена авторизации к запросам
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

/**
 * Интерсептор для обработки ошибок ответов
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Токен истёк или недействителен - удаляем его
      removeToken();
      // Можно добавить редирект на страницу входа
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('auth-error'));
      }
    }
    
    console.error('API Response Error:', {
      status: error.response?.status,
      message: (error.response?.data as any)?.error || error.message,
    });
    
    return Promise.reject(error);
  }
);

/**
 * Типы для API ответов
 */
export interface ApiError {
  error: string;
  details?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  skip: number;
  limit: number;
}

/**
 * Безопасный вызов API с обработкой ошибок
 */
export async function apiCall<T>(
  fn: () => Promise<{ data: T }>
): Promise<{ data?: T; error?: ApiError }> {
  try {
    const response = await fn();
    return { data: response.data };
  } catch (error) {
    if (error instanceof AxiosError) {
      const apiError: ApiError = {
        error: 'Ошибка сервера',
        details: error.message,
      };
      
      if (error.response?.data) {
        const data = error.response.data as any;
        apiError.error = data.error || apiError.error;
        apiError.details = data.details || data.message || error.message;
      }
      
      return { error: apiError };
    }
    
    return {
      error: {
        error: 'Неизвестная ошибка',
        details: error instanceof Error ? error.message : String(error),
      },
    };
  }
}

// === API методы ===

export const authApi = {
  /**
   * Регистрация пользователя
   */
  register: (username: string, email: string, password: string) =>
    apiClient.post<{
      status: string;
      message: string;
      token: string;
      user: { id: number; username: string; email: string };
    }>('/auth/register', { username, email, password }),

  /**
   * Вход пользователя
   */
  login: (email: string, password: string) =>
    apiClient.post<{
      token: string;
      user: { id: number; username: string; email: string };
    }>('/auth/login', { email, password }),

  /**
   * Получение данных текущего пользователя
   */
  me: () =>
    apiClient.get<{ id: number; username: string; email: string }>('/auth/me'),

  /**
   * Выход (удаляет токен)
   */
  logout: () => {
    removeToken();
    return Promise.resolve();
  },
};

export const wordsApi = {
  /**
   * Получение списка слов
   */
  getWords: (params?: { level?: string; skip?: number; limit?: number }) =>
    apiClient.get<PaginatedResponse<any>>('/words', { params }),

  /**
   * Получение слова по ID
   */
  getWord: (id: number) =>
    apiClient.get<any>(`/words/${id}`),

  /**
   * Поиск слов
   */
  searchWords: (query: string, limit?: number) =>
    apiClient.get<{ data: any[]; query: string }>('/words/search', {
      params: { q: query, limit },
    }),

  /**
   * Добавление слова в избранное
   */
  addFavorite: (wordId: number) =>
    apiClient.post<{ status: string; action: string }>(
      `/words/${wordId}/favorite`
    ),

  /**
   * Удаление слова из избранного
   */
  removeFavorite: (wordId: number) =>
    apiClient.delete<{ status: string; action: string }>(
      `/words/${wordId}/favorite`
    ),

  /**
   * Получение избранных слов
   */
  getFavorites: () =>
    apiClient.get<any[]>('/favorites'),

  /**
   * Добавление пользовательского слова
   */
  addCustomWord: (data: {
    de: string;
    ru: string;
    article?: string;
    level?: string;
    topic?: string;
  }) =>
    apiClient.post<{ status: string; word_id: number }>('/words/custom', data),
};

export const trainerApi = {
  /**
   * Получение слов для тренировки
   */
  getTrainingWords: (params?: { level?: string; limit?: number }) =>
    apiClient.get<any[]>('/trainer/words', { params }),

  /**
   * Оценка слова (алгоритм SM-2)
   */
  rateWord: (wordId: number, rating: 0 | 1 | 3 | 5) =>
    apiClient.post<{ status: string }>('/trainer/rate', { word_id: wordId, rating }),

  /**
   * Получение статистики
   */
  getStats: () =>
    apiClient.get<{
      total_words: Record<string, number>;
      user_progress: Record<string, number>;
      detailed: Array<{ level: string; status: string; count: number }>;
    }>('/trainer/stats'),
};

export const diaryApi = {
  /**
   * Коррекция текста
   */
  correctText: (text: string) =>
    apiClient.post<{ corrected: string; explanation: string }>('/diary/correct', {
      text,
    }),

  /**
   * История записей
   */
  getHistory: () =>
    apiClient.get<
      Array<{
        id: number;
        original_text: string;
        corrected_text: string;
        explanation: string;
        created_at: string;
      }>
    >('/diary/history'),

  /**
   * Удаление записи
   */
  deleteEntry: (id: number) =>
    apiClient.delete<{ status: string }>(`/diary/history/${id}`),

  /**
   * Извлечение слов из коррекции
   */
  extractWords: (original: string, corrected: string) =>
    apiClient.post<Array<{ de: string; ru: string; article: string; level: string }>>(
      '/diary/extract-words',
      { original, corrected }
    ),

  /**
   * Добавление слов из дневника
   */
  addWords: (words: Array<{ de: string; ru: string; article: string; level: string }>) =>
    apiClient.post<{ status: string; added_count: number }>('/diary/add-words', words),
};

export const audioApi = {
  /**
   * Загрузка аудио
   */
  uploadAudio: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post<{ status: string; url: string; id: number }>('/audio', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  /**
   * Список аудио
   */
  listAudio: (params?: { limit?: number; offset?: number }) =>
    apiClient.get<string[]>('/list_audio', { params }),

  /**
   * Удаление аудио
   */
  deleteAudio: (filename: string) =>
    apiClient.post<{ status: string }>('/delete_audio', { filename }),
};

export default apiClient;
