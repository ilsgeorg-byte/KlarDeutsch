#!/usr/bin/env python3
"""
Исправить ВСЕ слова C1 - добавить артикли и примеры ко всем 199 словам
"""

import os, sys, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

import psycopg2

conn = psycopg2.connect(os.environ.get("POSTGRES_URL"))
cur = conn.cursor()

# Все слова C1 с артиклями и примерами (полный список 199 слов)
C1_COMPLETE = {
    # A
    "die Abstraktion": ("die", "абстракция", "Die Abstraktion ist ein wichtiger Denkprozess.", "Абстракция — важный мыслительный процесс."),
    "die Ambition": ("die", "амбиция", "Seine Ambition kennt keine Grenzen.", "Его амбиция не знает границ."),
    "die Ambivalenz": ("die", "амбивалентность", "Die Ambivalenz der Gefühle verwirrt ihn.", "Амбивалентность чувств сбивает его с толку."),
    "die Analogie": ("die", "аналогия", "Die Analogie zwischen den Fällen ist striking.", "Аналогия между случаями поразительна."),
    "die Anomalie": ("die", "аномалия", "Diese Anomalie muss erklärt werden.", "Эта аномалия должна быть объяснена."),
    "die Antithese": ("die", "антитезис", "Die Antithese steht im Widerspruch zur These.", "Антитезис противоречит тезису."),
    "die Apologie": ("die", "апология", "Das Buch ist eine Apologie der Moderne.", "Книга — апология модерна."),
    "die Apotheose": ("die", "апофеоз", "Die Apotheose des Festes war das Feuerwerk.", "Апофеозом праздника был фейерверк."),
    "die Appellation": ("die", "апелляция", "Die Appellation hatte keinen Erfolg.", "Апелляция не имела успеха."),
    "die Applikation": ("die", "аппликация", "Die Applikation der Theorie ist komplex.", "Аппликация теории сложна."),
    "die Approximation": ("die", "аппроксимация", "Die Approximation ist hinreichend genau.", "Аппроксимация достаточно точна."),
    "die Äquivalenz": ("die", "эквивалентность", "Die Äquivalenz der beiden Aussagen ist bewiesen.", "Эквивалентность обоих утверждений доказана."),
    "die Argumentation": ("die", "аргументация", "Seine Argumentation war schlüssig.", "Его аргументация была убедительной."),
    "die Artikulation": ("die", "артикуляция", "Die Artikulation des Sprechers war klar.", "Артикуляция оратора была ясной."),
    "die Assoziation": ("die", "ассоциация", "Diese Assoziation ist sehr stark.", "Эта ассоциация очень сильная."),
    "die Assimilation": ("die", "ассимиляция", "Die Assimilation dauert mehrere Generationen.", "Ассимиляция длится несколько поколений."),
    "die Asymmetrie": ("die", "асимметрия", "Die Asymmetrie des Gesichts ist auffällig.", "Асимметрия лица бросается в глаза."),
    "die Atmosphäre": ("die", "атмосфера", "Die Atmosphäre im Raum war gespannt.", "Атмосфера в комнате была напряженной."),
    "die Attribution": ("die", "атрибуция", "Die Attribution der Verantwortung ist schwierig.", "Атрибуция ответственности сложна."),
    "die Authentizität": ("die", "аутентичность", "Die Authentizität des Gemäldes wurde bestätigt.", "Аутентичность картины была подтверждена."),
    "die Autonomie": ("die", "автономия", "Die Autonomie der Universität ist geschützt.", "Автономия университета защищена."),
    "die Avantgarde": ("die", "авангард", "Die Avantgarde der Kunst war revolutionär.", "Авангард искусства был революционным."),
    "die Aversion": ("die", "отвращение", "Er hat eine Aversion gegen laute Geräusche.", "У него отвращение к громким звукам."),
    
    # B
    "die Balance": ("die", "баланс", "Die Balance zwischen Arbeit und Freizeit ist wichtig.", "Баланс между работой и отдыхом важен."),
    "die Barriere": ("die", "барьер", "Die Barriere wurde erfolgreich überwunden.", "Барьер был успешно преодолен."),
    "die Blamage": ("die", "позор", "Die Pleite war eine echte Blamage.", "Банкротство было настоящим позором."),
    "die Bosheit": ("die", "злоба", "Die Bosheit in seinen Worten war unüberhörbar.", "Злоба в его словах была неоспорима."),
    "die Brisanz": ("die", "острота", "Die Brisanz des Themas ist unbestritten.", "Острота темы неоспорима."),
    "die Bürokratie": ("die", "бюрократия", "Die Bürokratie behindert den Fortschritt.", "Бюрократия препятствует прогрессу."),
    
    # C
    "die Chance": ("die", "шанс", "Das ist deine letzte Chance!", "Это твой последний шанс!"),
    "die Charakteristik": ("die", "характеристика", "Die Charakteristik des Produkts ist positiv.", "Характеристика продукта положительная."),
    "die Charisma": ("die", "харизма", "Seine Charisma zieht alle an.", "Его харизма привлекает всех."),
    "die Chronik": ("die", "хроника", "Die Chronik dokumentiert die Geschichte der Stadt.", "Хроника документирует историю города."),
    "die Chiffre": ("die", "шифр", "Die Chiffre wurde erfolgreich entschlüsselt.", "Шифр был успешно расшифрован."),
    "die Zivilisation": ("die", "цивилизация", "Die Zivilisation hat sich über Jahrtausende entwickelt.", "Цивилизация развивалась тысячелетиями."),
    "die Coalition": ("die", "коалиция", "Die Coalition der Parteien war erfolgreich.", "Коалиция партий была успешной."),
    "die Codierung": ("die", "кодирование", "Die Codierung der Daten ist sicher.", "Кодирование данных безопасно."),
    "die Cohärenz": ("die", "когерентность", "Die Cohärenz der Argumentation ist stark.", "Когерентность аргументации сильна."),
    "die Collage": ("die", "коллаж", "Die Collage aus Bildern ist kreativ.", "Коллаж из изображений креативен."),
    "die Combination": ("die", "комбинация", "Die Combination der Farben ist harmonisch.", "Комбинация цветов гармонична."),
    "die Comedy": ("die", "комедия", "Die Comedy im Fernsehen ist lustig.", "Комедия по телевизору смешная."),
    "die Community": ("die", "сообщество", "Die Community ist sehr aktiv.", "Сообщество очень активное."),
    "die Compilation": ("die", "компиляция", "Die Compilation des Codes war erfolgreich.", "Компиляция кода была успешной."),
    "die Compliance": ("die", "соответствие", "Die Compliance mit den Regeln ist wichtig.", "Соответствие правилам важно."),
    "die Complication": ("die", "осложнение", "Die Complication der Situation ist offensichtlich.", "Осложнение ситуации очевидно."),
    "die Composition": ("die", "композиция", "Die Composition des Musikstücks ist meisterhaft.", "Композиция музыкального произведения мастерская."),
    "die Conception": ("die", "концепция", "Die Conception des Projekts ist innovativ.", "Концепция проекта инновационна."),
    "die Conclusion": ("die", "заключение", "Die Conclusion der Studie ist eindeutig.", "Заключение исследования однозначно."),
    "die Concretion": ("die", "конкретизация", "Die Concretion der Pläne fehlt noch.", "Конкретизация планов еще отсутствует."),
    "die Condition": ("die", "условие", "Die Condition für die Teilnahme ist erfüllt.", "Условие для участия выполнено."),
    "die Conferenz": ("die", "конференция", "Die Conferenz war sehr informativ.", "Конференция была очень информативной."),
    "die Configuration": ("die", "конфигурация", "Die Configuration des Systems ist optimal.", "Конфигурация системы оптимальна."),
    "die Confrontation": ("die", "конфронтация", "Die Confrontation war unvermeidlich.", "Конфронтация была неизбежна."),
    "die Confusion": ("die", "путаница", "Die Confusion war groß nach der Ankündigung.", "Путаница была большой после объявления."),
    "die Congruenz": ("die", "конгруэнтность", "Die Congruenz der Dreiecke ist bewiesen.", "Конгруэнтность треугольников доказана."),
    "die Conjugation": ("die", "спряжение", "Die Conjugation dieses Verbs ist unregelmäßig.", "Спряжение этого глагола неправильное."),
    "die Conjunction": ("die", "конъюнкция", "Die Conjunction der Aussagen ist wahr.", "Конъюнкция утверждений истинна."),
    "die Connexion": ("die", "связь", "Die Connexion zwischen den Ereignissen ist klar.", "Связь между событиями ясна."),
    "die Connotation": ("die", "коннотация", "Die Connotation des Wortes ist positiv.", "Коннотация слова позитивная."),
    "die Consequenz": ("die", "последствие", "Die Consequenz der Handlung war vorhersehbar.", "Последствие действия было предсказуемо."),
    "die Conservation": ("die", "сохранение", "Die Conservation der Natur ist wichtig.", "Сохранение природы важно."),
    "die Consideration": ("die", "рассмотрение", "Die Consideration des Falls dauert an.", "Рассмотрение дела продолжается."),
    "die Consistenz": ("die", "консистентность", "Die Consistenz der Masse ist perfekt.", "Консистентность массы идеальна."),
    "die Consonanz": ("die", "консонанс", "Die Consonanz der Klänge ist harmonisch.", "Консонанс звуков гармоничен."),
    "die Constanz": ("die", "константность", "Die Constanz der Temperatur ist wichtig.", "Константность температуры важна."),
    "die Constitution": ("die", "конституция", "Die Constitution wurde 1949 verabschiedet.", "Конституция была принята в 1949 году."),
    "die Construction": ("die", "конструкция", "Die Construction des Gebäudes ist stabil.", "Конструкция здания стабильна."),
    "die Consultation": ("die", "консультация", "Die Consultation beim Arzt war hilfreich.", "Консультация у врача была полезной."),
    "die Consumption": ("die", "потребление", "Die Consumption von Energie steigt.", "Потребление энергии растет."),
    "die Contamination": ("die", "загрязнение", "Die Contamination des Wassers ist gefährlich.", "Загрязнение воды опасно."),
    "die Contemplation": ("die", "созерцание", "Die Contemplation bringt Ruhe.", "Созерцание приносит спокойствие."),
    "die Contestation": ("die", "оспаривание", "Die Contestation des Urteils ist berechtigt.", "Оспаривание приговора обосновано."),
    "der Context": ("der", "контекст", "Der Context ist für das Verständnis wichtig.", "Контекст важен для понимания."),
    "die Continuität": ("die", "непрерывность", "Die Continuität der Entwicklung ist gewährleistet.", "Непрерывность развития обеспечена."),
    "die Contraction": ("die", "сокращение", "Die Contraction des Muskels ist messbar.", "Сокращение мышцы измеримо."),
    "die Contradiction": ("die", "противоречие", "Die Contradiction ist offensichtlich.", "Противоречие очевидно."),
    "der Contrast": ("der", "контраст", "Der Contrast zwischen Hell und Dunkel ist stark.", "Контраст между светом и тьмой силен."),
    "die Contribution": ("die", "вклад", "Sein Contribution zum Projekt war wertvoll.", "Его вклад в проект был ценным."),
    "die Contrition": ("die", "раскаяние", "Die Contrition des Sünders war aufrichtig.", "Раскаяние грешника было искренним."),
    "die Controverse": ("die", "спор", "Die Controverse dauert seit Jahren an.", "Спор продолжается годами."),
    "die Convention": ("die", "конвенция", "Die Convention wurde von allen unterzeichnet.", "Конвенция была подписана всеми."),
    "die Conversation": ("die", "разговор", "Die Conversation war angenehm und lebhaft.", "Разговор был приятным и оживленным."),
    "die Conversion": ("die", "преобразование", "Die Conversion der Währung ist abgeschlossen.", "Преобразование валюты завершено."),
    "die Conviction": ("die", "убеждение", "Seine Conviction ist unerschütterlich.", "Его убеждение непоколебимо."),
    "die Cooperation": ("die", "кооперация", "Die Cooperation zwischen den Ländern ist erfolgreich.", "Кооперация между странами успешна."),
    "die Coordination": ("die", "координация", "Die Coordination der Aufgaben ist wichtig.", "Координация задач важна."),
    "die Correction": ("die", "коррекция", "Die Correction des Fehlers war notwendig.", "Коррекция ошибки была необходима."),
    "die Correlation": ("die", "корреляция", "Die Correlation zwischen den Variablen ist signifikant.", "Корреляция между переменными значима."),
    "die Correspondenz": ("die", "корреспонденция", "Die Correspondenz ist heute angekommen.", "Корреспонденция прибыла сегодня."),
    "die Corruption": ("die", "коррупция", "Die Corruption muss bekämpft werden.", "Коррупция должна быть искоренена."),
    "die Cosmologie": ("die", "космология", "Die Cosmologie erforscht das Universum.", "Космология исследует вселенную."),
    "die Courtoisie": ("die", "учтивость", "Die Courtoisie des Personals war bemerkenswert.", "Учтивость персонала была примечательной."),
    "die Creation": ("die", "создание", "Die Creation des Kunstwerks dauerte Jahre.", "Создание произведения искусства заняло годы."),
    "die Credibilität": ("die", "достоверность", "Die Credibilität der Quelle ist angezweifelt.", "Достоверность источника поставлена под сомнение."),
    "die Crew": ("die", "команда", "Die Crew des Schiffes ist erfahren.", "Команда корабля опытная."),
    "die Crise": ("die", "кризис", "Die Crise wurde erfolgreich überwunden.", "Кризис был успешно преодолен."),
    "die Critik": ("die", "критика", "Die Critik war konstruktiv und hilfreich.", "Критика была конструктивной и полезной."),
    "die Culmination": ("die", "кульминация", "Die Culmination des Festes war das Konzert.", "Кульминацией праздника был концерт."),
    "die Cumulation": ("die", "кумуляция", "Die Cumulation der Effekte ist stark.", "Кумуляция эффектов сильна."),
    "die Curiosity": ("die", "любопытство", "Die Curiosity des Kindes ist natürlich.", "Любопытство ребенка естественно."),
    "die Currency": ("die", "валюта", "Die Currency ist stabil.", "Валюта стабильна."),
    "das Colloquium": ("das", "коллоквиум", "Das Colloquium findet morgen statt.", "Коллоквиум состоится завтра."),
    "das Currículum": ("das", "учебный план", "Das Currículum ist umfassend und aktuell.", "Учебный план обширный и актуальный."),
    "der Cursor": ("der", "курсор", "Der Cursor bewegt sich über den Bildschirm.", "Курсор движется по экрану."),
    "die Curve": ("die", "кривая", "Die Curve der Funktion ist steil.", "Кривая функции крутая."),
    "die Custodie": ("die", "опека", "Die Custodie für das Kind wurde übertragen.", "Опека над ребенком была передана."),
    "die Customisierung": ("die", "кастомизация", "Die Customisierung des Produkts ist möglich.", "Кастомизация продукта возможна."),
    "die Cybernetik": ("die", "кибернетика", "Die Cybernetik ist eine interdisziplinäre Wissenschaft.", "Кибернетика — междисциплинарная наука."),
    "der Cycle": ("der", "цикл", "Der Cycle wiederholt sich jährlich.", "Цикл повторяется ежегодно."),
    "der Cylind": ("der", "цилиндр", "Der Cylind ist aus Stahl.", "Цилиндр из стали."),
    "der Cynismus": ("der", "цинизм", "Der Cynismus in seinen Worten ist auffällig.", "Цинизм в его словах бросается в глаза."),
    
    # D
    "die Dasein": ("die", "существование", "Das Dasein ist ein philosophischer Begriff.", "Существование — философский термин."),
    "die Datenbank": ("die", "база данных", "Die Datenbank ist sicher.", "База данных безопасна."),
    "die Dauer": ("die", "продолжительность", "Die Dauer des Projekts ist unklar.", "Продолжительность проекта неясна."),
    "das Debüt": ("das", "дебют", "Das Debüt der Schauspielerin war erfolgreich.", "Дебют актрисы был успешным."),
    "die Deduktion": ("die", "дедукция", "Die Deduktion ist eine logische Methode.", "Дедукция — логический метод."),
    "die Definition": ("die", "определение", "Die Definition des Begriffs ist klar.", "Определение термина ясно."),
    "die Deformation": ("die", "деформация", "Die Deformation des Materials ist messbar.", "Деформация материала измерима."),
    "die Degeneration": ("die", "дегенерация", "Die Degeneration der Zellen ist fortschreitend.", "Дегенерация клеток прогрессирует."),
    "die Degradierung": ("die", "деградация", "Die Degradierung der Umwelt ist besorgniserregend.", "Деградация окружающей среды вызывает беспокойство."),
    "die Dehnung": ("die", "растяжение", "Die Dehnung des Materials ist begrenzt.", "Растяжение материала ограничено."),
    "die Dekadenz": ("die", "декадентство", "Die Dekadenz der Gesellschaft ist offensichtlich.", "Декадентство общества очевидно."),
    "die Deklamation": ("die", "декламация", "Die Deklamation des Gedichts war beeindruckend.", "Декламация стихотворения была впечатляющей."),
    "die Deklination": ("die", "склонение", "Die Deklination dieses Substantivs ist unregelmäßig.", "Склонение этого существительного неправильное."),
    "die Dekoration": ("die", "декорация", "Die Dekoration des Saales war prachtvoll.", "Декорация зала была великолепной."),
    "die Delegation": ("die", "делегация", "Die Delegation aus Frankreich ist angekommen.", "Делегация из Франции прибыла."),
    "die Delikatesse": ("die", "деликатес", "Die Delikatesse war sehr teuer.", "Деликатес был очень дорогим."),
    "das Delikt": ("das", "деликт", "Das Delikt wurde aufgeklärt.", "Деликт был раскрыт."),
    "die Demagogie": ("die", "демагогия", "Die Demagogie des Politikers ist durchschaubar.", "Демагогия политика разоблачаема."),
    "die Demenz": ("die", "деменция", "Die Demenz ist eine ernste Krankheit.", "Деменция — серьезная болезнь."),
    "die Demission": ("die", "отставка", "Die Demission des Ministers wurde erwartet.", "Отставка министра ожидалась."),
    "die Demographie": ("die", "демография", "Die Demographie des Landes verändert sich.", "Демография страны меняется."),
    "die Demonstration": ("die", "демонстрация", "Die Demonstration war friedlich.", "Демонстрация была мирной."),
    "die Demut": ("die", "смирение", "Die Demut ist eine Tugend.", "Смирение — добродетель."),
    "die Denunziation": ("die", "донос", "Die Denunziation war falsch.", "Донос был ложным."),
    "die Dependance": ("die", "филиал", "Die Dependance der Bank ist neu.", "Филиал банка новый."),
    "die Depression": ("die", "депрессия", "Die Depression ist eine ernste Krankheit.", "Депрессия — серьезная болезнь."),
    "die Deputation": ("die", "депутация", "Die Deputation wurde empfangen.", "Депутация была принята."),
    "die Derivation": ("die", "деривация", "Die Derivation des Wortes ist klar.", "Деривация слова ясна."),
    "die Derogation": ("die", "дерогация", "Die Derogation des Gesetzes ist beschlossen.", "Дерогация закона решена."),
    "die Desillusion": ("die", "разочарование", "Die Desillusion war groß.", "Разочарование было большим."),
    "die Desinfektion": ("die", "дезинфекция", "Die Desinfektion der Hände ist wichtig.", "Дезинфекция рук важна."),
    "die Desintegration": ("die", "дезинтеграция", "Die Desintegration der Gesellschaft ist besorgniserregend.", "Дезинтеграция общества вызывает беспокойство."),
    "die Deskription": ("die", "описание", "Die Deskription des Phänomens ist detailliert.", "Описание феномена детально."),
    "die Desolation": ("die", "запустение", "Die Desolation der Landschaft ist traurig.", "Запустение пейзажа печально."),
    "die Despotie": ("die", "деспотия", "Die Despotie des Herrschers war berüchtigt.", "Деспотия правителя была печально известна."),
    "die Destination": ("die", "назначение", "Die Destination der Reise ist Paris.", "Назначение путешествия — Париж."),
    "die Destillation": ("die", "дистилляция", "Die Destillation des Wassers ist abgeschlossen.", "Дистилляция воды завершена."),
    "die Destruktion": ("die", "деструкция", "Die Destruktion des Gebäudes war geplant.", "Деструкция здания была запланирована."),
    "die Detektion": ("die", "детекция", "Die Detektion des Signals war erfolgreich.", "Детекция сигнала была успешной."),
    "die Determination": ("die", "детерминация", "Die Determination der Ursache ist wichtig.", "Детерминация причины важна."),
    "die Detonation": ("die", "детонация", "Die Detonation war laut.", "Детонация была громкой."),
    "die Devianz": ("die", "девиантность", "Die Devianz vom Normalverhalten ist auffällig.", "Девиантность от нормального поведения бросается в глаза."),
    "die Devise": ("die", "девиз", "Die Devise der Firma ist 'Qualität vor Quantität'.", "Девиз компании — 'Качество прежде количества'."),
    "die Devotion": ("die", "преданность", "Die Devotion des Dieners war bemerkenswert.", "Преданность слуги была примечательной."),
    "die Diät": ("die", "диета", "Die Diät ist gesund.", "Диета здорова."),
    "die Dichotomie": ("die", "дихотомия", "Die Dichotomie zwischen Gut und Böse ist klassisch.", "Дихотомия между добром и злом классическая."),
    "die Dichtung": ("die", "поэзия", "Die Dichtung des Autors ist berühmt.", "Поэзия автора знаменита."),
    "die Didaktik": ("die", "дидактика", "Die Didaktik des Unterrichts ist durchdacht.", "Дидактика урока продумана."),
    "die Differenz": ("die", "разница", "Die Differenz zwischen den Zahlen ist groß.", "Разница между числами велика."),
    "die Diffusion": ("die", "диффузия", "Die Diffusion der Gase ist messbar.", "Диффузия газов измерима."),
    "die Digitalisierung": ("die", "цифровизация", "Die Digitalisierung schreitet voran.", "Цифровизация продвигается."),
    "die Dignität": ("die", "достоинство", "Die Dignität des Menschen ist unantastbar.", "Достоинство человека неприкосновенно."),
    "die Dimension": ("die", "размер", "Die Dimension des Raums ist groß.", "Размер комнаты велик."),
    "die Diminution": ("die", "уменьшение", "Die Diminution der Ressourcen ist besorgniserregend.", "Уменьшение ресурсов вызывает беспокойство."),
    "die Diplomatie": ("die", "дипломатия", "Die Diplomatie hat den Krieg verhindert.", "Дипломатия предотвратила войну."),
    "die Direktion": ("die", "дирекция", "Die Direktion des Unternehmens ist erfahren.", "Дирекция компании опытная."),
    "die Disziplin": ("die", "дисциплина", "Die Disziplin ist wichtig für den Erfolg.", "Дисциплина важна для успеха."),
    "die Diskrepanz": ("die", "расхождение", "Die Diskrepanz zwischen Theorie und Praxis ist groß.", "Расхождение между теорией и практикой велико."),
    "die Diskriminierung": ("die", "дискриминация", "Die Diskriminierung ist verboten.", "Дискриминация запрещена."),
    "die Diskussion": ("die", "дискуссия", "Die Diskussion war lebhaft.", "Дискуссия была оживленной."),
    "die Disparität": ("die", "неравенство", "Die Disparität zwischen den Regionen ist groß.", "Неравенство между регионами велико."),
    "die Dispensation": ("die", "диспенсация", "Die Dispensation wurde gewährt.", "Диспенсация была предоставлена."),
    "die Disposition": ("die", "диспозиция", "Die Disposition der Truppen ist strategisch.", "Диспозиция войск стратегическая."),
    "die Disputation": ("die", "диспут", "Die Disputation war akademisch.", "Диспут был академическим."),
    "die Dissertation": ("die", "диссертация", "Die Dissertation ist abgeschlossen.", "Диссертация завершена."),
    "die Dissidenz": ("die", "диссидентство", "Die Dissidenz gegen das Regime war stark.", "Диссидентство против режима было сильным."),
    "die Distanz": ("die", "дистанция", "Die Distanz zwischen den Städten ist groß.", "Дистанция между городами велика."),
    "die Distinktion": ("die", "различие", "Die Distinktion ist wichtig.", "Различие важно."),
    "die Distortion": ("die", "искажение", "Die Distortion des Signals ist messbar.", "Искажение сигнала измеримо."),
    "die Distribution": ("die", "распределение", "Die Distribution der Güter ist fair.", "Распределение товаров справедливо."),
    "die Diversifikation": ("die", "диверсификация", "Die Diversifikation des Portfolios ist wichtig.", "Диверсификация портфеля важна."),
    "die Diversität": ("die", "разнообразие", "Die Diversität der Kulturen ist bereichernd.", "Разнообразие культур обогащает."),
    "die Diversion": ("die", "диверсия", "Die Diversion wurde verhindert.", "Диверсия была предотвращена."),
    "die Division": ("die", "деление", "Die Division der Zahlen ist einfach.", "Деление чисел простое."),
    "die Doktrin": ("die", "доктрина", "Die Doktrin der Partei ist klar.", "Доктрина партии ясна."),
    "die Dokumentation": ("die", "документация", "Die Dokumentation ist vollständig.", "Документация полная."),
    "die Domäne": ("die", "домен", "Die Domäne der Website ist neu.", "Домен веб-сайта новый."),
    "die Dominanz": ("die", "доминирование", "Die Dominanz der Mannschaft ist unbestritten.", "Доминирование команды неоспоримо."),
    "die Donation": ("die", "пожертвование", "Die Donation war großzügig.", "Пожертвование было щедрым."),
    "die Dosis": ("die", "доза", "Die Dosis des Medikaments ist wichtig.", "Доза лекарства важна."),
    "die Dramatik": ("die", "драматизм", "Die Dramatik der Situation ist offensichtlich.", "Драматизм ситуации очевиден."),
    "die Dramaturgie": ("die", "драматургия", "Die Dramaturgie des Stücks ist komplex.", "Драматургия пьесы сложна."),
    "die Drastik": ("die", "драстичность", "Die Drastik der Maßnahme ist notwendig.", "Драстичность меры необходима."),
    "die Dreistigkeit": ("die", "наглость", "Die Dreistigkeit der Aussage ist erstaunlich.", "Наглость заявления поразительна."),
    "die Drohung": ("die", "угроза", "Die Drohung war ernst gemeint.", "Угроза была серьезной."),
    "die Dualität": ("die", "дуальность", "Die Dualität von Körper und Geist ist philosophisch.", "Дуальность тела и духа философская."),
    "die Dublette": ("die", "дубликат", "Die Dublette des Dokuments ist verfügbar.", "Дубликат документа доступен."),
    "die Dummheit": ("die", "глупость", "Die Dummheit des Handelns ist offensichtlich.", "Глупость действия очевидна."),
    "die Duplizität": ("die", "двуличность", "Die Duplizität des Politikers ist bekannt.", "Двуличность политика известна."),
    "die Dynamik": ("die", "динамика", "Die Dynamik des Marktes ist hoch.", "Динамика рынка высока."),
    "die Dysfunktion": ("die", "дисфункция", "Die Dysfunktion des Organs ist ernst.", "Дисфункция органа серьезна."),
}

print("🔧 Исправление ВСЕХ слов C1...\n")

updated_count = 0
not_found_count = 0
error_count = 0

for word_full, (article, ru, example_de, example_ru) in C1_COMPLETE.items():
    try:
        # Обновляем слово
        cur.execute("""
            UPDATE words SET
                article = %s,
                ru = COALESCE(%s, ru),
                example_de = %s,
                example_ru = %s
            WHERE de = %s AND level = 'C1'
        """, (article, ru, example_de, example_ru, word_full))
        
        if cur.rowcount > 0:
            updated_count += 1
            print(f"✅ Исправлено: {word_full}")
        else:
            not_found_count += 1
            print(f"⚠️  Не найдено: {word_full}")
            
    except Exception as e:
        error_count += 1
        print(f"❌ Ошибка с '{word_full}': {e}")
        conn.rollback()

conn.commit()

print(f"\n📊 Итоги:")
print(f"   Исправлено: {updated_count}")
print(f"   Не найдено: {not_found_count}")
print(f"   Ошибок: {error_count}")

cur.close()
conn.close()
