# KlarDeutsch - General Documentation

## Overview

**KlarDeutsch** is a comprehensive German language learning web application designed primarily for Russian-speaking learners. The platform combines spaced repetition flashcards, AI-powered text correction, and interactive vocabulary training to make learning German efficient and engaging.

**Tagline:** "Учи немецкий легко" (Learn German easily)  
**Mission:** Your personal assistant for level A1 and beyond

---

## 🌟 Key Features

### 1. **Interactive Trainer** (`/trainer`)
- Spaced repetition system using the **SM-2 algorithm** (SuperMemo 2)
- Flashcard-based vocabulary practice
- Users rate their knowledge: 0 (Don't know), 1 (Hard), 3 (Good), 5 (Easy)
- Intelligent scheduling with fuzzing and ease-factor adjustments
- Tracks learning progress and optimizes review intervals

### 2. **Dictionary** (`/dictionary`)
- Browse vocabulary by **CEFR levels** (A1, A2, B1, B2, C1)
- Organized by thematic topics
- Advanced search functionality
- Each word entry includes:
  - Definite article (der/die/das)
  - Plural forms
  - Verb conjugations (if applicable)
  - Example sentences
  - Synonyms and antonyms
  - Common collocations

### 3. **AI-Powered Diary** (`/diary`)
- Write German text freely
- Get **AI-powered grammar correction** via Google Gemini or OpenAI
- Detailed explanations for each correction
- Extract vocabulary from your writings to add to your dictionary

### 4. **Pronunciation Training** (`/audio`)
- Record your pronunciation directly in the browser
- Store audio files (webm, mp3, wav, ogg formats)
- Compare your pronunciation with native speakers

### 5. **Thematic Topics** (`/topics`)
- Vocabulary organized by real-life situations
- Learn words in context (e.g., "At the Restaurant", "Travel", "Shopping")
- Structured learning paths

### 6. **Favorites System**
- Bookmark important words for quick access
- Personal word list management

### 7. **User Profile** (`/profile`)
- Track learning statistics
- View progress metrics
- Monitor mastered words

### 8. **Admin Panel** (`/admin`)
- JWT-protected access with email whitelist
- Word management (CRUD operations)
- User management
- Dictionary oversight
- Statistics dashboard
- AI-powered word enrichment tools

---

## 🛠️ Technology Stack

### Frontend
- **Next.js 14** - React framework with App Router
- **React 18.2** - UI library
- **TypeScript 5.3.3** - Type-safe development (strict mode)
- **Tailwind CSS 3.4** - Utility-first CSS framework with dark mode support
- **SWR** - Data fetching and caching
- **Lucide React** - Icon library
- **Google Inter font** with Cyrillic subset

### Backend
- **Flask 3.0** - Python web framework
- **PostgreSQL 15** - Primary database (via psycopg2 with connection pooling)
- **Redis 5.0** - Caching layer
- **Pydantic 2.6** - Request/response validation
- **PyJWT** - Authentication
- **bcrypt** - Password hashing
- **bleach** - HTML sanitization
- **Google Generative AI (Gemini)** - AI text correction
- **OpenAI** - Alternative AI provider
- **Gunicorn 21.2** - Production WSGI server

### Infrastructure
- **Docker** - Multi-stage builds
- **Docker Compose** - 5 services orchestration
- **Nginx** - Reverse proxy
- **Vercel** - Deployment support

---

## 📁 Project Structure

```
KlarDeutsch/
├── app/                    # Next.js frontend (App Router)
│   ├── admin/             # Admin panel pages
│   ├── api/               # Next.js API routes
│   ├── audio/             # Audio recording page
│   ├── components/        # Shared UI components
│   ├── context/           # React context (ThemeContext)
│   ├── diary/             # Diary writing page
│   ├── dictionary/        # Dictionary browse/search
│   ├── lib/               # Utility libraries
│   ├── login/             # Authentication
│   ├── profile/           # User profile
│   ├── register/          # User registration
│   ├── topics/            # Thematic vocabulary
│   ├── trainer/           # SM-2 training interface
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page
│
├── api/                    # Flask backend
│   ├── routes/            # API endpoints
│   │   ├── words.py       # Word CRUD, search, topics
│   │   ├── auth.py        # Authentication
│   │   ├── trainer.py     # SM-2 algorithm
│   │   ├── learning.py    # Learning progress
│   │   ├── diary.py       # AI text correction
│   │   ├── audio.py       # Audio upload
│   │   └── ai_enrich.py   # AI word enrichment
│   ├── utils/             # Utilities
│   ├── db.py              # Database connection
│   ├── schemas.py         # Pydantic schemas
│   └── index.py           # Flask app factory
│
├── docs/                   # Documentation
├── db/                     # Database scripts
├── scripts/                # Utility scripts
├── tools/                  # Development tools
├── nginx/                  # Nginx configuration
├── public/                 # Static assets
├── docker-compose.yml      # Docker services
├── Dockerfile              # Multi-stage build
├── package.json            # Frontend dependencies
├── requirements.txt        # Backend dependencies
└── .env.local.example      # Environment variables template
```

---

## 🚀 Getting Started

### Prerequisites
- Node.js 20+
- Python 3.10+
- PostgreSQL 15+
- Redis 5.0+

### Quick Start with Docker

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd KlarDeutsch
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your configuration
   ```

3. **Start all services:**
   ```bash
   docker-compose up -d
   ```

4. **Access the application:**
   - Frontend: http://localhost
   - Backend API: http://localhost:5000

### Manual Setup

1. **Frontend:**
   ```bash
   npm install
   npm run dev
   ```

2. **Backend:**
   ```bash
   pip install -r requirements.txt
   python api/app.py
   ```

---

## 🔐 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `POSTGRES_URL` | PostgreSQL connection string | ✅ |
| `REDIS_HOST` | Redis server host | ✅ |
| `REDIS_PORT` | Redis server port | ✅ |
| `REDIS_PASSWORD` | Redis password (if any) | ❌ |
| `REDIS_ENABLED` | Enable/disable caching | ❌ |
| `ADMIN_EMAILS` | Comma-separated admin emails | ✅ |
| `ADMIN_API_TOKEN` | Internal API token | ✅ |
| `UPLOAD_DIR` | Audio uploads directory | ✅ |
| `JWT_SECRET` | JWT signing key (min 32 chars) | ✅ |
| `NEXT_PUBLIC_API_URL` | Backend API URL | ✅ |
| `NEXT_PUBLIC_SITE_URL` | Site URL for metadata | ✅ |
| `GEMINI_API_KEY` | Google Gemini API key | ❌ |
| `OPENAI_API_KEY` | OpenAI API key | ❌ |

---

## 🏗️ Architecture

### SM-2 Spaced Repetition Algorithm

The platform uses the proven SuperMemo-2 algorithm for optimal learning:

- **Ease Factor (EF):** Starts at 2.5, adjusts based on performance
- **Interval Calculation:** 
  - Q < 2: Reset to day 1
  - Q >= 2: Interval = previous interval × EF
- **Fuzzing:** Adds randomness to prevent mass reviews
- **Progress Tracking:** Each word maintains its own review schedule

### AI Word Enrichment

Words are enriched with AI-generated data following strict linguistic rules:

- **Nouns:** Always have articles and plural forms
- **Verbs:** Never have articles, include conjugations
- **Adjectives:** Include comparative/superlative forms
- **All words:** Examples, synonyms, antonyms, collocations, topic classification

See `GEMINI.md` for detailed linguistic mandates.

### Security Features

- JWT-based authentication with HTTP-only cookies
- Email whitelist for admin access
- Input sanitization (bleach)
- SQL injection protection (parameterized queries)
- CORS configuration
- Security headers (HSTS, X-Frame-Options, etc.)
- Rate limiting on API endpoints
- Password hashing with bcrypt

---

## 📊 Database Schema

Key tables:
- **users:** User accounts and profiles
- **words:** Vocabulary entries with metadata
- **user_words:** User-specific word progress (SM-2 data)
- **diary_entries:** User diary writings
- **audio_files:** Pronunciation recordings
- **favorites:** User bookmarked words

---

## 🎨 Design Principles

- **Mobile-first responsive design**
- **Dark mode support** (class-based toggle)
- **Accessibility focused**
- **Clean, minimalist UI**
- **Consistent design language** with Tailwind CSS
- **Performance optimized** with Next.js SSR

---

## 🧪 Development

### Code Quality
- TypeScript strict mode
- ESLint configuration
- Prettier formatting
- Pydantic validation on backend

### Testing
Run frontend tests:
```bash
npm test
```

Run backend tests:
```bash
pytest
```

### Build
```bash
# Frontend
npm run build

# Backend (Docker)
docker-compose build
```

---

## 🌐 Deployment

### Docker Production Build
```bash
docker-compose -f docker-compose.yml up -d --build
```

### Vercel Deployment
- Push to GitHub
- Connect repository to Vercel
- Configure environment variables
- Deploy automatically on push

---

## 📚 Additional Documentation

- **Admin Panel:** `docs/ADMIN_PANEL.md`
- **SM-2 Algorithm:** `docs/SM2_IMPROVEMENTS.md`
- **Security:** `docs/SECURITY_IMPROVEMENTS.md`
- **Redis Caching:** `docs/REDIS_CACHING.md`
- **AI Word Check:** `docs/AI_WORD_CHECK.md`
- **Deployment:** `docs/VERCEL_DEPLOYMENT.md`
- **Quick Reference:** `docs/QUICK_REFERENCE.md`
- **First Run Guide:** `docs/FIRST_RUN.md`

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📝 License

[Specify your license here]

---

## 📞 Support

For issues and questions:
- Open a GitHub issue
- Check existing documentation in `/docs`
- Review `GEMINI.md` for AI enrichment rules

---

**Last updated:** April 2026  
**Version:** 1.0.0
