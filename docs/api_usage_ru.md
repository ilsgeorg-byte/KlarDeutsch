# API слой KlarDeutsch - Руководство по использованию

## Обзор

KlarDeutsch предоставляет централизованный API слой в директории `app/lib/`, который устраняет дублирование кода и обеспечивает согласованную обработку ошибок во всём приложении.

**Расположение:** `app/lib/api.ts` и `app/lib/hooks.ts`

---

## 📚 Содержание

1. [Архитектура](#архитектура)
2. [API клиент (api.ts)](#api-клиент-apits)
3. [React хуки (hooks.ts)](#react-хуки-hooksts)
4. [Руководство по миграции](#руководство-по-миграции)
5. [Лучшие практики](#лучшие-практики)

---

## Архитектура

```
┌─────────────────────────────────────────────────┐
│              React Компоненты                   │
│         (trainer, diary, dictionary...)         │
└───────────────────┬─────────────────────────────┘
                    │
         ИСПОЛЬЗУЮТ │
                    │
┌───────────────────▼─────────────────────────────┐
│           SWR Хуки (hooks.ts)                   │
│  • Автоматическое кэширование                   │
│  • Авто-ревалидация                             │
│  • Оптимистичные обновления                     │
└───────────────────┬─────────────────────────────┘
                    │
         ВЫЗЫВАЮТ  │
                    │
┌───────────────────▼─────────────────────────────┐
│         Axios Клиент (api.ts)                   │
│  • Инъекция токена (интерсептор)               │
│  • Обработка ошибок (401 → /login)             │
│  • Типобезопасные API методы                   │
└───────────────────┬─────────────────────────────┘
                    │
         ПЕРЕНАПРАВ │
                    │
┌───────────────────▼─────────────────────────────┐
│         Flask Backend API                       │
│     (http://localhost:5000/api)                │
└─────────────────────────────────────────────────┘
```

---

## API клиент (api.ts)

### Управление токенами

```typescript
import { getToken, setToken, removeToken } from '@/lib/api';

// Получить текущий токен
const token = getToken(); // Возвращает 'token' из localStorage

// Установить токен (после входа)
setToken('ваш-jwt-токен');

// Удалить токен (после выхода)
removeToken();
```

**ВАЖНО:** Ключ токена — `'token'` (не `'klardeutsch_token'`). Это обеспечивает совместимость со всеми существующими компонентами.

### Прямые вызовы API

```typescript
import { wordsApi, trainerApi, diaryApi, audioApi, adminApi } from '@/lib/api';

// Получить слова
const words = await wordsApi.getWords({ level: 'A1', skip: 0, limit: 20 });

// Поиск слов
const searchResults = await wordsApi.searchWords('Haus', 10);

// Добавить в избранное
await wordsApi.addFavorite(wordId);

// Оценить слово (тренер)
await trainerApi.rateWord(wordId, 5); // 0, 1, 3 или 5

// Коррекция текста (дневник)
const { corrected, explanation } = await diaryApi.correctText(text);

// Загрузить аудио
const formData = new FormData();
formData.append('file', audioFile);
await audioApi.uploadAudio(audioFile);

// Админка: Получить статистику
const stats = await adminApi.getStats();

// Админка: Удалить пользователя
await adminApi.deleteUser(userId);
```

### Безопасные вызовы API с обработкой ошибок

```typescript
import { apiCall } from '@/lib/api';

const { data, error } = await apiCall(() => wordsApi.getWords({ level: 'A1' }));

if (error) {
  console.error('Не удалось загрузить слова:', error.error, error.details);
} else {
  console.log('Слова:', data.data);
}
```

### Доступные API модули

| Модуль | Методы | Описание |
|--------|--------|----------|
| `authApi` | `register()`, `login()`, `me()`, `logout()` | Аутентификация |
| `wordsApi` | `getWords()`, `getWord()`, `searchWords()`, `addFavorite()`, `removeFavorite()`, `getFavorites()`, `getWordsByTopic()`, `addCustomWord()` | Слова и Словарь |
| `trainerApi` | `getTrainingWords()`, `rateWord()`, `getStats()` | Тренировка (SM-2) |
| `diaryApi` | `correctText()`, `getHistory()`, `deleteEntry()`, `extractWords()`, `addWords()` | Дневник и ИИ-коррекция |
| `audioApi` | `uploadAudio()`, `listAudio()`, `deleteAudio()` | Аудиозаписи |
| `adminApi` | `getStats()`, `getUsers()`, `deleteUser()`, `getWordsToCheck()`, `approveWord()`, `rejectWord()`, `updateWord()`, `deleteWord()`, `bulkUploadWords()`, `getCheckWordsStats()` | Панель администратора |
| `topicsApi` | `getTopics()`, `getTopic()` | Тематические темы |

---

## React хуки (hooks.ts)

### Хуки для получения данных

#### useWords

```typescript
import { useWords } from '@/lib/hooks';

function DictionaryPage() {
  const { words, total, isLoading, error, mutate } = useWords('A1', 0, 20);
  
  if (isLoading) return <div>Загрузка...</div>;
  if (error) return <div>Ошибка: {error.message}</div>;
  
  return (
    <div>
      <p>Всего: {total} слов</p>
      {words.map(word => (
        <div key={word.id}>{word.article} {word.de} - {word.ru}</div>
      ))}
    </div>
  );
}
```

#### useTrainingWords

```typescript
import { useTrainingWords } from '@/lib/hooks';

function TrainerPage() {
  const { words, isLoading, error, mutate } = useTrainingWords('A1', 10);
  
  if (isLoading) return <div>Загрузка слов для тренировки...</div>;
  
  return (
    <div>
      {words.map(word => (
        <WordCard key={word.id} word={word} />
      ))}
    </div>
  );
}
```

#### useWordSearch

```typescript
import { useWordSearch } from '@/lib/hooks';

function SearchBar() {
  const [query, setQuery] = useState('');
  const { results, isLoading } = useWordSearch(query, 10);
  
  return (
    <div>
      <input value={query} onChange={e => setQuery(e.target.value)} />
      {isLoading && <p>Поиск...</p>}
      {results.map(word => <WordItem key={word.id} word={word} />)}
    </div>
  );
}
```

#### useFavorites

```typescript
import { useFavorites } from '@/lib/hooks';

function FavoritesPage() {
  const { favorites, isLoading, mutate } = useFavorites();
  
  return (
    <div>
      <h2>Мои избранные</h2>
      {favorites.map(word => <WordCard key={word.id} word={word} />)}
    </div>
  );
}
```

#### useDiaryHistory

```typescript
import { useDiaryHistory } from '@/lib/hooks';

function DiaryPage() {
  const { entries, isLoading, mutate } = useDiaryHistory();
  
  return (
    <div>
      <h2>Мои записи в дневнике</h2>
      {entries.map(entry => (
        <DiaryEntry key={entry.id} entry={entry} />
      ))}
    </div>
  );
}
```

#### useStats

```typescript
import { useStats } from '@/lib/hooks';

function ProfilePage() {
  const { stats, isLoading } = useStats();
  
  if (!stats) return null;
  
  return (
    <div>
      <h2>Прогресс обучения</h2>
      <p>A1: {stats.user_progress.A1} / {stats.total_words.A1}</p>
      <p>A2: {stats.user_progress.A2} / {stats.total_words.A2}</p>
    </div>
  );
}
```

#### useAudioList

```typescript
import { useAudioList } from '@/lib/hooks';

function AudioPage() {
  const { files, isLoading } = useAudioList(20);
  
  return (
    <ul>
      {files.map(file => <AudioFile key={file} filename={file} />)}
    </ul>
  );
}
```

#### useTopics

```typescript
import { useTopics } from '@/lib/hooks';

function TopicsPage() {
  const { topics, isLoading } = useTopics();
  
  return (
    <div>
      {topics.map(topic => (
        <TopicCard key={topic.slug} topic={topic} />
      ))}
    </div>
  );
}
```

### Хуки для админки

#### useAdminStats

```typescript
import { useAdminStats } from '@/lib/hooks';

function AdminDashboard() {
  const { stats, isLoading } = useAdminStats();
  
  return (
    <div>
      <p>Пользователи: {stats?.total_users}</p>
      <p>Слова: {stats?.total_words}</p>
    </div>
  );
}
```

#### useAdminUsers

```typescript
import { useAdminUsers } from '@/lib/hooks';

function AdminUsers() {
  const { users, total, isLoading } = useAdminUsers(0, 20);
  
  return (
    <div>
      <p>Всего пользователей: {total}</p>
      {users.map(user => <UserRow key={user.id} user={user} />)}
    </div>
  );
}
```

#### useAdminWordsToCheck

```typescript
import { useAdminWordsToCheck } from '@/lib/hooks';

function AdminWords() {
  const { words, total, isLoading } = useAdminWordsToCheck(0, 20);
  
  return (
    <div>
      <p>Ожидают проверки: {total}</p>
      {words.map(word => <WordReview key={word.id} word={word} />)}
    </div>
  );
}
```

### Хуки для мутаций

#### useAddFavorite / useRemoveFavorite

```typescript
import { useAddFavorite, useRemoveFavorite } from '@/lib/hooks';

function WordCard({ word }) {
  const { addFavorite } = useAddFavorite();
  const { removeFavorite } = useRemoveFavorite();
  
  const handleToggle = async () => {
    try {
      if (word.is_favorite) {
        await removeFavorite(word.id);
      } else {
        await addFavorite(word.id);
      }
    } catch (error) {
      console.error('Не удалось переключить избранное:', error);
    }
  };
  
  return (
    <button onClick={handleToggle}>
      {word.is_favorite ? '★' : '☆'}
    </button>
  );
}
```

#### useRateWord

```typescript
import { useRateWord } from '@/lib/hooks';

function TrainingCard({ word }) {
  const { rateWord } = useRateWord();
  
  const handleRate = async (rating: 0 | 1 | 3 | 5) => {
    try {
      await rateWord(word.id, rating);
      // UI автоматически обновится через SWR
    } catch (error) {
      console.error('Не удалось оценить слово:', error);
    }
  };
  
  return (
    <div>
      <button onClick={() => handleRate(0)}>Не знаю</button>
      <button onClick={() => handleRate(1)}>Трудно</button>
      <button onClick={() => handleRate(3)}>Хорошо</button>
      <button onClick={() => handleRate(5)}>Легко</button>
    </div>
  );
}
```

#### useCorrectText

```typescript
import { useCorrectText } from '@/lib/hooks';

function DiaryEditor() {
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const { correctText } = useCorrectText();
  
  const handleCorrect = async () => {
    try {
      const correction = await correctText(text);
      setResult(correction);
    } catch (error) {
      console.error('Не удалось скорректировать текст:', error);
    }
  };
  
  return (
    <div>
      <textarea value={text} onChange={e => setText(e.target.value)} />
      <button onClick={handleCorrect}>Скорректировать ИИ</button>
      {result && (
        <div>
          <p>Исправлено: {result.corrected}</p>
          <p>Объяснение: {result.explanation}</p>
        </div>
      )}
    </div>
  );
}
```

#### useDeleteDiaryEntry

```typescript
import { useDeleteDiaryEntry } from '@/lib/hooks';

function DiaryEntry({ entry }) {
  const { deleteEntry } = useDeleteDiaryEntry();
  
  const handleDelete = async () => {
    if (!confirm('Удалить эту запись?')) return;
    
    try {
      await deleteEntry(entry.id);
      // Список автоматически обновится через SWR
    } catch (error) {
      console.error('Не удалось удалить:', error);
    }
  };
  
  return <button onClick={handleDelete}>Удалить</button>;
}
```

#### useDeleteAudio / useUploadAudio

```typescript
import { useDeleteAudio, useUploadAudio } from '@/lib/hooks';

function AudioFileManager() {
  const { deleteAudio } = useDeleteAudio();
  const { uploadAudio } = useUploadAudio();
  
  const handleDelete = async (filename: string) => {
    try {
      await deleteAudio(filename);
    } catch (error) {
      console.error('Не удалось удалить аудио:', error);
    }
  };
  
  const handleUpload = async (file: File) => {
    try {
      await uploadAudio(file);
    } catch (error) {
      console.error('Не удалось загрузить аудио:', error);
    }
  };
  
  return (
    <div>
      <input type="file" onChange={e => e.target.files && handleUpload(e.target.files[0])} />
      {/* ... список файлов ... */}
    </div>
  );
}
```

#### useAddCustomWord

```typescript
import { useAddCustomWord } from '@/lib/hooks';

function AddWordForm() {
  const { addCustomWord } = useAddCustomWord();
  
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    try {
      await addCustomWord({
        de: 'Haus',
        ru: 'Дом',
        article: 'das',
        level: 'A1',
        topic: 'basics',
      });
      // Список слов автоматически обновится
    } catch (error) {
      console.error('Не удалось добавить слово:', error);
    }
  };
  
  return <form onSubmit={handleSubmit}>...</form>;
}
```

#### useExtractWords / useAddDiaryWords

```typescript
import { useExtractWords, useAddDiaryWords } from '@/lib/hooks';

function DiaryWordExtractor() {
  const { extractWords } = useExtractWords();
  const { addWords } = useAddDiaryWords();
  
  const handleExtractAndAdd = async (original: string, corrected: string) => {
    try {
      const words = await extractWords(original, corrected);
      await addWords(words);
      alert(`Добавлено ${words.length} слов в ваш словарь!`);
    } catch (error) {
      console.error('Не удалось извлечь/добавить слова:', error);
    }
  };
  
  return <button onClick={() => handleExtractAndAdd(original, corrected)}>Извлечь слова</button>;
}
```

### Универсальный хук useMutation

```typescript
import { useMutation } from '@/lib/hooks';
import { authApi } from '@/lib/api';

function LoginForm() {
  const { mutate: login } = useMutation(
    authApi.login,
    {
      onSuccess: (data) => {
        localStorage.setItem('token', data.token);
        router.push('/trainer');
      },
      onError: (error) => {
        alert('Вход не удался: ' + error.message);
      },
      invalidateKeys: () => ['/auth/me'], // Опционально: инвалидировать конкретные кэши
    }
  );
  
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    await login(email, password);
  };
  
  return <form onSubmit={handleSubmit}>...</form>;
}
```

---

## Руководство по миграции

### До (Сырой fetch - НЕ ИСПОЛЬЗУЙТЕ)

```typescript
// ❌ ПЛОХО: Ручной fetch с дублированной логикой
const token = localStorage.getItem('token');
const res = await fetch('/api/trainer/rate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  },
  body: JSON.stringify({ word_id: wordId, rating }),
});

if (res.status === 401) {
  localStorage.removeItem('token');
  router.push('/login');
  return;
}

if (!res.ok) throw new Error('Не удалось оценить слово');
const data = await res.json();
```

### После (Использование хуков - РЕКОМЕНДУЕТСЯ)

```typescript
// ✅ ХОРОШО: Использование SWR хуков
import { useRateWord } from '@/lib/hooks';

function WordCard({ word }) {
  const { rateWord } = useRateWord();
  
  const handleRate = async () => {
    try {
      await rateWord(word.id, 5);
      // Статистика и списки слов автоматически обновятся!
    } catch (error) {
      console.error('Ошибка:', error);
    }
  };
  
  return <button onClick={handleRate}>Оценить</button>;
}
```

### Шаги миграции

1. **Удалите ручные вызовы fetch:**
   - Удалите вызовы `fetch('/api/...')`
   - Удалите ручное управление токенами
   - Удалите логику редиректа при 401

2. **Используйте соответствующие хуки:**
   - Найдите подходящий хук в `hooks.ts`
   - Импортируйте и используйте его в компоненте

3. **Удалите дублирование состояний загрузки/ошибок:**
   - Хуки предоставляют `isLoading`, `error` и `mutate`
   - Нет необходимости в ручном `useState` для этого

4. **Тщательно протестируйте:**
   - Убедитесь, что авто-ревалидация работает
   - Проверьте обработку ошибок
   - Убедитесь, что редиректы 401 всё ещё работают

---

## Лучшие практики

### ✅ ДЕЛАЙТЕ

```typescript
// Используйте хуки для получения данных
const { words, isLoading, error, mutate } = useWords('A1');

// Используйте хуки мутаций для действий
const { addFavorite } = useAddFavorite();

// Обрабатывайте состояния загрузки из хуков
if (isLoading) return <LoadingSpinner />;

// Обрабатывайте ошибки из хуков
if (error) return <ErrorMessage error={error.message} />;

// Ревалидируйте при необходимости
mutate();

// Используйте apiCall для прямых вызовов API вне компонентов
const result = await apiCall(() => wordsApi.getWords({ level: 'A1' }));
```

### ❌ НЕ ДЕЛАЙТЕ

```typescript
// Не используйте сырой fetch
const res = await fetch('/api/words', { ... });

// Не управляйте токенами вручную
const token = localStorage.getItem('token');

// Не дублируйте обработку ошибок
if (res.status === 401) { router.push('/login'); }

// Не создавайте свои состояния загрузки, когда хуки их предоставляют
const [loading, setLoading] = useState(false); // Избыточно!
```

---

## Структура файлов

```
app/
├── lib/
│   ├── api.ts       # Axios клиент + API методы
│   └── hooks.ts     # SWR хуки для всех API операций
└── ...
```

---

## Устранение неполадок

### Токен не отправляется

- Убедитесь, что используете `hooks.ts` или `api.ts` (не сырой `fetch`)
- Проверьте существование токена: `console.log(getToken())`
- Проверьте формат токена: `'token'` в localStorage

### Ошибки 401 не перенаправляют

- API клиент автоматически перенаправляет при 401
- Убедитесь, что не перехватываете ошибки до интерсептора

### Хуки не ревалидируются

- Убедитесь, что вызываете `mutate()` после мутаций
- Используйте `globalMutate()` для инвалидации конкретных кэшей
- Установите `revalidateOnFocus: true` при необходимости

---

**Последнее обновление:** Апрель 2026  
**Смотрите также:** `docs/general_en.md`, `docs/general_ru.md`
