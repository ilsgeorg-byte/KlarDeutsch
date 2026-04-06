/**
 * React хуки для работы с API через SWR
 *
 * SWR обеспечивает:
 * - Автоматическое кэширование
 * - Повторные запросы при фокусе
 * - Оптимистичные обновления
 * - Дедупликация запросов
 *
 * Примеры использования см. в docs/api_usage_en.md или docs/api_usage_ru.md
 */

import useSWR, { SWRConfiguration, mutate as globalMutate } from 'swr';
import { useCallback } from 'react';
import {
  wordsApi,
  trainerApi,
  diaryApi,
  audioApi,
  adminApi,
  topicsApi,
  apiCall,
  PaginatedResponse,
} from './api';

// === Общие типы ===

export interface Word {
  id: number;
  de: string;
  ru: string;
  article?: string;
  plural?: string;
  verb_forms?: string;
  level?: string;
  topic?: string;
  example_de?: string;
  example_ru?: string;
  synonyms?: string;
  antonyms?: string;
  collocations?: string;
  examples?: Array<{ de: string; ru: string }>;
  is_favorite?: boolean;
  ef?: number;
  interval?: number;
  repetitions?: number;
  next_review?: string;
  status?: string;
}

export interface ApiError {
  error: string;
  details?: string;
}

// === Хуки для слов ===

/**
 * Получение списка слов с пагинацией
 * 
 * Пример:
 * const { words, total, isLoading, mutate } = useWords('A1', 0, 20);
 */
export function useWords(level: string = 'A1', skip: number = 0, limit: number = 20) {
  const key = level ? `/words?level=${level}&skip=${skip}&limit=${limit}` : null;

  const { data, error, isLoading, mutate } = useSWR(
    key,
    async () => {
      const result = await apiCall(() => wordsApi.getWords({ level, skip, limit }));
      if (result.error) throw new Error(result.error.details || result.error.error);
      return result.data;
    },
    {
      revalidateOnFocus: false,
      dedupingInterval: 5000,
    }
  );

  return {
    words: (data?.data || []) as Word[],
    total: data?.total || 0,
    isLoading,
    error: error as Error | null,
    mutate,
  };
}

/**
 * Получение слов по теме
 * 
 * Пример:
 * const { words, total, isLoading } = useWordsByTopic('travel', 0, 20);
 */
export function useWordsByTopic(topic: string, skip: number = 0, limit: number = 20) {
  const key = topic ? `/words/by-topic/${topic}?skip=${skip}&limit=${limit}` : null;

  const { data, error, isLoading, mutate } = useSWR(
    key,
    async () => {
      const result = await apiCall(() => wordsApi.getWordsByTopic(topic, { skip, limit }));
      if (result.error) throw new Error(result.error.details || result.error.error);
      return result.data;
    },
    {
      revalidateOnFocus: false,
      dedupingInterval: 5000,
    }
  );

  return {
    words: (data?.data || []) as Word[],
    total: data?.total || 0,
    isLoading,
    error: error as Error | null,
    mutate,
  };
}

/**
 * Поиск слов
 * 
 * Пример:
 * const { results, isLoading } = useWordSearch('Haus', 10);
 */
export function useWordSearch(query: string, limit: number = 20) {
  const key = query ? `/words/search?q=${query}&limit=${limit}` : null;

  const { data, error, isLoading, mutate } = useSWR(
    key,
    async () => {
      const result = await apiCall(() => wordsApi.searchWords(query, limit));
      if (result.error) throw new Error(result.error.details || result.error.error);
      return result.data;
    },
    {
      dedupingInterval: 2000,
    }
  );

  return {
    results: (data?.data || []) as Word[],
    isLoading,
    error: error as Error | null,
    mutate,
  };
}

/**
 * Избранные слова
 * 
 * Пример:
 * const { favorites, isLoading, mutate } = useFavorites();
 */
export function useFavorites() {
  const { data, error, isLoading, mutate } = useSWR(
    '/favorites',
    async () => {
      const result = await apiCall(() => wordsApi.getFavorites());
      if (result.error) throw new Error(result.error.details || result.error.error);
      return result.data;
    }
  );

  return {
    favorites: (data || []) as Word[],
    isLoading,
    error: error as Error | null,
    mutate,
  };
}

// === Хуки для тренера ===

/**
 * Слова для тренировки
 * 
 * Пример:
 * const { words, isLoading, mutate } = useTrainingWords('A1', 10);
 */
export function useTrainingWords(level: string = 'A1', limit: number = 10) {
  const key = `/trainer/words?level=${level}&limit=${limit}`;

  const { data, error, isLoading, mutate } = useSWR(
    key,
    async () => {
      const result = await apiCall(() => trainerApi.getTrainingWords({ level, limit }));
      if (result.error) throw new Error(result.error.details || result.error.error);
      return result.data;
    },
    {
      revalidateOnFocus: false,
    }
  );

  return {
    words: (data || []) as Word[],
    isLoading,
    error: error as Error | null,
    mutate,
  };
}

/**
 * Статистика обучения
 * 
 * Пример:
 * const { stats, isLoading } = useStats();
 */
export function useStats() {
  const { data, error, isLoading, mutate } = useSWR(
    '/trainer/stats',
    async () => {
      const result = await apiCall(() => trainerApi.getStats());
      if (result.error) throw new Error(result.error.details || result.error.error);
      return result.data;
    },
    {
      refreshInterval: 30000, // Обновлять каждые 30 секунд
    }
  );

  return {
    stats: data,
    isLoading,
    error: error as Error | null,
    mutate,
  };
}

// === Хуки для дневника ===

/**
 * История записей дневника
 * 
 * Пример:
 * const { entries, isLoading, mutate } = useDiaryHistory();
 */
export function useDiaryHistory() {
  const { data, error, isLoading, mutate } = useSWR(
    '/diary/history',
    async () => {
      const result = await apiCall(() => diaryApi.getHistory());
      if (result.error) throw new Error(result.error.details || result.error.error);
      return result.data;
    }
  );

  return {
    entries: data || [],
    isLoading,
    error: error as Error | null,
    mutate,
  };
}

// === Хуки для аудио ===

/**
 * Список аудио записей
 * 
 * Пример:
 * const { files, isLoading } = useAudioList(20);
 */
export function useAudioList(limit: number = 20) {
  const key = `/audio/list?limit=${limit}`;

  const { data, error, isLoading, mutate } = useSWR(
    key,
    async () => {
      const result = await apiCall(() => audioApi.listAudio({ limit }));
      if (result.error) throw new Error(result.error.details || result.error.error);
      return result.data;
    }
  );

  return {
    files: data || [],
    isLoading,
    error: error as Error | null,
    mutate,
  };
}

// === Хуки для тем ===

/**
 * Все темы
 * 
 * Пример:
 * const { topics, isLoading } = useTopics();
 */
export function useTopics() {
  const { data, error, isLoading, mutate } = useSWR(
    '/topics',
    async () => {
      const result = await apiCall(() => topicsApi.getTopics());
      if (result.error) throw new Error(result.error.details || result.error.error);
      return result.data;
    }
  );

  return {
    topics: data || [],
    isLoading,
    error: error as Error | null,
    mutate,
  };
}

// === Хуки для админки ===

/**
 * Статистика приложения (админка)
 * 
 * Пример:
 * const { stats, isLoading } = useAdminStats();
 */
export function useAdminStats() {
  const { data, error, isLoading, mutate } = useSWR(
    '/admin/stats',
    async () => {
      const result = await apiCall(() => adminApi.getStats());
      if (result.error) throw new Error(result.error.details || result.error.error);
      return result.data;
    }
  );

  return {
    stats: data,
    isLoading,
    error: error as Error | null,
    mutate,
  };
}

/**
 * Пользователи (админка)
 * 
 * Пример:
 * const { users, total, isLoading } = useAdminUsers(0, 20);
 */
export function useAdminUsers(skip: number = 0, limit: number = 20) {
  const key = `/admin/users?skip=${skip}&limit=${limit}`;

  const { data, error, isLoading, mutate } = useSWR(
    key,
    async () => {
      const result = await apiCall(() => adminApi.getUsers({ skip, limit }));
      if (result.error) throw new Error(result.error.details || result.error.error);
      return result.data;
    }
  );

  return {
    users: data?.data || [],
    total: data?.total || 0,
    isLoading,
    error: error as Error | null,
    mutate,
  };
}

/**
 * Слова для проверки (админка)
 * 
 * Пример:
 * const { words, total, isLoading } = useAdminWordsToCheck(0, 20);
 */
export function useAdminWordsToCheck(skip: number = 0, limit: number = 20, status?: string) {
  const key = `/admin/check-words?skip=${skip}&limit=${limit}${status ? `&status=${status}` : ''}`;

  const { data, error, isLoading, mutate } = useSWR(
    key,
    async () => {
      const result = await apiCall(() => adminApi.getWordsToCheck({ skip, limit, status }));
      if (result.error) throw new Error(result.error.details || result.error.error);
      return result.data;
    }
  );

  return {
    words: data?.data || [],
    total: data?.total || 0,
    isLoading,
    error: error as Error | null,
    mutate,
  };
}

// === Mutation Hooks (для создания, обновления, удаления) ===

/**
 * Хук для добавления слова в избранное
 * 
 * Пример:
 * const { addFavorite, isLoading } = useAddFavorite();
 * await addFavorite(wordId);
 */
export function useAddFavorite() {
  const { mutate: revalidateFavorites } = useFavorites();
  
  const addFavorite = useCallback(async (wordId: number) => {
    const result = await apiCall(() => wordsApi.addFavorite(wordId));
    if (result.error) throw new Error(result.error.details || result.error.error);
    // Оптимистичное обновление кэша
    globalMutate('/favorites');
    return result.data;
  }, [revalidateFavorites]);

  return { addFavorite, isLoading: false };
}

/**
 * Хук для удаления слова из избранного
 * 
 * Пример:
 * const { removeFavorite, isLoading } = useRemoveFavorite();
 * await removeFavorite(wordId);
 */
export function useRemoveFavorite() {
  const removeFavorite = useCallback(async (wordId: number) => {
    const result = await apiCall(() => wordsApi.removeFavorite(wordId));
    if (result.error) throw new Error(result.error.details || result.error.error);
    globalMutate('/favorites');
    return result.data;
  }, []);

  return { removeFavorite, isLoading: false };
}

/**
 * Хук для оценки слова (тренер)
 * 
 * Пример:
 * const { rateWord, isLoading } = useRateWord();
 * await rateWord(wordId, 5);
 */
export function useRateWord() {
  const { mutate: revalidateStats } = useStats();
  
  const rateWord = useCallback(async (wordId: number, rating: 0 | 1 | 3 | 5) => {
    const result = await apiCall(() => trainerApi.rateWord(wordId, rating));
    if (result.error) throw new Error(result.error.details || result.error.error);
    // Обновляем статистику и слова для тренировки
    globalMutate('/trainer/stats');
    globalMutate((key: string) => typeof key === 'string' && key.startsWith('/trainer/words'));
    return result.data;
  }, [revalidateStats]);

  return { rateWord, isLoading: false };
}

/**
 * Хук для коррекции текста (дневник)
 * 
 * Пример:
 * const { correctText, isLoading, result } = useCorrectText();
 * const { corrected, explanation } = await correctText('Ich gehen Schule');
 */
export function useCorrectText() {
  const { mutate, isLoading, error } = useSWR(
    null,
    () => Promise.resolve(null)
  );

  const correctText = useCallback(async (text: string) => {
    const result = await apiCall(() => diaryApi.correctText(text));
    if (result.error) throw new Error(result.error.details || result.error.error);
    return result.data;
  }, []);

  return { correctText, isLoading, error };
}

/**
 * Хук для удаления записи дневника
 * 
 * Пример:
 * const { deleteEntry } = useDeleteDiaryEntry();
 * await deleteEntry(entryId);
 */
export function useDeleteDiaryEntry() {
  const { mutate: revalidateHistory } = useDiaryHistory();
  
  const deleteEntry = useCallback(async (id: number) => {
    const result = await apiCall(() => diaryApi.deleteEntry(id));
    if (result.error) throw new Error(result.error.details || result.error.error);
    globalMutate('/diary/history');
    return result.data;
  }, [revalidateHistory]);

  return { deleteEntry, isLoading: false };
}

/**
 * Хук для удаления аудио
 * 
 * Пример:
 * const { deleteAudio } = useDeleteAudio();
 * await deleteAudio(filename);
 */
export function useDeleteAudio() {
  const deleteAudio = useCallback(async (filename: string) => {
    const result = await apiCall(() => audioApi.deleteAudio(filename));
    if (result.error) throw new Error(result.error.details || result.error.error);
    globalMutate((key: string) => typeof key === 'string' && key.startsWith('/audio/list'));
    return result.data;
  }, []);

  return { deleteAudio, isLoading: false };
}

/**
 * Хук для загрузки аудио
 * 
 * Пример:
 * const { uploadAudio, isLoading } = useUploadAudio();
 * await uploadAudio(file);
 */
export function useUploadAudio() {
  const uploadAudio = useCallback(async (file: File) => {
    const result = await apiCall(() => audioApi.uploadAudio(file));
    if (result.error) throw new Error(result.error.details || result.error.error);
    globalMutate((key: string) => typeof key === 'string' && key.startsWith('/audio/list'));
    return result.data;
  }, []);

  return { uploadAudio, isLoading: false };
}

/**
 * Хук для добавления пользовательского слова
 * 
 * Пример:
 * const { addCustomWord, isLoading } = useAddCustomWord();
 * await addCustomWord({ de: 'Haus', ru: 'Дом', article: 'das' });
 */
export function useAddCustomWord() {
  const addCustomWord = useCallback(async (data: Parameters<typeof wordsApi.addCustomWord>[0]) => {
    const result = await apiCall(() => wordsApi.addCustomWord(data));
    if (result.error) throw new Error(result.error.details || result.error.error);
    // Реалим кэш слов
    globalMutate((key: string) => typeof key === 'string' && key.startsWith('/words'));
    return result.data;
  }, []);

  return { addCustomWord, isLoading: false };
}

/**
 * Хук для извлечения слов из коррекции
 * 
 * Пример:
 * const { extractWords } = useExtractWords();
 * const words = await extractWords(original, corrected);
 */
export function useExtractWords() {
  const extractWords = useCallback(async (original: string, corrected: string) => {
    const result = await apiCall(() => diaryApi.extractWords(original, corrected));
    if (result.error) throw new Error(result.error.details || result.error.error);
    return result.data;
  }, []);

  return { extractWords, isLoading: false };
}

/**
 * Хук для добавления слов из дневника
 * 
 * Пример:
 * const { addWords } = useAddDiaryWords();
 * await addWords(words);
 */
export function useAddDiaryWords() {
  const addWords = useCallback(async (words: Array<{ de: string; ru: string; article: string; level: string }>) => {
    const result = await apiCall(() => diaryApi.addWords(words));
    if (result.error) throw new Error(result.error.details || result.error.error);
    return result.data;
  }, []);

  return { addWords, isLoading: false };
}

/**
 * Универсальный хук для мутаций
 * 
 * Пример:
 * const { mutate: login, isLoading } = useMutation(authApi.login, onSuccess);
 * await login(email, password);
 */
export function useMutation<T, F extends (...args: any[]) => Promise<any>>(
  mutationFn: F,
  options?: {
    onSuccess?: (data: T) => void;
    onError?: (error: Error) => void;
    invalidateKeys?: string[] | ((...args: any[]) => string[]);
  }
) {
  const execute = useCallback(async (...args: Parameters<F>) => {
    try {
      const result = await apiCall(() => mutationFn(...args));
      if (result.error) {
        throw new Error(result.error.details || result.error.error);
      }
      options?.onSuccess?.(result.data as T);
      // Инвалидация кэша
      if (options?.invalidateKeys) {
        const keys = typeof options.invalidateKeys === 'function'
          ? options.invalidateKeys(...args)
          : options.invalidateKeys;
        keys.forEach(key => globalMutate(key));
      }
      return result.data as T;
    } catch (error) {
      options?.onError?.(error as Error);
      throw error;
    }
  }, [mutationFn, options]);

  return { mutate: execute, isLoading: false };
}
