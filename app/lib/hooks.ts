/**
 * React хуки для работы с API через SWR
 * 
 * SWR обеспечивает:
 * - Автоматическое кэширование
 * - Повторные запросы при фокусе
 * - Оптимистичные обновления
 * - Дедупликация запросов
 */

import useSWR, { SWRConfiguration, Key } from 'swr';
import {
  wordsApi,
  trainerApi,
  diaryApi,
  audioApi,
  apiCall,
  PaginatedResponse,
} from '../lib/api';

// === Общие типы ===

interface ApiError {
  error: string;
  details?: string;
}

// === Хуки для слов ===

/**
 * Получение списка слов с пагинацией
 */
export function useWords(
  level: string = 'A1',
  skip: number = 0,
  limit: number = 20
) {
  const key = `/words?level=${level}&skip=${skip}&limit=${limit}`;
  
  const { data, error, isLoading, mutate } = useSWR(
    key,
    async () => {
      const result = await apiCall(() => wordsApi.getWords({ level, skip, limit }));
      if (result.error) throw new Error(result.error.error);
      return result.data;
    },
    {
      revalidateOnFocus: false,
      dedupingInterval: 5000,
    }
  );

  return {
    words: data?.data || [],
    total: data?.total || 0,
    isLoading,
    isError: error,
    mutate,
  };
}

/**
 * Поиск слов
 */
export function useWordSearch(query: string, limit: number = 20) {
  const key = query ? `/words/search?q=${query}&limit=${limit}` : null;
  
  const { data, error, isLoading, mutate } = useSWR(
    key,
    async () => {
      const result = await apiCall(() => wordsApi.searchWords(query, limit));
      if (result.error) throw new Error(result.error.error);
      return result.data;
    },
    {
      dedupingInterval: 2000,
    }
  );

  return {
    results: data?.data || [],
    isLoading,
    isError: error,
    mutate,
  };
}

/**
 * Избранные слова
 */
export function useFavorites() {
  const { data, error, isLoading, mutate } = useSWR(
    '/favorites',
    async () => {
      const result = await apiCall(() => wordsApi.getFavorites());
      if (result.error) throw new Error(result.error.error);
      return result.data;
    }
  );

  return {
    favorites: data || [],
    isLoading,
    isError: error,
    mutate,
  };
}

// === Хуки для тренера ===

/**
 * Слова для тренировки
 */
export function useTrainingWords(level: string = 'A1', limit: number = 10) {
  const key = `/trainer/words?level=${level}&limit=${limit}`;
  
  const { data, error, isLoading, mutate } = useSWR(
    key,
    async () => {
      const result = await apiCall(() => trainerApi.getTrainingWords({ level, limit }));
      if (result.error) throw new Error(result.error.error);
      return result.data;
    },
    {
      revalidateOnFocus: false,
    }
  );

  return {
    words: data || [],
    isLoading,
    isError: error,
    mutate,
  };
}

/**
 * Статистика обучения
 */
export function useStats() {
  const { data, error, isLoading, mutate } = useSWR(
    '/trainer/stats',
    async () => {
      const result = await apiCall(() => trainerApi.getStats());
      if (result.error) throw new Error(result.error.error);
      return result.data;
    },
    {
      refreshInterval: 30000, // Обновлять каждые 30 секунд
    }
  );

  return {
    stats: data,
    isLoading,
    isError: error,
    mutate,
  };
}

// === Хуки для дневника ===

/**
 * История записей дневника
 */
export function useDiaryHistory() {
  const { data, error, isLoading, mutate } = useSWR(
    '/diary/history',
    async () => {
      const result = await apiCall(() => diaryApi.getHistory());
      if (result.error) throw new Error(result.error.error);
      return result.data;
    }
  );

  return {
    entries: data || [],
    isLoading,
    isError: error,
    mutate,
  };
}

// === Хуки для аудио ===

/**
 * Список аудио записей
 */
export function useAudioList(limit: number = 20) {
  const { data, error, isLoading, mutate } = useSWR(
    `/audio/list?limit=${limit}`,
    async () => {
      const result = await apiCall(() => audioApi.listAudio({ limit }));
      if (result.error) throw new Error(result.error.error);
      return result.data;
    }
  );

  return {
    files: data || [],
    isLoading,
    isError: error,
    mutate,
  };
}

// === Хелпер для мутаций ===

/**
 * Хук для мутаций (создание, обновление, удаление)
 */
export function useMutation<T, A extends any[]>(
  mutationFn: (...args: A) => Promise<{ data?: T; error?: ApiError }>,
  onSuccess?: (data: T) => void,
  onError?: (error: ApiError) => void
) {
  const mutate = async (...args: A): Promise<T | null> => {
    try {
      const result = await mutationFn(...args);
      if (result.error) {
        onError?.(result.error);
        return null;
      }
      if (result.data) {
        onSuccess?.(result.data);
        return result.data;
      }
      return null;
    } catch (error) {
      const apiError: ApiError = {
        error: 'Ошибка выполнения операции',
        details: error instanceof Error ? error.message : String(error),
      };
      onError?.(apiError);
      return null;
    }
  };

  return { mutate };
}
