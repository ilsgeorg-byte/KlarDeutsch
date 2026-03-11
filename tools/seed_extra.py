import os
import sys

# Добавляем путь к текущей директории
sys.path.append(os.path.dirname(__file__))

from db import get_db_connection

NEW_WORDS = [
    # A1 - Личные данные
    {"level": "A1", "topic": "Личные данные", "de": "Name", "ru": "Имя/Фамилия", "article": "der", "example_de": "Mein Name ist Hans.", "example_ru": "Меня зовут Ганс."},
    {"level": "A1", "topic": "Личные данные", "de": "Adresse", "ru": "Адрес", "article": "die", "example_de": "Wie ist deine Adresse?", "example_ru": "Какой твой адрес?"},
    {"level": "A1", "topic": "Личные данные", "de": "Alter", "ru": "Возраст", "article": "das", "example_de": "Wie ist dein Alter?", "example_ru": "Каков твой возраст?"},
    {"level": "A1", "topic": "Личные данные", "de": "Beruf", "ru": "Профессия", "article": "der", "example_de": "Ich bin Lehrer von Beruf.", "example_ru": "Я учитель по профессии."},
    {"level": "A1", "topic": "Личные данные", "de": "Frau", "ru": "Женщина/Госпожа", "article": "die", "example_de": "Das ist Frau Müller.", "example_ru": "Это госпожа Мюллер."},
    {"level": "A1", "topic": "Личные данные", "de": "Herr", "ru": "Мужчина/Господин", "article": "der", "example_de": "Guten Tag, Herr Schmidt!", "example_ru": "Добрый день, господин Шмидт!"},
    {"level": "A1", "topic": "Личные данные", "de": "Kind", "ru": "Ребёнок", "article": "das", "example_de": "Das Kind spielt.", "example_ru": "Ребёнок играет."},
    {"level": "A1", "topic": "Личные данные", "de": "Wohnort", "ru": "Место жительства", "article": "der", "example_de": "Mein Wohnort ist Berlin.", "example_ru": "Мое место жительства - Берлин."},

    # A1 - Покупки и еда
    {"level": "A1", "topic": "Еда", "de": "Bier", "ru": "Пиво", "article": "das", "example_de": "Ein Bier, bitte.", "example_ru": "Одно пиво, пожалуйста."},
    {"level": "A1", "topic": "Еда", "de": "Fleisch", "ru": "Мясо", "article": "das", "example_de": "Ich esse kein Fleisch.", "example_ru": "Я не ем мясо."},
    {"level": "A1", "topic": "Еда", "de": "Gemüse", "ru": "Овощи", "article": "das", "example_de": "Gemüse является здоровым.", "example_ru": "Овощи полезны."},
    {"level": "A1", "topic": "Еда", "de": "Obst", "ru": "Фрукты", "article": "das", "example_de": "Obst mag я очень.", "example_ru": "Я очень люблю фрукты."},
    {"level": "A1", "topic": "Еда", "de": "Rechnung", "ru": "Счёт", "article": "die", "example_de": "Die Rechnung, bitte.", "example_ru": "Счёт, пожалуйста."},
    {"level": "A1", "topic": "Еда", "de": "Wein", "ru": "Вино", "article": "der", "example_de": "Der Wein ist gut.", "example_ru": "Вино хорошее."},
    {"level": "A1", "topic": "Еда", "de": "Zucker", "ru": "Сахар", "article": "der", "example_de": "Mit Zucker, bitte.", "example_ru": "С сахаром, пожалуйста."},

    # A1 - Транспорт и время
    {"level": "A1", "topic": "Транспорт", "de": "Bahnhof", "ru": "Вокзал", "article": "der", "example_de": "Wo ist der Bahnhof?", "example_ru": "Где вокзал?"},
    {"level": "A1", "topic": "Транспорт", "de": "Fahrkarte", "ru": "Проездной билет", "article": "die", "example_de": "Ich brauche eine Fahrkarte.", "example_ru": "Мне нужен билет."},
    {"level": "A1", "topic": "Транспорт", "de": "Flughafen", "ru": "Аэропорт", "article": "der", "example_de": "Das Taxi fährt zum Flughafen.", "example_ru": "Такси едет в аэропорт."},
    {"level": "A1", "topic": "Транспорт", "de": "Bus", "ru": "Автобус", "article": "der", "example_de": "Der Bus kommt um 8 Uhr.", "example_ru": "Автобус приходит в 8 часов."},
    {"level": "A1", "topic": "Транспорт", "de": "U-Bahn", "ru": "Метро", "article": "die", "example_de": "Wir fahren mit der U-Bahn.", "example_ru": "Мы едем на метро."},

    # A2 - Работа и Офис
    {"level": "A2", "topic": "Работа", "de": "Kollege", "ru": "Коллега", "article": "der", "example_de": "Mein Kollege ist nett.", "example_ru": "Мой коллега милый."},
    {"level": "A2", "topic": "Работа", "de": "Chef", "ru": "Начальник", "article": "der", "example_de": "Der Chef ist im Büro.", "example_ru": "Начальник в офисе."},
    {"level": "A2", "topic": "Работа", "de": "Besprechung", "ru": "Совещание", "article": "die", "example_de": "Die Besprechung dauert lange.", "example_ru": "Совещание длится долго."},
    {"level": "A2", "topic": "Работа", "de": "Gehalt", "ru": "Зарплата", "article": "das", "example_de": "Das Gehalt ist pünktlich.", "example_ru": "Зарплата вовремя."},

    # A2 - Здоровье
    {"level": "A2", "topic": "Здоровье", "de": "Krankenhaus", "ru": "Больница", "article": "das", "example_de": "Er ist im Krankenhaus.", "example_ru": "Он в больнице."},
    {"level": "A2", "topic": "Здоровье", "de": "Medikament", "ru": "Лекарство", "article": "das", "example_de": "Ich nehme ein Medikament.", "example_ru": "Я принимаю лекарство."},
    {"level": "A2", "topic": "Здоровье", "de": "Schmerzen", "ru": "Боли", "article": "die", "example_de": "Ich habe Kopfschmerzen.", "example_ru": "У меня болит голова."},

    # B1 - Абстрактные понятия
    {"level": "B1", "topic": "Общество", "de": "Erfahrung", "ru": "Опыт", "article": "die", "example_de": "Er hat viel Erfahrung.", "example_ru": "У него много опыта."},
    {"level": "B1", "topic": "Общество", "de": "Entscheidung", "ru": "Решение", "article": "die", "example_de": "Das ist eine wichtige Entscheidung.", "example_ru": "Это важное решение."},
    {"level": "B1", "topic": "Общество", "de": "Verantwortung", "ru": "Ответственность", "article": "die", "example_de": "Du hast Verantwortung.", "example_ru": "У тебя есть ответственность."},
]

def seed_extra():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        count = 0
        for w in NEW_WORDS:
            cur.execute("SELECT id FROM words WHERE de = %s AND ru = %s", (w['de'], w['ru']))
            if cur.fetchone():
                continue

            cur.execute("""
                INSERT INTO words (level, topic, de, ru, article, example_de, example_ru)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (w['level'], w['topic'], w['de'], w['ru'], w['article'], w['example_de'], w['example_ru']))
            count += 1
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"Successfully added {count} new core words.")
    except Exception as e:
        print(f"Error seeding extra data: {e}")

if __name__ == "__main__":
    seed_extra()
