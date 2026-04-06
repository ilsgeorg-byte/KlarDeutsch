# KlarDeutsch API Layer - Usage Guide

## Overview

KlarDeutsch provides a centralized API layer in `app/lib/` that eliminates code duplication and ensures consistent error handling across the application.

**Location:** `app/lib/api.ts` and `app/lib/hooks.ts`

---

## 📚 Table of Contents

1. [Architecture](#architecture)
2. [API Client (api.ts)](#api-client-apits)
3. [React Hooks (hooks.ts)](#react-hooks-hooksts)
4. [Migration Guide](#migration-guide)
5. [Best Practices](#best-practices)

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│              React Components                   │
│         (trainer, diary, dictionary...)         │
└───────────────────┬─────────────────────────────┘
                    │
         USES VIA   │
                    │
┌───────────────────▼─────────────────────────────┐
│           SWR Hooks (hooks.ts)                  │
│  • Automatic caching                            │
│  • Auto-revalidation                            │
│  • Optimistic updates                           │
└───────────────────┬─────────────────────────────┘
                    │
         CALLS      │
                    │
┌───────────────────▼─────────────────────────────┐
│         Axios Client (api.ts)                   │
│  • Token injection (interceptor)                │
│  • Error handling (401 → /login)               │
│  • Type-safe API methods                        │
└───────────────────┬─────────────────────────────┘
                    │
         FORWARDS   │
                    │
┌───────────────────▼─────────────────────────────┐
│         Flask Backend API                       │
│     (http://localhost:5000/api)                │
└─────────────────────────────────────────────────┘
```

---

## API Client (api.ts)

### Token Management

```typescript
import { getToken, setToken, removeToken } from '@/lib/api';

// Get current token
const token = getToken(); // Returns 'token' from localStorage

// Set token (after login)
setToken('your-jwt-token-here');

// Remove token (after logout)
removeToken();
```

**IMPORTANT:** The token key is `'token'` (not `'klardeutsch_token'`). This ensures compatibility with all existing components.

### Direct API Calls

```typescript
import { wordsApi, trainerApi, diaryApi, audioApi, adminApi } from '@/lib/api';

// Get words
const words = await wordsApi.getWords({ level: 'A1', skip: 0, limit: 20 });

// Search words
const searchResults = await wordsApi.searchWords('Haus', 10);

// Add to favorites
await wordsApi.addFavorite(wordId);

// Rate word (trainer)
await trainerApi.rateWord(wordId, 5); // 0, 1, 3, or 5

// Correct text (diary)
const { corrected, explanation } = await diaryApi.correctText(text);

// Upload audio
const formData = new FormData();
formData.append('file', audioFile);
await audioApi.uploadAudio(audioFile);

// Admin: Get stats
const stats = await adminApi.getStats();

// Admin: Delete user
await adminApi.deleteUser(userId);
```

### Safe API Calls with Error Handling

```typescript
import { apiCall } from '@/lib/api';

const { data, error } = await apiCall(() => wordsApi.getWords({ level: 'A1' }));

if (error) {
  console.error('Failed to load words:', error.error, error.details);
} else {
  console.log('Words:', data.data);
}
```

### Available API Modules

| Module | Methods | Description |
|--------|---------|-------------|
| `authApi` | `register()`, `login()`, `me()`, `logout()` | Authentication |
| `wordsApi` | `getWords()`, `getWord()`, `searchWords()`, `addFavorite()`, `removeFavorite()`, `getFavorites()`, `getWordsByTopic()`, `addCustomWord()` | Words & Dictionary |
| `trainerApi` | `getTrainingWords()`, `rateWord()`, `getStats()` | Training (SM-2) |
| `diaryApi` | `correctText()`, `getHistory()`, `deleteEntry()`, `extractWords()`, `addWords()` | Diary & AI Correction |
| `audioApi` | `uploadAudio()`, `listAudio()`, `deleteAudio()` | Audio Recordings |
| `adminApi` | `getStats()`, `getUsers()`, `deleteUser()`, `getWordsToCheck()`, `approveWord()`, `rejectWord()`, `updateWord()`, `deleteWord()`, `bulkUploadWords()`, `getCheckWordsStats()` | Admin Panel |
| `topicsApi` | `getTopics()`, `getTopic()` | Thematic Topics |

---

## React Hooks (hooks.ts)

### Data Fetching Hooks

#### useWords

```typescript
import { useWords } from '@/lib/hooks';

function DictionaryPage() {
  const { words, total, isLoading, error, mutate } = useWords('A1', 0, 20);
  
  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  
  return (
    <div>
      <p>Total: {total} words</p>
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
  
  if (isLoading) return <div>Loading training words...</div>;
  
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
      {isLoading && <p>Searching...</p>}
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
      <h2>My Favorites</h2>
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
      <h2>My Diary Entries</h2>
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
      <h2>Learning Progress</h2>
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

### Admin Hooks

#### useAdminStats

```typescript
import { useAdminStats } from '@/lib/hooks';

function AdminDashboard() {
  const { stats, isLoading } = useAdminStats();
  
  return (
    <div>
      <p>Users: {stats?.total_users}</p>
      <p>Words: {stats?.total_words}</p>
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
      <p>Total users: {total}</p>
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
      <p>Pending words: {total}</p>
      {words.map(word => <WordReview key={word.id} word={word} />)}
    </div>
  );
}
```

### Mutation Hooks

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
      console.error('Failed to toggle favorite:', error);
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
      // UI will auto-revalidate via SWR
    } catch (error) {
      console.error('Failed to rate word:', error);
    }
  };
  
  return (
    <div>
      <button onClick={() => handleRate(0)}>Don't know</button>
      <button onClick={() => handleRate(1)}>Hard</button>
      <button onClick={() => handleRate(3)}>Good</button>
      <button onClick={() => handleRate(5)}>Easy</button>
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
      console.error('Failed to correct text:', error);
    }
  };
  
  return (
    <div>
      <textarea value={text} onChange={e => setText(e.target.value)} />
      <button onClick={handleCorrect}>Correct with AI</button>
      {result && (
        <div>
          <p>Corrected: {result.corrected}</p>
          <p>Explanation: {result.explanation}</p>
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
    if (!confirm('Delete this entry?')) return;
    
    try {
      await deleteEntry(entry.id);
      // List auto-refreshes via SWR
    } catch (error) {
      console.error('Failed to delete:', error);
    }
  };
  
  return <button onClick={handleDelete}>Delete</button>;
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
      console.error('Failed to delete audio:', error);
    }
  };
  
  const handleUpload = async (file: File) => {
    try {
      await uploadAudio(file);
    } catch (error) {
      console.error('Failed to upload audio:', error);
    }
  };
  
  return (
    <div>
      <input type="file" onChange={e => e.target.files && handleUpload(e.target.files[0])} />
      {/* ... file list ... */}
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
      // Word list auto-refreshes
    } catch (error) {
      console.error('Failed to add word:', error);
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
      alert(`Added ${words.length} words to your dictionary!`);
    } catch (error) {
      console.error('Failed to extract/add words:', error);
    }
  };
  
  return <button onClick={() => handleExtractAndAdd(original, corrected)}>Extract Words</button>;
}
```

### Generic useMutation Hook

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
        alert('Login failed: ' + error.message);
      },
      invalidateKeys: () => ['/auth/me'], // Optional: invalidate specific caches
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

## Migration Guide

### Before (Raw fetch - DON'T USE)

```typescript
// ❌ BAD: Manual fetch with duplicated logic
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

if (!res.ok) throw new Error('Failed to rate word');
const data = await res.json();
```

### After (Using hooks - RECOMMENDED)

```typescript
// ✅ GOOD: Using SWR hooks
import { useRateWord } from '@/lib/hooks';

function WordCard({ word }) {
  const { rateWord } = useRateWord();
  
  const handleRate = async () => {
    try {
      await rateWord(word.id, 5);
      // Stats and word lists auto-refresh!
    } catch (error) {
      console.error('Failed:', error);
    }
  };
  
  return <button onClick={handleRate}>Rate</button>;
}
```

### Migration Steps

1. **Remove manual fetch calls:**
   - Delete `fetch('/api/...')` calls
   - Remove manual token handling
   - Remove 401 redirect logic

2. **Use appropriate hooks:**
   - Find matching hook in `hooks.ts`
   - Import and use it in your component

3. **Remove loading/error state duplication:**
   - Hooks provide `isLoading`, `error`, and `mutate`
   - No need for manual `useState` for these

4. **Test thoroughly:**
   - Verify auto-revalidation works
   - Check error handling
   - Ensure 401 redirects still work

---

## Best Practices

### ✅ DO

```typescript
// Use hooks for data fetching
const { words, isLoading, error, mutate } = useWords('A1');

// Use mutation hooks for actions
const { addFavorite } = useAddFavorite();

// Handle loading states from hooks
if (isLoading) return <LoadingSpinner />;

// Handle errors from hooks
if (error) return <ErrorMessage error={error.message} />;

// Revalidate when needed
mutate();

// Use apiCall for direct API calls outside components
const result = await apiCall(() => wordsApi.getWords({ level: 'A1' }));
```

### ❌ DON'T

```typescript
// Don't use raw fetch
const res = await fetch('/api/words', { ... });

// Don't manually handle tokens
const token = localStorage.getItem('token');

// Don't duplicate error handling
if (res.status === 401) { router.push('/login'); }

// Don't create your own loading states when hooks provide them
const [loading, setLoading] = useState(false); // Unnecessary!
```

---

## File Structure

```
app/
├── lib/
│   ├── api.ts       # Axios client + API methods
│   └── hooks.ts     # SWR hooks for all API operations
└── ...
```

---

## Troubleshooting

### Token not being sent

- Make sure you're using `hooks.ts` or `api.ts` (not raw `fetch`)
- Check that token exists: `console.log(getToken())`
- Verify token format: `'token'` in localStorage

### 401 errors not redirecting

- The API client automatically redirects on 401
- Make sure you're not catching errors before the interceptor

### Hooks not revalidating

- Check that you're calling `mutate()` after mutations
- Use `globalMutate()` to invalidate specific caches
- Set `revalidateOnFocus: true` if needed

---

**Last updated:** April 2026  
**See also:** `docs/general_en.md`, `docs/general_ru.md`
