import os
import psycopg2
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local')
load_dotenv(dotenv_path)
url = os.getenv("DATABASE_URL")

WORDS_B2 = [
            "die Verringerung", "verrückt", 
    "die Versammlung", "versammeln", "verschieben", "die Verschiebung", 
    "verschieden", "die Verschiedenheit", "verschwinden", "das Verschwinden", 
    "versehen", "das Versehen", "versichern", "die Versicherung", "die Version", 
    "verspäten", "die Verspätung", "versprechen", "das Versprechen", 
    "der Verstand", "das Verständnis", "verständlich", "verständnisvoll", 
    "verstecken", "verstehen", "der Versuch", "versuchen", "verteilen", 
    "die Verteilung", "der Vertrag", "vertrauen", "das Vertrauen", "vertraut", 
    "vertreten", "der Vertreter", "die Vertretung", "verursachen", "die Ursache", 
    "verurteilen", "das Urteil", "die Verwaltung", "verwandt", "der Verwandte", 
    "verwechseln", "die Verwechslung", "verweigern", "die Verweigerung", 
    "verwenden", "die Verwendung", "verzichten", "der Verzicht", "verzweifeln", 
    "die Verzweiflung", "viel", "vielleicht", "vielfach", "vielfältig", 
    "die Vielfalt", "völlig", "von", "vor", "vorab", "voran", "voraus", 
    "die Voraussetzung", "voraussetzen", "vorbei", "vorbereiten", "die Vorbereitung", 
    "vorbeugen", "die Vorbeugung", "vordere", "vorfallen", "der Vorfall", 
    "vorhaben", "das Vorhaben", "vorhanden", "vorher", "vorherig", "vorig", 
    "vorkommen", "das Vorkommen", "vorläufig", "vorlesen", "die Vorlesung", 
    "vorn", "vorne", "der Vorname", "der Vorort", "der Vorschlag", "vorschlagen", 
    "die Vorschrift", "Vorsicht", "vorsichtig", "der Vorsitzende", "der Vorstand", 
    "vorstellen", "die Vorstellung", "der Vorteil", "vorteilhaft", "der Vortrag", 
    "vorwärts", "der Vorwurf", "vorwerfen", "vorziehen", "der Vorzug", "wach", 
    "wachsen", "das Wachstum", "der Wagen", "wählen", "die Wahl", "wahr", 
    "die Wahrheit", "wahrscheinlich", "die Wahrscheinlichkeit", "der Wald", 
    "die Wand", "wandern", "die Wanderung", "wann", "die Ware", "warm", 
    "die Wärme", "warnen", "die Warnung", "warten", "die Wartung", "warum", 
    "was", "waschen", "das Wasser", "wechseln", "der Wechsel", "wecken", 
    "weder", "der Weg", "wegen", "wehren", "die Wehr", "das Weib", "weiblich", 
    "weich", "weigern", "die Weigerung", "weil", "der Wein", "weinen", 
    "die Weise", "weisen", "die Weisheit", "weiß", "weit", "die Weite", 
    "weiter", "weitere", "weiterhin", "welch", "die Welle", "die Welt", 
    "weltweit", "wenden", "die Wendung", "wenig", "wenige", "weniger", 
    "wenigstens", "wenn", "wer", "die Werbung", "werden", "werfen", "das Werk", 
    "die Werkstatt", "der Wert", "wert", "wertvoll", "das Wesen", "wesentlich", 
    "der Westen", "westlich", "die Wette", "das Wetter", "wichtig", "die Wichtigkeit", 
    "wider", "der Widerspruch", "widersprechen", "der Widerstand", "wie", 
    "wieder", "wiederholen", "die Wiederholung", "wiegen", "die Wiese", 
    "wieso", "wild", "der Wille", "willkommen", "der Wind", "der Winkel", 
    "der Winter", "wir", "wirken", "die Wirkung", "wirklich", "die Wirklichkeit", 
    "wirksam", "die Wirtschaft", "wirtschaftlich", "wissen", "das Wissen", 
    "die Wissenschaft", "wissenschaftlich", "der Wissenschaftler", "witze", 
    "der Witz", "wo", "die Woche", "das Wochenende", "wofür", "woher", 
    "wohin", "wohl", "wohlhabend", "der Wohnort", "der Wohnsitz", "wohnen", 
    "die Wohnung", "die Wolke", "wollen", "das Wort", "wörtlich", "worüber", 
    "worum", "die Wunde", "das Wunder", "wunderbar", "wundern", "der Wunsch", 
    "wünschen", "die Würde", "würdig", "der Wurf", "die Wurst", "die Wurzel", 
    "wütend", "die Wut", "die Zahl", "zählen", "zahlreich", "zahlen", 
    "die Zahlung", "der Zahn", "die Zange", "zart", "der Zauber", "der Zaun", 
    "das Zehn", "das Zeichen", "zeichnen", "die Zeichnung", "zeigen", "die Zeile", 
    "die Zeit", "der Zeitpunkt", "die Zeitschrift", "die Zeitung", "das Zelt", 
    "das Zentrum", "zentral", "zerstören", "die Zerstörung", "das Zertifikat", 
    "der Zettel", "das Zeug", "der Zeuge", "die Zeugin", "das Zeugnis", "ziehen", 
    "das Ziel", "zielen", "die Zigarre", "die Zigarette", "das Zimmer", 
    "der Zins", "der Zirkus", "die Zitrone", "zögern", "der Zoll", "die Zone", 
    "der Zoo", "zu", "der Zucker", "zuerst", "der Zufall", "zufällig", 
    "die Zuflucht", "zufrieden", "die Zufriedenheit", "der Zugang", "zugänglich", 
    "zugeben", "zugehören", "die Zugehörigkeit", "zugleich", "zugrunde", 
    "zuhören", "der Zuhörer", "die Zukunft", "zukünftig", "zulassen", "die Zulassung", 
    "zuletzt", "zumachen", "zumeist", "zumindest", "zumuten", "die Zumutung", 
    "zunächst", "zunehmen", "die Zunahme", "zuordnen", "die Zuordnung", 
    "zurecht", "zurück", "zurückgehen", "zurückhalten", "die Zurückhaltung", 
    "zurückkehren", "zurücktreten", "der Rücktritt", "zurückziehen", "die Zurückziehung", 
    "zusagen", "die Zusage", "zusammen", "die Zusammenarbeit", "zusammenfassen", 
    "die Zusammenfassung", "der Zusammenhang", "zusätzlich", "zuschauen", 
    "der Zuschauer", "zuschlagen", "der Zuschlag", "zuständig", "die Zuständigkeit", 
    "der Zustand", "zustimmen", "die Zustimmung", "zuverlässig", "die Zuverlässigkeit", 
    "die Zuversicht", "zuversichtlich", "zuvor", "der Zwang", "zwingen", 
    "zwar", "der Zweck", "zweckmäßig", "zweifeln", "der Zweifel", "der Zweig", 
    "zweit-", "zwingend", "zwischen", "zwischendurch", "der Zwischenfall"


]

def import_b2_words():
    added_count = 0
    skipped_count = 0
    conn = None
    cur = None
    try:
        print("Подключаюсь к базе...")
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        print(f"Найдено {len(WORDS_B2)} слов B2. Начинаю импорт...\n")

        for word in WORDS_B2:
            word = word.strip()
            if not word:
                continue
            cur.execute("SELECT id FROM words WHERE de = %s;", (word,))
            if cur.fetchone():
                skipped_count += 1
                continue
            cur.execute(
                "INSERT INTO words (de, ru, level, topic, examples) VALUES (%s, %s, %s, %s, NULL);",
                (word, "перевод в процессе", "B2", "Goethe B2")
            )
            added_count += 1

        conn.commit()
        print(f"✅ Успешно добавлено новых слов B2: {added_count}")
        print(f"⏩ Пропущено (уже были в базе): {skipped_count}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    import_b2_words()
