#!/usr/bin/env python3
"""
Добавить слова уровня C1 (порция 2)
"""

import os, sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

# Слова C1 - порция 2
C1_WORDS_BATCH2 = [
    ("die Abstraktion", "абстракция", "die"),
    ("die Ambition", "амбиция", "die"),
    ("die Ambivalenz", "амбивалентность", "die"),
    ("die Analogie", "аналогия", "die"),
    ("die Anomalie", "аномалия", "die"),
    ("die Antithese", "антитезис", "die"),
    ("die Apologie", "апология", "die"),
    ("die Apotheose", "апофеоз", "die"),
    ("die Appellation", "апелляция", "die"),
    ("die Applikation", "аппликация", "die"),
    ("die Approximation", "аппроксимация", "die"),
    ("die Äquivalenz", "эквивалентность", "die"),
    ("die Argumentation", "аргументация", "die"),
    ("die Artikulation", "артикуляция", "die"),
    ("die Assoziation", "ассоциация", "die"),
    ("die Assimilation", "ассимиляция", "die"),
    ("die Asymmetrie", "асимметрия", "die"),
    ("die Atmosphäre", "атмосфера", "die"),
    ("die Attribution", "атрибуция", "die"),
    ("die Authentizität", "аутентичность", "die"),
    ("die Autonomie", "автономия", "die"),
    ("die Avantgarde", "авангард", "die"),
    ("die Aversion", "отвращение", "die"),
    ("die Balance", "баланс", "die"),
    ("die Barriere", "барьер", "die"),
    ("die Blamage", "позор", "die"),
    ("die Bosheit", "злоба", "die"),
    ("die Brisanz", "острота", "die"),
    ("die Bürokratie", "бюрократия", "die"),
    ("die Chance", "шанс", "die"),
    ("die Charakteristik", "характеристика", "die"),
    ("die Charisma", "харизма", "die"),
    ("die Chronik", "хроника", "die"),
    ("die Chiffre", "шифр", "die"),
    ("die Zivilisation", "цивилизация", "die"),
    ("die Coalition", "коалиция", "die"),
    ("die Codierung", "кодирование", "die"),
    ("die Cohärenz", "когерентность", "die"),
    ("die Collage", "коллаж", "die"),
    ("die Colloquium", "коллоквиум", "das"),
    ("die Combination", "комбинация", "die"),
    ("die Comedy", "комедия", "die"),
    ("die Community", "сообщество", "die"),
    ("die Compilation", "компиляция", "die"),
    ("die Compliance", "соответствие", "die"),
    ("die Complication", "осложнение", "die"),
    ("die Composition", "композиция", "die"),
    ("die Conception", "концепция", "die"),
    ("die Conclusion", "заключение", "die"),
    ("die Concretion", "конкретизация", "die"),
    ("die Condition", "условие", "die"),
    ("die Conferenz", "конференция", "die"),
    ("die Configuration", "конфигурация", "die"),
    ("die Confrontation", "конфронтация", "die"),
    ("die Confusion", "путаница", "die"),
    ("die Congruenz", "конгруэнтность", "die"),
    ("die Conjugation", "спряжение", "die"),
    ("die Conjunction", "конъюнкция", "die"),
    ("die Connexion", "связь", "die"),
    ("die Connotation", "коннотация", "die"),
    ("die Consequenz", "последствие", "die"),
    ("die Conservation", "сохранение", "die"),
    ("die Consideration", "рассмотрение", "die"),
    ("die Consistenz", "консистентность", "die"),
    ("die Consonanz", "консонанс", "die"),
    ("die Constanz", "константность", "die"),
    ("die Constitution", "конституция", "die"),
    ("die Construction", "конструкция", "die"),
    ("die Consultation", "консультация", "die"),
    ("die Consumption", "потребление", "die"),
    ("die Contamination", "загрязнение", "die"),
    ("die Contemplation", "созерцание", "die"),
    ("die Contestation", "оспаривание", "die"),
    ("die Context", "контекст", "der"),
    ("die Continuität", "непрерывность", "die"),
    ("die Contraction", "сокращение", "die"),
    ("die Contradiction", "противоречие", "die"),
    ("die Contrast", "контраст", "der"),
    ("die Contribution", "вклад", "die"),
    ("die Contrition", "раскаяние", "die"),
    ("die Controverse", "спор", "die"),
    ("die Convention", "конвенция", "die"),
    ("die Conversation", "разговор", "die"),
    ("die Conversion", "преобразование", "die"),
    ("die Conviction", "убеждение", "die"),
    ("die Cooperation", "кооперация", "die"),
    ("die Coordination", "координация", "die"),
    ("die Correction", "коррекция", "die"),
    ("die Correlation", "корреляция", "die"),
    ("die Correspondenz", "корреспонденция", "die"),
    ("die Corruption", "коррупция", "die"),
    ("die Cosmologie", "космология", "die"),
    ("die Courtoisie", "учтивость", "die"),
    ("die Creation", "создание", "die"),
    ("die Credibilität", "достоверность", "die"),
    ("die Crew", "команда", "die"),
    ("die Crise", "кризис", "die"),
    ("die Critik", "критика", "die"),
    ("die Culmination", "кульминация", "die"),
    ("die Cumulation", "кумуляция", "die"),
    ("die Curiosity", "любопытство", "die"),
    ("die Currency", "валюта", "die"),
    ("die Currículum", "учебный план", "das"),
    ("die Cursor", "курсор", "der"),
    ("die Curve", "кривая", "die"),
    ("die Custodie", "опека", "die"),
    ("die Customisierung", "кастомизация", "die"),
    ("die Cybernetik", "кибернетика", "die"),
    ("die Cycle", "цикл", "der"),
    ("die Cylind", "цилиндр", "der"),
    ("die Cynismus", "цинизм", "der"),
    ("die Dasein", "существование", "das"),
    ("die Datenbank", "база данных", "die"),
    ("die Dauer", "продолжительность", "die"),
    ("die Debüt", "дебют", "das"),
    ("die Deduktion", "дедукция", "die"),
    ("die Definition", "определение", "die"),
    ("die Deformation", "деформация", "die"),
    ("die Degeneration", "дегенерация", "die"),
    ("die Degradierung", "деградация", "die"),
    ("die Dehnung", "растяжение", "die"),
    ("die Dekadenz", "декадентство", "die"),
    ("die Deklamation", "декламация", "die"),
    ("die Deklination", "склонение", "die"),
    ("die Dekoration", "декорация", "die"),
    ("die Delegation", "делегация", "die"),
    ("die Delikatesse", "деликатес", "die"),
    ("die Delikt", "деликт", "das"),
    ("die Demagogie", "демагогия", "die"),
    ("die Demenz", "деменция", "die"),
    ("die Demission", "отставка", "die"),
    ("die Demographie", "демография", "die"),
    ("die Demonstration", "демонстрация", "die"),
    ("die Demut", "смирение", "die"),
    ("die Denunziation", "донос", "die"),
    ("die Dependance", "филиал", "die"),
    ("die Depression", "депрессия", "die"),
    ("die Deputation", "депутация", "die"),
    ("die Derivation", "деривация", "die"),
    ("die Derogation", "дерогация", "die"),
    ("die Desillusion", "разочарование", "die"),
    ("die Desinfektion", "дезинфекция", "die"),
    ("die Desintegration", "дезинтеграция", "die"),
    ("die Deskription", "описание", "die"),
    ("die Desolation", "запустение", "die"),
    ("die Despotie", "деспотия", "die"),
    ("die Destination", "назначение", "die"),
    ("die Destillation", "дистилляция", "die"),
    ("die Destruktion", "деструкция", "die"),
    ("die Detektion", "детекция", "die"),
    ("die Determination", "детерминация", "die"),
    ("die Detonation", "детонация", "die"),
    ("die Devianz", "девиантность", "die"),
    ("die Devise", "девиз", "die"),
    ("die Devotion", "преданность", "die"),
    ("die Diät", "диета", "die"),
    ("die Dichotomie", "дихотомия", "die"),
    ("die Dichtung", "поэзия", "die"),
    ("die Didaktik", "дидактика", "die"),
    ("die Differenz", "разница", "die"),
    ("die Diffusion", "диффузия", "die"),
    ("die Digitalisierung", "цифровизация", "die"),
    ("die Dignität", "достоинство", "die"),
    ("die Dimension", "размер", "die"),
    ("die Diminution", "уменьшение", "die"),
    ("die Diplomatie", "дипломатия", "die"),
    ("die Direktion", "дирекция", "die"),
    ("die Disziplin", "дисциплина", "die"),
    ("die Diskrepanz", "расхождение", "die"),
    ("die Diskriminierung", "дискриминация", "die"),
    ("die Diskussion", "дискуссия", "die"),
    ("die Disparität", "неравенство", "die"),
    ("die Dispensation", "диспенсация", "die"),
    ("die Disposition", "диспозиция", "die"),
    ("die Disputation", "диспут", "die"),
    ("die Dissertation", "диссертация", "die"),
    ("die Dissidenz", "диссидентство", "die"),
    ("die Distanz", "дистанция", "die"),
    ("die Distinktion", "различие", "die"),
    ("die Distortion", "искажение", "die"),
    ("die Distribution", "распределение", "die"),
    ("die Diversifikation", "диверсификация", "die"),
    ("die Diversität", "разнообразие", "die"),
    ("die Diversion", "диверсия", "die"),
    ("die Division", "деление", "die"),
    ("die Doktrin", "доктрина", "die"),
    ("die Dokumentation", "документация", "die"),
    ("die Domäne", "домен", "die"),
    ("die Dominanz", "доминирование", "die"),
    ("die Donation", "пожертвование", "die"),
    ("die Dosis", "доза", "die"),
    ("die Dramatik", "драматизм", "die"),
    ("die Dramaturgie", "драматургия", "die"),
    ("die Drastik", "драстичность", "die"),
    ("die Dreistigkeit", "наглость", "die"),
    ("die Drohung", "угроза", "die"),
    ("die Dualität", "дуальность", "die"),
    ("die Dublette", "дубликат", "die"),
    ("die Dummheit", "глупость", "die"),
    ("die Duplizität", "двуличность", "die"),
    ("die Dynamik", "динамика", "die"),
    ("die Dysfunktion", "дисфункция", "die"),
]

print("🔍 Добавление слов уровня C1 (порция 2)...\n")

conn = None
cur = None
try:
    conn = psycopg2.connect(os.environ.get("POSTGRES_URL"))
    cur = conn.cursor()

    added_count = 0
    existing_count = 0
    error_count = 0

    for de, ru, article in C1_WORDS_BATCH2:
        try:
            # Проверяем есть ли слово в базе
            cur.execute("""
                SELECT id FROM words
                WHERE de ILIKE %s AND ru ILIKE %s AND level = 'C1'
            """, (de, ru))

            if cur.fetchone():
                existing_count += 1
            else:
                # Добавляем слово
                cur.execute("""
                    INSERT INTO words (de, ru, article, level, topic, verb_forms)
                    VALUES (%s, %s, %s, 'C1', 'Goethe C1', NULL)
                """, (de, ru, article))
                added_count += 1

        except Exception as e:
            if "duplicate" not in str(e).lower() and "unique" not in str(e).lower():
                error_count += 1
                print(f"❌ Ошибка с '{de}': {e}")
                if conn:
                    conn.rollback()

    conn.commit()

    print(f"\n📊 Итоги:")
    print(f"   Добавлено: {added_count}")
    print(f"   Уже было: {existing_count}")
    print(f"   Ошибок: {error_count}")
    print(f"   Всего проверено: {len(C1_WORDS_BATCH2)}")

except Exception as e:
    print(f"❌ Критическая ошибка: {e}")
    if conn:
        conn.rollback()
finally:
    if cur:
        cur.close()
    if conn:
        conn.close()
