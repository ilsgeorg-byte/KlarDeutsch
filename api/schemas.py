"""
Pydantic схемы для валидации данных API KlarDeutsch
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal


# === Общие типы ===

LevelType = Literal["A1", "A2", "B1", "B2", "C1"]
VALID_LEVELS = {"A1", "A2", "B1", "B2", "C1"}


# === Auth схемы ===

class UserRegister(BaseModel):
    """Схема регистрации пользователя"""
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    email: str = Field(..., min_length=5, max_length=100, description="Email")
    password: str = Field(..., min_length=6, max_length=128, description="Пароль")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if '@' not in v or '.' not in v.split('@')[-1]:
            raise ValueError('Неверный формат email')
        return v


class UserLogin(BaseModel):
    """Схема входа пользователя"""
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=1, max_length=128)


# === Words схемы ===

class WordCreate(BaseModel):
    """Схема создания слова"""
    de: str = Field(..., min_length=1, max_length=200, description="Немецкое слово")
    ru: str = Field(..., min_length=1, max_length=200, description="Русский перевод")
    article: Optional[str] = Field(default="", max_length=10, description="Артикль")
    level: LevelType = Field(default="A1", description="Уровень")
    topic: Optional[str] = Field(default="Общее", max_length=100, description="Тема")
    verb_forms: Optional[str] = Field(default="", max_length=200, description="Формы глагола")
    example_de: Optional[str] = Field(default="", max_length=500, description="Пример на немецком")
    example_ru: Optional[str] = Field(default="", max_length=500, description="Пример на русском")
    user_id: Optional[int] = None


class WordSearch(BaseModel):
    """Схема поиска слов"""
    query: str = Field(..., min_length=2, max_length=100, description="Поисковый запрос")
    limit: int = Field(default=50, ge=1, le=100, description="Максимум результатов")


class WordQuery(BaseModel):
    """Схема query параметров для получения слов"""
    level: LevelType = Field(default="A1")
    skip: int = Field(default=0, ge=0, le=10000)
    limit: int = Field(default=100, ge=1, le=500)


# === Trainer схемы ===

class RateWordRequest(BaseModel):
    """Схема оценки слова"""
    word_id: int = Field(..., gt=0, description="ID слова")
    rating: int = Field(..., description="Оценка: 0=Знаю, 1=Сложно, 3=Хорошо, 5=Легко")
    
    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        if v not in [0, 1, 3, 5]:
            raise ValueError('Рейтинг должен быть 0, 1, 3 или 5')
        return v


class TrainingQuery(BaseModel):
    """Схема query параметров для тренировки"""
    level: LevelType = Field(default="A1")
    limit: int = Field(default=10, ge=1, le=100)


# === Diary схемы ===

class DiaryCorrectionRequest(BaseModel):
    """Схема запроса коррекции текста"""
    text: str = Field(..., min_length=1, max_length=5000, description="Текст для коррекции")


class DiaryWordsAdd(BaseModel):
    """Схема добавления слов из дневника"""
    words: List[dict] = Field(default_factory=list)
    
    @field_validator('words')
    @classmethod
    def validate_words(cls, v):
        if len(v) > 50:
            raise ValueError('Максимум 50 слов за раз')
        for w in v:
            if not isinstance(w, dict):
                raise ValueError('Каждое слово должно быть объектом')
            if 'de' not in w or 'ru' not in w:
                raise ValueError('Слово должно содержать de и ru')
        return v


# === Audio схемы ===

class AudioUploadRequest(BaseModel):
    """Схема загрузки аудио (для документации)"""
    file: str = Field(..., description="Аудиофайл (webm, mp3, wav, ogg)")
    # Фактическая валидка происходит в роуте через request.files


class AudioListQuery(BaseModel):
    """Схема query параметров для списка аудио"""
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class AudioDeleteRequest(BaseModel):
    """Схема удаления аудио"""
    filename: str = Field(..., min_length=1, max_length=500, description="Имя файла")


# === AI Enrich схемы ===

class AIEnrichRequest(BaseModel):
    """Схема запроса к AI для обогащения слова"""
    de: str = Field(..., min_length=1, max_length=200, description="Немецкое слово")
    ru: Optional[str] = Field(default="", max_length=200, description="Русский перевод (опционально)")


# === Response схемы ===

class WordResponse(BaseModel):
    """Схема ответа с словом"""
    id: int
    level: str
    topic: Optional[str]
    de: str
    ru: str
    article: Optional[str]
    verb_forms: Optional[str]
    example_de: Optional[str]
    example_ru: Optional[str]
    audio_url: Optional[str]
    is_favorite: bool = False


class PaginatedWordsResponse(BaseModel):
    """Схема пагинированного ответа"""
    data: List[WordResponse]
    total: int
    skip: int
    limit: int


class StatsResponse(BaseModel):
    """Схема статистики"""
    total_words: dict
    user_progress: dict
    detailed: List[dict]


# === Error схемы ===

class ErrorResponse(BaseModel):
    """Схема ошибки"""
    error: str
    details: Optional[str] = None
