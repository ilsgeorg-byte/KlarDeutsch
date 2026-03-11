import os
import sys

# Добавляем путь к текущей директории
sys.path.append(os.path.dirname(__file__))

from db import get_db_connection

# Категории: Дом, Еда, Офис, Город, Время, Эмоции, Природа
COMPREHENSIVE_WORDS = [
    # --- A1 (Basic Survival) ---
    {"level": "A1", "topic": "Дом", "de": "Tisch", "ru": "Стол", "article": "der", "example_de": "Der Tisch ist neu.", "example_ru": "Этот стол новый."},
    {"level": "A1", "topic": "Дом", "de": "Stuhl", "ru": "Стул", "article": "der", "example_de": "Hier ist ein Stuhl.", "example_ru": "Вот стул."},
    {"level": "A1", "topic": "Дом", "de": "Bett", "ru": "Кровать", "article": "das", "example_de": "Das Bett ist bequem.", "example_ru": "Кровать удобная."},
    {"level": "A1", "topic": "Дом", "de": "Fenster", "ru": "Окно", "article": "das", "example_de": "Mach das Fenster zu.", "example_ru": "Закрой окно."},
    {"level": "A1", "topic": "Дом", "de": "Tür", "ru": "Дверь", "article": "die", "example_de": "Die Tür ist offen.", "example_ru": "Дверь открыта."},
    {"level": "A1", "topic": "Еда", "de": "Salat", "ru": "Салат", "article": "der", "example_de": "Ich mag Salat.", "example_ru": "Я люблю салат."},
    {"level": "A1", "topic": "Еда", "de": "Suppe", "ru": "Суп", "article": "die", "example_de": "Die Suppe ist heiß.", "example_ru": "Суп горячий."},
    {"level": "A1", "topic": "Еда", "de": "Fisch", "ru": "Рыба", "article": "der", "example_de": "Fisch ist gesund.", "example_ru": "Рыба полезна."},
    {"level": "A1", "topic": "Еда", "de": "Reis", "ru": "Рис", "article": "der", "example_de": "Reis mit Gemüse.", "example_ru": "Рис с овощами."},
    {"level": "A1", "topic": "Еда", "de": "Saft", "ru": "Сок", "article": "der", "example_de": "Ein Apfelsaft, bitte.", "example_ru": "Яблочный сок, пожалуйста."},
    {"level": "A1", "topic": "Город", "de": "Straße", "ru": "Улица", "article": "die", "example_de": "Die Straße ist lang.", "example_ru": "Улица длинная."},
    {"level": "A1", "topic": "Город", "de": "Park", "ru": "Парк", "article": "der", "example_de": "Wir gehen in den Park.", "example_ru": "Мы идем в парк."},
    {"level": "A1", "topic": "Город", "de": "Supermarkt", "ru": "Супермаркет", "article": "der", "example_de": "Der Supermarkt ist groß.", "example_ru": "Супермаркет большой."},
    {"level": "A1", "topic": "Время", "de": "Tag", "ru": "День", "article": "der", "example_de": "Schönen Tag еще!", "example_ru": "Хорошего дня!"},
    {"level": "A1", "topic": "Время", "de": "Woche", "ru": "Неделя", "article": "die", "example_de": "Die Woche hat sieben Tage.", "example_ru": "В неделе семь дней."},
    {"level": "A1", "topic": "Время", "de": "Monat", "ru": "Месяц", "article": "der", "example_de": "Ein Monat имеет 30 Tage.", "example_ru": "В месяце 30 дней."},
    {"level": "A1", "topic": "Природа", "de": "Sonne", "ru": "Солнце", "article": "die", "example_de": "Die Sonne scheint.", "example_ru": "Солнце светит."},
    {"level": "A1", "topic": "Природа", "de": "Regen", "ru": "Дождь", "article": "der", "example_de": "Es gibt Regen heute.", "example_ru": "Сегодня идет дождь."},

    # --- A2 (Everyday life) ---
    {"level": "A2", "topic": "Офис", "de": "Drucker", "ru": "Принтер", "article": "der", "example_de": "Der Drucker ist kaputt.", "example_ru": "Принтер сломан."},
    {"level": "A2", "topic": "Офис", "de": "Computer", "ru": "Компьютер", "article": "der", "example_de": "Mein Computer ist schnell.", "example_ru": "Мой компьютер быстрый."},
    {"level": "A2", "topic": "Офис", "de": "Termin", "ru": "Встреча/Прием", "article": "der", "example_de": "Ich habe einen Termin.", "example_ru": "У меня назначена встреча."},
    {"level": "A2", "topic": "Офис", "de": "Kollegin", "ru": "Коллега (жен)", "article": "die", "example_de": "Meine Kollegin помогает мне.", "example_ru": "Моя коллега помогает мне."},
    {"level": "A2", "topic": "Магазин", "de": "Kleidung", "ru": "Одежда", "article": "die", "example_de": "Die Kleidung ist teuer.", "example_ru": "Одежда дорогая."},
    {"level": "A2", "topic": "Магазин", "de": "Schuh", "ru": "Ботинок", "article": "der", "example_de": "Dieser Schuh passt mir.", "example_ru": "Этот ботинок мне подходит."},
    {"level": "A2", "topic": "Магазин", "de": "Hemd", "ru": "Рубашка", "article": "das", "example_de": "Das Hemd является белым.", "example_ru": "Рубашка белая."},
    {"level": "A2", "topic": "Здоровье", "de": "Fieber", "ru": "Температура", "article": "das", "example_de": "Ich habe Fieber.", "example_ru": "У меня температура."},
    {"level": "A2", "topic": "Здоровье", "de": "Apotheke", "ru": "Аптека", "article": "die", "example_de": "Geh in die Apotheke.", "example_ru": "Сходи в аптеку."},
    {"level": "A2", "topic": "Эмоции", "de": "Freude", "ru": "Радость", "article": "die", "example_de": "Das macht mir Freude.", "example_ru": "Это приносит мне радость."},
    {"level": "A2", "topic": "Эмоции", "de": "Angst", "ru": "Страх", "article": "die", "example_de": "Hast du Angst?", "example_ru": "Тебе страшно?"},

    # --- B1 (Detailed Communication) ---
    {"level": "B1", "topic": "Культура", "de": "Erfolg", "ru": "Успех", "article": "der", "example_de": "Viel Erfolg!", "example_ru": "Большого успеха!"},
    {"level": "B1", "topic": "Культура", "de": "Bedeutung", "ru": "Значение", "article": "die", "example_de": "Was ist die Bedeutung?", "example_ru": "Какое значение?"},
    {"level": "B1", "topic": "СМИ", "de": "Nachricht", "ru": "Новость/Сообщение", "article": "die", "example_de": "Ich habe eine Nachricht.", "example_ru": "У меня есть сообщение."},
    {"level": "B1", "topic": "СМИ", "de": "Werbung", "ru": "Реклама", "article": "die", "example_de": "Die Werbung ist laut.", "example_ru": "Реклама громкая."},
    {"level": "B1", "topic": "Отношения", "de": "Nachbar", "ru": "Сосед", "article": "der", "example_de": "Mein Nachbar ist laut.", "example_ru": "Мой сосед шумный."},
    {"level": "B1", "topic": "Отношения", "de": "Geschenk", "ru": "Подарок", "article": "das", "example_de": "Das ist ein Geschenk.", "example_ru": "Это подарок."},
    {"level": "B1", "topic": "Окружение", "de": "Umwelt", "ru": "Окружающая среда", "article": "die", "example_de": "Wir schützen die Umwelt.", "example_ru": "Мы защищаем окружающую среду."},

    # --- Цвета и Качества (A1/A2) ---
    {"level": "A1", "topic": "Качества", "de": "neu", "ru": "новый", "article": "", "example_de": "Das Auto ist neu.", "example_ru": "Автомобиль новый."},
    {"level": "A1", "topic": "Качества", "de": "alt", "ru": "старый", "article": "", "example_de": "Das Haus ist alt.", "example_ru": "Дом старый."},
    {"level": "A1", "topic": "Качества", "de": "groß", "ru": "большой", "article": "", "example_de": "Die Stadt ist groß.", "example_ru": "Город боьшой."},
    {"level": "A1", "topic": "Качества", "de": "klein", "ru": "маленький", "article": "", "example_de": "Das Zimmer ist klein.", "example_ru": "Комната маленькая."},
    {"level": "A1", "topic": "Качества", "de": "gut", "ru": "хороший", "article": "", "example_de": "Das Wetter ist gut.", "example_ru": "Погода хорошая."},
    {"level": "A1", "topic": "Качества", "de": "schlecht", "ru": "плохой", "article": "", "example_de": "Das ist schlecht.", "example_ru": "Это плохо."},
    {"level": "A1", "topic": "Цвета", "de": "rot", "ru": "красный", "article": "", "example_de": "Der Apfel ist rot.", "example_ru": "Яблоко красное."},
    {"level": "A1", "topic": "Цвета", "de": "blau", "ru": "синий", "article": "", "example_de": "Der Himmel ist blau.", "example_ru": "Небо синее."},
    {"level": "A1", "topic": "Цвета", "de": "grün", "ru": "зеленый", "article": "", "example_de": "Das Gras ist grün.", "example_ru": "Трава зеленая."},
]

def seed_comprehensive():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        count = 0
        for w in COMPREHENSIVE_WORDS:
            cur.execute("SELECT id FROM words WHERE de = %s AND ru = %s", (w['de'], w['ru']))
            if cur.fetchone():
                continue

            cur.execute("""
                INSERT INTO words (level, topic, de, ru, article, example_de, example_ru)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (w['level'], w['topic'], w['de'], w['ru'], w.get('article', ''), w.get('example_de', ''), w.get('example_ru', '')))
            count += 1
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"Successfully added {count} common Goethe words.")
    except Exception as e:
        print(f"Error seeding comprehensive data: {e}")

if __name__ == "__main__":
    seed_comprehensive()
