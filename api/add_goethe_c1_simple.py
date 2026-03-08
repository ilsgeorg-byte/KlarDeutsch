#!/usr/bin/env python3
"""
Добавить слова уровня C1 (упрощенная версия)
"""

import os, sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

conn = psycopg2.connect(os.environ.get("POSTGRES_URL"))
cur = conn.cursor()

# Уникальные слова C1
C1_WORDS = [
    ("die Abstraktion", "абстракция"),
    ("die Ambition", "амбиция"),
    ("die Ambivalenz", "амбивалентность"),
    ("die Analogie", "аналогия"),
    ("die Anomalie", "аномалия"),
    ("die Antithese", "антитезис"),
    ("die Apologie", "апология"),
    ("die Apotheose", "апофеоз"),
    ("die Appellation", "апелляция"),
    ("die Applikation", "аппликация"),
    ("die Approximation", "аппроксимация"),
    ("die Äquivalenz", "эквивалентность"),
    ("die Argumentation", "аргументация"),
    ("die Artikulation", "артикуляция"),
    ("die Assoziation", "ассоциация"),
    ("die Assimilation", "ассимиляция"),
    ("die Asymmetrie", "асимметрия"),
    ("die Atmosphäre", "атмосфера"),
    ("die Attribution", "атрибуция"),
    ("die Authentizität", "аутентичность"),
    ("die Autonomie", "автономия"),
    ("die Avantgarde", "авангард"),
    ("die Aversion", "отвращение"),
    ("die Balance", "баланс"),
    ("die Barriere", "барьер"),
    ("die Bibliothek", "библиотека"),
    ("die Biografie", "биография"),
    ("die Biologie", "биология"),
    ("die Blamage", "позор"),
    ("die Bosheit", "злоба"),
    ("die Brisanz", "острота"),
    ("die Bürokratie", "бюрократия"),
    ("die Chance", "шанс"),
    ("die Charakteristik", "характеристика"),
    ("die Charisma", "харизма"),
    ("die Chemie", "химия"),
    ("die Chronik", "хроника"),
    ("die Chiffre", "шифр"),
    ("die Zivilisation", "цивилизация"),
    ("die Coalition", "коалиция"),
    ("die Codierung", "кодирование"),
    ("die Cognition", "познание"),
    ("die Cohärenz", "когерентность"),
    ("die Collage", "коллаж"),
    ("die Colloquium", "коллоквиум"),
    ("die Combination", "комбинация"),
    ("die Comedy", "комедия"),
    ("die Community", "сообщество"),
    ("die Compilation", "компиляция"),
    ("die Compliance", "соответствие"),
    ("die Complication", "осложнение"),
    ("die Composition", "композиция"),
    ("die Compromission", "компромисс"),
    ("die Conception", "концепция"),
    ("die Conclusion", "заключение"),
    ("die Concretion", "конкретизация"),
    ("die Condition", "условие"),
    ("die Conferenz", "конференция"),
    ("die Configuration", "конфигурация"),
    ("die Confrontation", "конфронтация"),
    ("die Confusion", "путаница"),
    ("die Congruenz", "конгруэнтность"),
    ("die Conjugation", "спряжение"),
    ("die Conjunction", "конъюнкция"),
    ("die Connexion", "связь"),
    ("die Connotation", "коннотация"),
    ("die Consequenz", "последствие"),
    ("die Conservation", "сохранение"),
    ("die Consideration", "рассмотрение"),
    ("die Consistenz", "консистентность"),
    ("die Consonanz", "консонанс"),
    ("die Constanz", "константность"),
    ("die Constitution", "конституция"),
    ("die Construction", "конструкция"),
    ("die Consultation", "консультация"),
    ("die Consumption", "потребление"),
    ("die Contamination", "загрязнение"),
    ("die Contemplation", "созерцание"),
    ("die Contestation", "оспаривание"),
    ("die Context", "контекст"),
    ("die Continuität", "непрерывность"),
    ("die Contraction", "сокращение"),
    ("die Contradiction", "противоречие"),
    ("die Contrast", "контраст"),
    ("die Contribution", "вклад"),
    ("die Contrition", "раскаяние"),
    ("die Controverse", "спор"),
    ("die Convention", "конвенция"),
    ("die Conversation", "разговор"),
    ("die Conversion", "преобразование"),
    ("die Conviction", "убеждение"),
    ("die Cooperation", "кооперация"),
    ("die Coordination", "координация"),
    ("die Correction", "коррекция"),
    ("die Correlation", "корреляция"),
    ("die Correspondenz", "корреспонденция"),
    ("die Corruption", "коррупция"),
    ("die Cosmologie", "космология"),
    ("die Courtoisie", "учтивость"),
    ("die Creation", "создание"),
    ("die Credibilität", "достоверность"),
    ("die Crew", "команда"),
    ("die Crise", "кризис"),
    ("die Critik", "критика"),
    ("die Culmination", "кульминация"),
    ("die Cultur", "культура"),
    ("die Cumulation", "кумуляция"),
    ("die Curiosity", "любопытство"),
    ("die Currency", "валюта"),
    ("die Currículum", "учебный план"),
    ("die Cursor", "курсор"),
    ("die Curve", "кривая"),
    ("die Custodie", "опека"),
    ("die Customisierung", "кастомизация"),
    ("die Cybernetik", "кибернетика"),
    ("die Cycle", "цикл"),
    ("die Cylind", "цилиндр"),
    ("die Cynismus", "цинизм"),
    ("die Dämonstration", "демонстрация"),
    ("die Dämpfung", "демпфирование"),
    ("die Dasein", "существование"),
    ("die Datenbank", "база данных"),
    ("die Dauer", "продолжительность"),
    ("die Debüt", "дебют"),
    ("die Decke", "потолок"),
    ("die Deduktion", "дедукция"),
    ("die Definition", "определение"),
    ("die Deformation", "деформация"),
    ("die Degeneration", "дегенерация"),
    ("die Degradierung", "деградация"),
    ("die Dehnung", "растяжение"),
    ("die Dekadenz", "декадентство"),
    ("die Deklamation", "декламация"),
    ("die Deklination", "склонение"),
    ("die Dekoration", "декорация"),
    ("die Delegation", "делегация"),
    ("die Delikatesse", "деликатес"),
    ("die Delikt", "деликт"),
    ("die Demagogie", "демагогия"),
    ("die Demenz", "деменция"),
    ("die Demission", "отставка"),
    ("die Demographie", "демография"),
    ("die Demonstration", "демонстрация"),
    ("die Demut", "смирение"),
    ("die Denunziation", "донос"),
    ("die Dependance", "филиал"),
    ("die Depression", "депрессия"),
    ("die Deputation", "депутация"),
    ("die Derivation", "деривация"),
    ("die Derogation", "дерогация"),
    ("die Desillusion", "разочарование"),
    ("die Desinfektion", "дезинфекция"),
    ("die Desintegration", "дезинтеграция"),
    ("die Deskription", "описание"),
    ("die Desolation", "запустение"),
    ("die Despotie", "деспотия"),
    ("die Destination", "назначение"),
    ("die Destillation", "дистилляция"),
    ("die Destruktion", "деструкция"),
    ("die Detektion", "детекция"),
    ("die Determination", "детерминация"),
    ("die Detonation", "детонация"),
    ("die Devianz", "девиантность"),
    ("die Devise", "девиз"),
    ("die Devotion", "преданность"),
    ("die Diät", "диета"),
    ("die Dichotomie", "дихотомия"),
    ("die Dichtung", "поэзия"),
    ("die Didaktik", "дидактика"),
    ("die Differenz", "разница"),
    ("die Diffusion", "диффузия"),
    ("die Digitalisierung", "цифровизация"),
    ("die Dignität", "достоинство"),
    ("die Dimension", "размер"),
    ("die Diminution", "уменьшение"),
    ("die Diphtherie", "дифтерия"),
    ("die Diplomatie", "дипломатия"),
    ("die Direktion", "дирекция"),
    ("die Disziplin", "дисциплина"),
    ("die Diskrepanz", "расхождение"),
    ("die Diskriminierung", "дискриминация"),
    ("die Diskussion", "дискуссия"),
    ("die Disparität", "неравенство"),
    ("die Dispensation", "диспенсация"),
    ("die Disposition", "диспозиция"),
    ("die Disputation", "диспут"),
    ("die Dissertation", "диссертация"),
    ("die Dissidenz", "диссидентство"),
    ("die Distanz", "дистанция"),
    ("die Distinktion", "различие"),
    ("die Distortion", "искажение"),
    ("die Distribution", "распределение"),
    ("die Diversifikation", "диверсификация"),
    ("die Diversität", "разнообразие"),
    ("die Diversion", "диверсия"),
    ("die Division", "деление"),
    ("die Doktrin", "доктрина"),
    ("die Dokumentation", "документация"),
    ("die Domäne", "домен"),
    ("die Dominanz", "доминирование"),
    ("die Donation", "пожертвование"),
    ("die Dosis", "доза"),
    ("die Dramatik", "драматизм"),
    ("die Dramaturgie", "драматургия"),
    ("die Drastik", "драстичность"),
    ("die Dreistigkeit", "наглость"),
    ("die Drohung", "угроза"),
    ("die Dualität", "дуальность"),
    ("die Dublette", "дубликат"),
    ("die Dummheit", "глупость"),
    ("die Duplizität", "двуличность"),
    ("die Dynamik", "динамика"),
    ("die Dysfunktion", "дисфункция"),
]

print("🔍 Добавление слов уровня C1...\n")

added_count = 0
existing_count = 0

for de, ru in C1_WORDS:
    # Определяем артикль
    article = None
    if de.startswith("der "):
        article = "der"
        de = de[4:]
    elif de.startswith("die "):
        article = "die"
        de = de[4:]
    elif de.startswith("das "):
        article = "das"
        de = de[4:]
    
    # Проверяем есть ли слово в базе
    cur.execute("""
        SELECT id FROM words 
        WHERE de ILIKE %s AND ru ILIKE %s AND level = 'C1'
    """, (de, ru))
    
    if cur.fetchone():
        existing_count += 1
    else:
        # Добавляем слово
        try:
            cur.execute("""
                INSERT INTO words (de, ru, article, level, topic, verb_forms)
                VALUES (%s, %s, %s, 'C1', 'Goethe C1', NULL)
            """, (de, ru, article))
            added_count += 1
        except Exception as e:
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                existing_count += 1
            else:
                print(f"❌ Ошибка: {e}")
                conn.rollback()

conn.commit()

print(f"\n📊 Итоги:")
print(f"   Добавлено: {added_count}")
print(f"   Уже было: {existing_count}")
print(f"   Всего проверено: {len(C1_WORDS)}")

cur.close()
conn.close()
