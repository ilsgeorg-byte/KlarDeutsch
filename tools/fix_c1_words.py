#!/usr/bin/env python3
"""
Исправить слова C1 - добавить артикли и примеры
"""

import os, sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

conn = None
cur = None
try:
    conn = psycopg2.connect(os.environ.get("POSTGRES_URL"))
    cur = conn.cursor()

    # Слова C1 с артиклями и примерами
    C1_CORRECTIONS = {
    # die-слова
    "die Abstraktion": ("die", "абстракция", "Die Abstraktion ist ein wichtiger Prozess.", "Абстракция — важный процесс."),
    "die Ambition": ("die", "амбиция", "Seine Ambition ist bewundernswert.", "Его амбиция восхитительна."),
    "die Ambivalenz": ("die", "амбивалентность", "Die Ambivalenz der Gefühle ist normal.", "Амбивалентность чувств нормальна."),
    "die Analogie": ("die", "аналогия", "Die Analogie zwischen den Fällen ist offensichtlich.", "Аналогия между случаями очевидна."),
    "die Anomalie": ("die", "аномалия", "Diese Anomalie muss untersucht werden.", "Эта аномалия должна быть исследована."),
    "die Antithese": ("die", "антитезис", "Die Antithese zur These ist die Negation.", "Антитезис к тезису — отрицание."),
    "die Apologie": ("die", "апология", "Das ist eine Apologie des Systems.", "Это апология системы."),
    "die Apotheose": ("die", "апофеоз", "Die Apotheose des Dramas war beeindruckend.", "Апофеоз драмы был впечатляющим."),
    "die Appellation": ("die", "апелляция", "Die Appellation wurde abgelehnt.", "Апелляция была отклонена."),
    "die Applikation": ("die", "аппликация", "Die Applikation der Methode war erfolgreich.", "Аппликация метода была успешной."),
    "die Approximation": ("die", "аппроксимация", "Die Approximation ist ausreichend genau.", "Аппроксимация достаточно точна."),
    "die Äquivalenz": ("die", "эквивалентность", "Die Äquivalenz der Aussagen ist bewiesen.", "Эквивалентность утверждений доказана."),
    "die Argumentation": ("die", "аргументация", "Seine Argumentation war überzeugend.", "Его аргументация была убедительной."),
    "die Artikulation": ("die", "артикуляция", "Die Artikulation war deutlich.", "Артикуляция была четкой."),
    "die Assoziation": ("die", "ассоциация", "Diese Assoziation ist sehr stark.", "Эта ассоциация очень сильная."),
    "die Assimilation": ("die", "ассимиляция", "Die Assimilation dauert Generationen.", "Ассимиляция длится поколениями."),
    "die Asymmetrie": ("die", "асимметрия", "Die Asymmetrie ist auffällig.", "Асимметрия бросается в глаза."),
    "die Atmosphäre": ("die", "атмосфера", "Die Atmosphäre war angespannt.", "Атмосфера была напряженной."),
    "die Attribution": ("die", "атрибуция", "Die Attribution der Verantwortung ist wichtig.", "Атрибуция ответственности важна."),
    "die Authentizität": ("die", "аутентичность", "Die Authentizität des Dokuments ist bestätigt.", "Аутентичность документа подтверждена."),
    "die Autonomie": ("die", "автономия", "Die Autonomie der Region wurde erweitert.", "Автономия региона была расширена."),
    "die Avantgarde": ("die", "авангард", "Die Avantgarde der Kunst war revolutionär.", "Авангард искусства был революционным."),
    "die Aversion": ("die", "отвращение", "Er hat eine Aversion gegen Spinat.", "У него отвращение к шпинату."),
    "die Balance": ("die", "баланс", "Die Balance ist gestört.", "Баланс нарушен."),
    "die Barriere": ("die", "барьер", "Die Barriere wurde überwunden.", "Барьер был преодолен."),
    "die Blamage": ("die", "позор", "Das war eine echte Blamage.", "Это был настоящий позор."),
    "die Bosheit": ("die", "злоба", "Die Bosheit war unübersehbar.", "Злоба была неоспорима."),
    "die Brisanz": ("die", "острота", "Die Brisanz des Themas ist hoch.", "Острота темы высока."),
    "die Bürokratie": ("die", "бюрократия", "Die Bürokratie ist übermäßig.", "Бюрократия чрезмерна."),
    "die Chance": ("die", "шанс", "Das ist deine Chance!", "Это твой шанс!"),
    "die Charakteristik": ("die", "характеристика", "Die Charakteristik ist treffend.", "Характеристика точна."),
    "die Charisma": ("die", "харизма", "Seine Charisma ist beeindruckend.", "Его харизма впечатляет."),
    "die Chronik": ("die", "хроника", "Die Chronik dokumentiert die Ereignisse.", "Хроника документирует события."),
    "die Chiffre": ("die", "шифр", "Die Chiffre wurde entschlüsselt.", "Шифр был расшифрован."),
    "die Zivilisation": ("die", "цивилизация", "Die Zivilisation entwickelte sich schnell.", "Цивилизация развивалась быстро."),
    "die Coalition": ("die", "коалиция", "Die Coalition wurde gebildet.", "Коалиция была сформирована."),
    "die Codierung": ("die", "кодирование", "Die Codierung ist komplex.", "Кодирование сложное."),
    "die Cohärenz": ("die", "когерентность", "Die Cohärenz der Wellen ist wichtig.", "Когерентность волн важна."),
    "die Collage": ("die", "коллаж", "Die Collage ist kreativ.", "Коллаж креативный."),
    "die Colloquium": ("die", "коллоквиум", "Das Colloquium findet morgen statt.", "Коллоквиум состоится завтра."),
    "die Combination": ("die", "комбинация", "Die Combination ist effektiv.", "Комбинация эффективна."),
    "die Comedy": ("die", "комедия", "Die Comedy war lustig.", "Комедия была смешной."),
    "die Community": ("die", "сообщество", "Die Community ist aktiv.", "Сообщество активное."),
    "die Compilation": ("die", "компиляция", "Die Compilation ist abgeschlossen.", "Компиляция завершена."),
    "die Compliance": ("die", "соответствие", "Die Compliance ist erforderlich.", "Соответствие требуется."),
    "die Complication": ("die", "осложнение", "Die Complication war unerwartet.", "Осложнение было неожиданным."),
    "die Composition": ("die", "композиция", "Die Composition ist ausgewogen.", "Композиция сбалансирована."),
    "die Conception": ("die", "концепция", "Die Conception ist innovativ.", "Концепция инновационна."),
    "die Conclusion": ("die", "заключение", "Die Conclusion ist logisch.", "Заключение логично."),
    "die Concretion": ("die", "конкретизация", "Die Concretion fehlt noch.", "Конкретизация еще отсутствует."),
    "die Condition": ("die", "условие", "Die Condition muss erfüllt sein.", "Условие должно быть выполнено."),
    "die Conferenz": ("die", "конференция", "Die Conferenz war erfolgreich.", "Конференция была успешной."),
    "die Configuration": ("die", "конфигурация", "Die Configuration ist optimal.", "Конфигурация оптимальна."),
    "die Confrontation": ("die", "конфронтация", "Die Confrontation war unvermeidlich.", "Конфронтация была неизбежна."),
    "die Confusion": ("die", "путаница", "Die Confusion war groß.", "Путаница была большой."),
    "die Congruenz": ("die", "конгруэнтность", "Die Congruenz ist gegeben.", "Конгруэнтность имеется."),
    "die Conjugation": ("die", "спряжение", "Die Conjugation ist unregelmäßig.", "Спряжение неправильное."),
    "die Conjunction": ("die", "конъюнкция", "Die Conjunction ist wahr.", "Конъюнкция истинна."),
    "die Connexion": ("die", "связь", "Die Connexion ist stark.", "Связь сильная."),
    "die Connotation": ("die", "коннотация", "Die Connotation ist positiv.", "Коннотация позитивная."),
    "die Consequenz": ("die", "последствие", "Die Consequenz war vorhersehbar.", "Последствие было предсказуемо."),
    "die Conservation": ("die", "сохранение", "Die Conservation ist wichtig.", "Сохранение важно."),
    "die Consideration": ("die", "рассмотрение", "Die Consideration dauert an.", "Рассмотрение продолжается."),
    "die Consistenz": ("die", "консистентность", "Die Consistenz ist perfekt.", "Консистентность идеальна."),
    "die Consonanz": ("die", "консонанс", "Die Consonanz ist harmonisch.", "Консонанс гармоничен."),
    "die Constanz": ("die", "константность", "Die Constanz ist bemerkenswert.", "Константность примечательна."),
    "die Constitution": ("die", "конституция", "Die Constitution wurde verabschiedet.", "Конституция была принята."),
    "die Construction": ("die", "конструкция", "Die Construction ist stabil.", "Конструкция стабильна."),
    "die Consultation": ("die", "консультация", "Die Consultation war hilfreich.", "Консультация была полезной."),
    "die Consumption": ("die", "потребление", "Die Consumption steigt.", "Потребление растет."),
    "die Contamination": ("die", "загрязнение", "Die Contamination ist gefährlich.", "Загрязнение опасно."),
    "die Contemplation": ("die", "созерцание", "Die Contemplation beruhigt.", "Созерцание успокаивает."),
    "die Contestation": ("die", "оспаривание", "Die Contestation ist berechtigt.", "Оспаривание обосновано."),
    "die Context": ("die", "контекст", "Der Context ist wichtig.", "Контекст важен."),
    "die Continuität": ("die", "непрерывность", "Die Continuität ist gewährleistet.", "Непрерывность обеспечена."),
    "die Contraction": ("die", "сокращение", "Die Contraction ist messbar.", "Сокращение измеримо."),
    "die Contradiction": ("die", "противоречие", "Die Contradiction ist offensichtlich.", "Противоречие очевидно."),
    "die Contrast": ("die", "контраст", "Der Contrast ist stark.", "Контраст сильный."),
    "die Contribution": ("die", "вклад", "Sein Contribution war wertvoll.", "Его вклад был ценным."),
    "die Contrition": ("die", "раскаяние", "Die Contrition war aufrichtig.", "Раскаяние было искренним."),
    "die Controverse": ("die", "спор", "Die Controverse dauert an.", "Спор продолжается."),
    "die Convention": ("die", "конвенция", "Die Convention wurde unterzeichnet.", "Конвенция была подписана."),
    "die Conversation": ("die", "разговор", "Die Conversation war angenehm.", "Разговор был приятным."),
    "die Conversion": ("die", "преобразование", "Die Conversion ist abgeschlossen.", "Преобразование завершено."),
    "die Conviction": ("die", "убеждение", "Seine Conviction ist stark.", "Его убеждение сильно."),
    "die Cooperation": ("die", "кооперация", "Die Cooperation war erfolgreich.", "Кооперация была успешной."),
    "die Coordination": ("die", "координация", "Die Coordination fehlt.", "Координация отсутствует."),
    "die Correction": ("die", "коррекция", "Die Correction ist notwendig.", "Коррекция необходима."),
    "die Correlation": ("die", "корреляция", "Die Correlation ist signifikant.", "Корреляция значима."),
    "die Correspondenz": ("die", "корреспонденция", "Die Correspondenz ist eingegangen.", "Корреспонденция поступила."),
    "die Corruption": ("die", "коррупция", "Die Corruption muss bekämpft werden.", "Коррупция должна быть искоренена."),
    "die Cosmologie": ("die", "космология", "Die Cosmologie ist faszinierend.", "Космология захватывающая."),
    "die Courtoisie": ("die", "учтивость", "Die Courtoisie ist bemerkenswert.", "Учтивость примечательна."),
    "die Creation": ("die", "создание", "Die Creation war erfolgreich.", "Создание было успешным."),
    "die Credibilität": ("die", "достоверность", "Die Credibilität ist angezweifelt.", "Достоверность поставлена под сомнение."),
    "die Crew": ("die", "команда", "Die Crew ist erfahren.", "Команда опытная."),
    "die Crise": ("die", "кризис", "Die Crise ist überwunden.", "Кризис преодолен."),
    "die Critik": ("die", "критика", "Die Critik war konstruktiv.", "Критика была конструктивной."),
    "die Culmination": ("die", "кульминация", "Die Culmination war spektakulär.", "Кульминация была spektakulär."),
    "die Cumulation": ("die", "кумуляция", "Die Cumulation ist abgeschlossen.", "Кумуляция завершена."),
    "die Curiosity": ("die", "любопытство", "Die Curiosity ist natürlich.", "Любопытство естественно."),
    "die Currency": ("die", "валюта", "Die Currency ist stabil.", "Валюта стабильна."),
    "die Currículum": ("die", "учебный план", "Das Currículum ist umfassend.", "Учебный план обширный."),
    "die Cursor": ("die", "курсор", "Der Cursor bewegt sich.", "Курсор движется."),
    "die Curve": ("die", "кривая", "Die Curve ist steil.", "Кривая крутая."),
    "die Custodie": ("die", "опека", "Die Custodie wurde übertragen.", "Опека была передана."),
    "die Customisierung": ("die", "кастомизация", "Die Customisierung ist möglich.", "Кастомизация возможна."),
    "die Cybernetik": ("die", "кибернетика", "Die Cybernetik ist interdisziplinär.", "Кибернетика междисциплинарна."),
    "die Cycle": ("die", "цикл", "Der Cycle wiederholt sich.", "Цикл повторяется."),
    "die Cylind": ("die", "цилиндр", "Der Cylind ist hohl.", "Цилиндр полый."),
    "die Cynismus": ("die", "цинизм", "Der Cynismus ist auffällig.", "Цинизм бросается в глаза."),
    
    # der-слова
    "der Context": ("der", "контекст", "Der Context ist wichtig.", "Контекст важен."),
    "der Contrast": ("der", "контраст", "Der Contrast ist deutlich.", "Контраст очевиден."),
    "der Cursor": ("der", "курсор", "Der Cursor blinkt.", "Курсор мигает."),
    "der Cycle": ("der", "цикл", "Der Cycle dauert lange.", "Цикл длится долго."),
    "der Cylind": ("der", "цилиндр", "Der Cylind ist aus Metall.", "Цилиндр из металла."),
    "der Cynismus": ("der", "цинизм", "Der Cynismus stört.", "Цинизм раздражает."),
    
    # das-слова
    "das Colloquium": ("das", "коллоквиум", "Das Colloquium beginnt um 10 Uhr.", "Коллоквиум начинается в 10 часов."),
    "das Currículum": ("das", "учебный план", "Das Currículum ist neu.", "Учебный план новый."),
}

print("🔧 Исправление слов C1...\n")

updated_count = 0
not_found_count = 0

for word_full, (article, ru, example_de, example_ru) in C1_CORRECTIONS.items():
    try:
        # Обновляем слово (ищем по полному названию с артиклем)
        cur.execute("""
            UPDATE words SET
                article = %s,
                ru = %s,
                example_de = %s,
                example_ru = %s
            WHERE de = %s AND level = 'C1'
        """, (article, ru, example_de, example_ru, word_full))
        
        if cur.rowcount > 0:
            updated_count += 1
        else:
            not_found_count += 1
            print(f"⚠️  Не найдено: {word_full}")

    except Exception as e:
        print(f"❌ Ошибка с '{word_full}': {e}")
        if conn:
            conn.rollback()

    conn.commit()

    print(f"\n📊 Итоги:")
    print(f"   Исправлено: {updated_count}")
    print(f"   Не найдено: {not_found_count}")

except Exception as e:
    print(f"❌ Критическая ошибка: {e}")
    if conn:
        conn.rollback()
finally:
    if cur:
        cur.close()
    if conn:
        conn.close()
