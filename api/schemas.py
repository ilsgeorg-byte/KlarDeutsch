"""
Pydantic схемы для валидации данных API KlarDeutsch
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
import re
from utils.sanitization_utils import (
    sanitize_string,
    sanitize_text_for_sql,
    sanitize_html_content,
    validate_level as validate_level_func,
    validate_word_rating,
    sanitize_email as sanitize_email_func,
    sanitize_username as sanitize_username_func,
    sanitize_password as sanitize_password_func
)


# === Общие типы ===

LevelType = Literal["A1", "A2", "B1", "B2", "C1"]
VALID_LEVELS = {"A1", "A2", "B1", "B2", "C1"}


# === Auth схемы ===

class UserRegister(BaseModel):
    """Схема регистрации пользователя"""
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    email: str = Field(..., min_length=5, max_length=100, description="Email")
    password: str = Field(..., min_length=6, max_length=128, description="Пароль")
    
    @field_validator('username')
    @classmethod
    def validate_and_sanitize_username(cls, v):
        return sanitize_username_func(v)
    
    @field_validator('email')
    @classmethod
    def validate_and_sanitize_email(cls, v):
        sanitized = sanitize_email_func(v)
        if not sanitized:
            raise ValueError('Неверный формат email')
        return sanitized
    
    @field_validator('password')
    @classmethod
    def validate_and_sanitize_password(cls, v):
        return sanitize_password_func(v)


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
    plural: Optional[str] = Field(default="", max_length=200, description="Множественное число")
    example_de: Optional[str] = Field(default="", max_length=500, description="Пример на немецком")
    example_ru: Optional[str] = Field(default="", max_length=500, description="Пример на русском")
    synonyms: Optional[str] = Field(default="", max_length=500, description="Синонимы")
    antonyms: Optional[str] = Field(default="", max_length=500, description="Антонимы")
    collocations: Optional[str] = Field(default="", max_length=500, description="Коллокации")
    examples: Optional[List[dict]] = Field(default_factory=list, description="Список примеров (JSON)")
    user_id: Optional[int] = None
    
    @field_validator('de', 'ru', 'article', 'topic', 'verb_forms', 'plural', 'example_de', 'example_ru', 'synonyms', 'antonyms', 'collocations')
    @classmethod
    def validate_and_sanitize_strings(cls, v):
        if v is None:
            return v
        return sanitize_text_for_sql(sanitize_string(v, max_length=500))
    
    @field_validator('level')
    @classmethod
    def validate_level_field(cls, v):
        if not validate_level_func(v):
            raise ValueError(f'Неверный уровень: {v}. Допустимые значения: A1, A2, B1, B2, C1')
        return v


class WordSearch(BaseModel):
    """Схема поиска слов"""
    query: str = Field(..., min_length=2, max_length=100, description="Поисковый запрос")
    limit: int = Field(default=50, ge=1, le=100, description="Максимум результатов")
    
    @field_validator('query')
    @classmethod
    def validate_and_sanitize_query(cls, v):
        return sanitize_text_for_sql(sanitize_string(v, max_length=100))


class WordQuery(BaseModel):
    """Схема query параметров для получения слов"""
    level: LevelType = Field(default="A1")
    skip: int = Field(default=0, ge=0, le=10000)
    limit: int = Field(default=100, ge=1, le=500)
    
    @field_validator('level')
    @classmethod
    def validate_level_field(cls, v):
        if not validate_level_func(v):
            raise ValueError(f'Неверный уровень: {v}. Допустимые значения: A1, A2, B1, B2, C1')
        return v


# === Trainer схемы ===

class RateWordRequest(BaseModel):
    """Схема оценки слова"""
    word_id: int = Field(..., gt=0, description="ID слова")
    rating: int = Field(..., description="Оценка: 0=Знаю, 1=Сложно, 3=Хорошо, 5=Легко")
    
    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        if not validate_word_rating(v):
            raise ValueError('Рейтинг должен быть 0, 1, 3 или 5')
        return v


class TrainingQuery(BaseModel):
    """Схема query параметров для тренировки"""
    level: LevelType = Field(default="A1")
    limit: int = Field(default=10, ge=1, le=100)
    
    @field_validator('level')
    @classmethod
    def validate_level_field(cls, v):
        if not validate_level_func(v):
            raise ValueError(f'Неверный уровень: {v}. Допустимые значения: A1, A2, B1, B2, C1')
        return v


# === Diary схемы ===

class DiaryCorrectionRequest(BaseModel):
    """Схема запроса коррекции текста"""
    text: str = Field(..., min_length=1, max_length=5000, description="Текст для коррекции")
    
    @field_validator('text')
    @classmethod
    def validate_and_sanitize_text(cls, v):
        return sanitize_text_for_sql(sanitize_string(v, max_length=5000))


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

class AIWordExample(BaseModel):
    """Схема примера предложения от AI"""
    de: str = Field(..., description="Пример на немецком")
    ru: str = Field(..., description="Перевод примера на русский")

class AIWordData(BaseModel):
    """Схема полных данных о слове, возвращаемых AI"""
    article: str = Field(default="", description="Артикль (der/die/das или пусто)")
    plural: str = Field(default="", description="Форма множественного числа (напр. die Schilder)")
    level: LevelType = Field(default="A1", description="Уровень (A1-C1)")
    verb_forms: str = Field(default="", description="Формы глагола: Infinitiv, Präsens(3sg), Präteritum(3sg), Partizip II")
    synonyms: str = Field(default="", description="Синонимы через запятую")
    antonyms: str = Field(default="", description="Антонимы через запятую")
    examples: List[AIWordExample] = Field(default_factory=list, description="Список примеров")

class AIEnrichRequest(BaseModel):
    """Схема запроса к AI для обогащения слова"""
    de: str = Field(..., min_length=1, max_length=200, description="Немецкое слово")
    ru: Optional[str] = Field(default="", max_length=200, description="Русский перевод (опционально)")
    
    @field_validator('de', 'ru')
    @classmethod
    def validate_and_sanitize_ai_request_fields(cls, v):
        if v is None:
            return v
        return sanitize_text_for_sql(sanitize_string(v, max_length=200))


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
    plural: Optional[str] = ""
    example_de: Optional[str] = ""
    example_ru: Optional[str] = ""
    synonyms: Optional[str] = ""
    antonyms: Optional[str] = ""
    collocations: Optional[str] = ""
    examples: Optional[List[dict]] = []
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
