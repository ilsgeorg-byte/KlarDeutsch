import os
import psycopg2
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local')
load_dotenv(dotenv_path)
url = os.getenv("DATABASE_URL")

WORDS_B1 = [
    # A
    "die Abbildung", "abbrechen", "der Abbruch", "abhalten", "abhängen von",
    "abkürzen", "die Abkürzung", "ablaufen", "ableiten", "abmachen",
    "abschaffen", "abschätzen", "absichtlich", "abstrakt", "abwägen",
    "abweichen", "die Abweichung", "abwesend", "die Abwesenheit",
    "achten auf", "die Achtung", "ähneln", "akzeptieren", "die Akzeptanz",
    "allgemein", "die Allgemeinheit", "analysieren", "die Analyse",
    "die Anforderung", "angemessen", "angesichts", "anklagen", "anknüpfen",
    "anlegen", "anpassen", "die Anpassung", "anregen", "die Anregung",
    "anschließend", "ansprechen", "anstreben", "der Anteil", "anwenden",
    "die Anwendung", "der Appell", "die Arbeitslosigkeit", "das Argument",
    "argumentieren", "die Armut", "aufbauen", "auffordern", "die Aufforderung",
    "aufgrund", "aufhalten", "aufmerksam machen", "aufnehmen", "sich aufregen",
    "aufteilen", "aufzeigen", "ausbilden", "die Auseinandersetzung",
    "ausgehen von", "ausgleichen", "der Ausgleich", "auslösen", "ausreichend",
    "außerdem", "äußern", "die Äußerung", "auswirken", "die Auswirkung",

    # B
    "der Bedarf", "bedingen", "bedrohen", "die Bedrohung", "beeinflussen",
    "der Einfluss", "sich befassen mit", "befördern", "die Beförderung",
    "begründen", "die Begründung", "behaupten", "die Behauptung",
    "bei weitem", "beitragen zu", "belasten", "die Belastung", "belegen",
    "der Beleg", "bemerkenswert", "sich bemühen", "die Bemühung",
    "berichten", "der Bericht", "berücksichtigen", "die Berücksichtigung",
    "sich beschäftigen mit", "die Beschäftigung", "beseitigen",
    "die Beseitigung", "bestätigen", "die Bestätigung", "betonen",
    "die Betonung", "betragen", "beurteilen", "die Beurteilung",
    "bewältigen", "die Bewältigung", "beweisen", "der Beweis",
    "bewusst", "das Bewusstsein", "sich beziehen auf", "die Beziehung",
    "bezüglich", "bilden", "die Bildung", "der Bürger", "die Bürgerin",
    "die Bürgerschaft",

    # C
    "charakterisieren", "der Charakter", "die Chancengleichheit",

    # D
    "darstellen", "die Darstellung", "dauerhaft", "definieren",
    "die Definition", "demokratisch", "die Demokratie", "denkbar",
    "der Druck", "durchsetzen", "die Durchsetzung", "durchführen",

    # E
    "ebenfalls", "effektiv", "die Effektivität", "ehrenamtlich",
    "das Ehrenamt", "einbeziehen", "eindeutig", "einerseits",
    "einschränken", "die Einschränkung", "einstellen", "die Einstellung",
    "entwickeln", "die Entwicklung", "das Ereignis", "erfassen",
    "erfolgen", "die Erkenntnis", "erkennen", "ermöglichen",
    "sich erweisen als", "erwerben", "der Erwerb", "erzeugen",
    "die Erzeugung",

    # F
    "fähig", "die Fähigkeit", "fair", "die Fairness", "feststellen",
    "die Feststellung", "fördern", "die Förderung", "die Forschung",
    "forschen", "der Forscher", "fordern", "die Forderung",
    "die Freiheit", "der Frieden", "führen zu", "die Funktion",
    "funktionieren",

    # G
    "geeignet", "gefährden", "gegenüber", "gelten als", "genehmigen",
    "die Genehmigung", "gesellschaftlich", "die Gesellschaft",
    "gesetzlich", "das Gesetz", "der Gewinn", "das Gleichgewicht",
    "die Gleichstellung", "gliedern", "die Gliederung", "global",
    "die Globalisierung", "grundlegend", "die Grundlage",

    # H
    "handeln", "das Handeln", "herausfordern", "die Herausforderung",
    "herstellen", "die Herstellung", "hervorheben", "hinweisen auf",
    "hinsichtlich",

    # I
    "im Gegensatz zu", "im Hinblick auf", "immerhin", "individuell",
    "das Individuum", "informieren", "der Inhalt", "integrieren",
    "die Integration", "interagieren", "die Interaktion", "investieren",
    "die Investition",

    # J
    "je nach", "jedoch",

    # K
    "die Kommunikation", "kommunizieren", "die Kompetenz", "komplex",
    "die Komplexität", "der Konflikt", "konsequent", "die Konsequenz",
    "konstruktiv", "kontrollieren", "die Kontrolle", "sich konzentrieren auf",
    "kooperieren", "die Kooperation", "kritisch", "die Kritik", "kritisieren",

    # L
    "die Lage", "langfristig", "die Leistung", "leisten", "lösen",

    # M
    "maßgeblich", "die Maßnahme", "die Mehrheit", "meistern",
    "der Mindestlohn", "die Minderheit", "das Mittel", "möglicherweise",
    "motivieren", "die Motivation",

    # N
    "nachhaltig", "die Nachhaltigkeit", "nachweisen", "der Nachweis",
    "notwendig", "die Notwendigkeit",

    # O
    "objektiv", "die Objektivität", "öffentlich", "die Öffentlichkeit",
    "ökologisch", "die Ökologie", "optimieren", "die Optimierung",

    # P
    "die Perspektive", "politisch", "die Politik", "der Politiker",
    "die Politikerin", "positiv", "die Priorität", "problematisch",
    "profitieren", "das Profil",

    # R
    "reagieren auf", "die Reaktion", "realisieren", "die Realisierung",
    "rechtlich", "das Recht", "reflektieren", "die Reflexion",
    "regeln", "die Regelung", "repräsentieren", "die Repräsentation",
    "das Resultat", "die Rolle",

    # S
    "schaffen", "sichern", "die Sicherung", "die Sichtweise", "sinnvoll",
    "die Solidarität", "sozial", "die Sozialpolitik", "der Standard",
    "die Strategie", "streben nach", "die Struktur", "strukturieren",

    # T
    "die Teilhabe", "teilhaben", "tendenziell", "die Tendenz",
    "die Transparenz", "transparent",

    # U
    "überzeugen", "die Überzeugung", "umgehen mit", "der Umgang",
    "umsetzen", "die Umsetzung", "unabhängig", "die Unabhängigkeit",
    "unterscheiden", "der Unterschied", "untersuchen", "die Untersuchung",

    # V
    "verändern", "die Veränderung", "verbinden", "die Verbindung",
    "vereinbaren", "die Vereinbarung", "verfolgen", "verhindern",
    "die Verhinderung", "vermitteln", "die Vermittlung", "vernetzen",
    "die Vernetzung", "verstärken", "die Verstärkung", "verwirklichen",
    "die Verwirklichung", "die Vielfalt", "vielfältig", "voraussetzen",
    "die Voraussetzung", "der Vorteil",

    # W
    "wahrnehmen", "die Wahrnehmung", "weiterentwickeln",
    "die Weiterentwicklung", "wertvoll", "der Wert", "sich widmen",
    "wirtschaftlich", "die Wirtschaft", "wirken", "die Wirkung",
    "wirkungsvoll",

    # Z
    "zielen auf", "das Ziel", "zusammenarbeiten", "die Zusammenarbeit",
    "zusammenfassen", "die Zusammenfassung", "der Zusammenhang",
    "zuständig", "die Zuständigkeit", "zuverlässig", "die Zuverlässigkeit",
    "die Zukunft", "zukunftsorientiert",
]


def import_b1_words():
    print(f"Подключаюсь к базе для импорта {len(WORDS_B1)} слов B1...")
    conn = None
    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()

        added_count = 0
        skipped_count = 0

        for word in WORDS_B1:
            cur.execute("SELECT id FROM words WHERE de = %s;", (word,))
            if cur.fetchone():
                skipped_count += 1
                continue

            cur.execute(
                "INSERT INTO words (de, ru, level, topic, examples) VALUES (%s, %s, %s, %s, NULL);",
                (word, "перевод в процессе", "B1", "Goethe B1")
            )
            added_count += 1

        conn.commit()
        print(f"✅ Успешно добавлено новых слов: {added_count}")
        print(f"⏩ Пропущено (уже были в базе): {skipped_count}")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        if conn:
            conn.rollback()
    finally:
        if 'cur' in locals():
            cur.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    import_b1_words()
