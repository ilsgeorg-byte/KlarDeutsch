import os
import psycopg2
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local')
load_dotenv(dotenv_path)
url = os.getenv("DATABASE_URL")

# Официальный список Goethe-Institut A2 (~1300 слов)
# Использован как ориентир по уровню; все записи — собственная подборка.
WORDS_A2 = [
    # A
    "ab und zu", "der Abfall", "die Abfallentsorgung", "abgeben", "abhängen", "die Abhängigkeit",
    "ablehnen", "abnehmen", "abonnieren", "das Abonnement", "abreisen", "der Absatz",
    "abschalten", "abschließen", "der Abschluss", "die Absicht", "abstimmen", "die Abteilung",
    "die Abwechslung", "ärgerlich", "sich ärgern", "der Ärger", "ähnlich", "die Ähnlichkeit",
    "ändern", "die Änderung", "das Angebot", "die Angst", "sich anmelden", "annehmen",
    "anprobieren", "anschauen", "ansehen", "die Ansicht", "anstrengend", "die Anstrengung",
    "die Anzeige", "der Anzug", "der Apotheker", "der Appetit", "die Arbeitsstelle",
    "der Arbeitsvertrag", "das Arbeitsamt", "die Arbeitszeit", "der Architekt", "der Ärmel",
    "die Atmosphäre", "auch wenn", "auffordern", "aufnehmen", "aufpassen", "aufräumen",
    "der Aufenthalt", "aufgeregt", "aufheben", "auflegen", "auflösen", "aufmachen",
    "aufmerksam", "die Aufmerksamkeit", "aufregend", "der Auftrag", "der Aufwand",
    "ausdrücken", "der Ausdruck", "ausführen", "die Ausführung", "ausleihen", "auspacken",
    "ausrechnen", "ausruhen", "sich ausruhen", "ausschalten", "aussuchen", "austauschen",
    "der Austausch", "auswählen", "die Auswahl", "die Ausbildung", "das Ausbildungszentrum",

    # B
    "die Bäckerin", "das Badezimmer", "die Bahn", "bald", "der Balkon", "die Band",
    "die Bar", "der Bart", "bauen", "die Baustelle", "beantragen", "der Antrag",
    "bearbeiten", "bedanken", "sich bedanken", "die Bedingung", "sich beeilen", "beenden",
    "befragen", "sich befinden", "die Begegnung", "begegnen", "begeistert", "die Begeisterung",
    "begleiten", "die Begleitung", "der Begriff", "behalten", "behandeln", "die Behandlung",
    "beitragen", "der Beitrag", "beklagen", "sich beklagen", "belegen", "beliebt",
    "bemerken", "benutzen", "die Benutzung", "bereit", "bereits", "beschreiben",
    "die Beschreibung", "besichtigen", "besonders", "bestehen", "bestimmt", "bewerben",
    "sich bewerben", "die Bewerbung", "bezahlen", "die Bibliothek", "bieten", "die Bildung",
    "die Bluse", "die Bohne", "braten", "die Brust", "das Büro", "der Bürger",
    "die Bürgermeisterin", "der Bürgermeister",

    # C
    "die Chance", "charakteristisch", "chatten", "der Club",

    # D
    "dagegen", "daher", "damit", "danach", "daran", "darüber", "darum", "dass",
    "dauerhaft", "dazu", "dazugehören", "denken", "deswegen", "deutlich", "diesmal",
    "diskutieren", "die Diskussion", "doch", "der Dom", "doppelt", "draußen",
    "drücken", "dunkel", "durchführen", "die Durchführung",

    # E
    "egal", "ehrenamtlich", "das Ehrenamt", "eigentlich", "einander", "die Einheit",
    "einige", "einladen", "die Einladung", "sich einigen", "die Einigung", "einkaufen",
    "das Einkaufszentrum", "einschlafen", "einverstanden", "das Einverständnis",
    "elektrisch", "die Elektronik", "empfehlen", "die Empfehlung", "das Engagement",
    "engagiert", "sich engagieren", "entscheiden", "die Entscheidung", "sich entspannen",
    "die Entspannung", "erfahren", "die Erfahrung", "erfolgreich", "der Erfolg",
    "erinnern", "sich erinnern", "die Erinnerung", "erklären", "erleben", "das Erlebnis",
    "erledigen", "die Erledigung", "ernst", "erreichen", "erscheinen", "erst", "erwarten",
    "die Erwartung", "erzählen", "die Erzählung",

    # F
    "die Fähigkeit", "die Fahrt", "fallen", "die Farbe", "fast", "fehlen",
    "feiern", "das Fest", "feststellen", "fit", "das Fitnessstudio", "fleißig",
    "folgen", "die Folge", "fordern", "die Forderung", "der Fortschritt", "fortsetzen",
    "fotografieren", "das Foto", "froh", "führen", "füllen", "funktionieren",

    # G
    "die Galerie", "ganz", "die Garantie", "das Gebäude", "gefährlich",
    "die Gefahr", "das Gefühl", "gemeinsam", "genug", "genießen", "das Gepäck",
    "das Gericht", "gern haben", "das Geschäft", "die Geschichte", "das Gesetz",
    "gestalten", "die Gestaltung", "das Gewicht", "gewinnen", "glauben", "gleich",
    "die Gleichheit", "glücklicherweise", "gratulieren", "die Gratulation", "der Grund",
    "gültig", "günstig",

    # H
    "der Haushalt", "häufig", "die Hauptstadt", "das Heimweh", "helfen", "der Helm",
    "herausfinden", "herunterladen", "das Herz", "herzlich", "hilfsbereit", "die Hilfsbereitschaft",
    "hinweisen", "der Hinweis", "das Hobby", "hoffen", "die Hoffnung", "höflich",
    "die Höflichkeit", "der Hof", "holen", "der Hunger",

    # I
    "die Idee", "immer noch", "inklusive", "innerhalb", "interessant",
    "sich interessieren", "das Interesse", "irgendwo", "irgendwann",

    # J
    "jedenfalls", "jemand", "jedoch", "jubeln",

    # K
    "der Kalender", "die Karriere", "die Kasse", "kaufen", "die Kenntnisse",
    "die Kindheit", "klappen", "die Klasse", "das Klima", "die Klinik",
    "das Knie", "der Koch", "die Köchin", "der Körper", "die Kosten",
    "krankenversichert", "die Krankenversicherung", "kreativ", "die Kreativität",
    "der Kreis", "kriegen", "kulturell", "der Künstler", "die Künstlerin",
    "der Kundendienst", "die Kündigung", "kündigen",

    # L
    "das Labor", "das Lager", "langweilig", "die Langeweile", "laut",
    "leider", "die Leistung", "leisten", "sich leisten", "leihen", "lösen",
    "die Lösung", "lustig", "die Lust", "Lust haben",

    # M
    "manchmal", "die Mannschaft", "der Markt", "der Mechaniker", "die Mechanikerin",
    "melden", "sich melden", "die Meinung", "meinen", "der Mietvertrag", "mindestens",
    "der Mitarbeiter", "die Mitarbeiterin", "das Mitglied", "mieten", "mitkommen",
    "mitteilen", "die Mitteilung", "die Mode", "motiviert", "die Motivation",
    "der Müll", "müssen",

    # N
    "die Nachbarschaft", "der Nachbar", "nachfragen", "nachher", "nachschlagen",
    "die Nachricht", "die Natur", "neben", "die Neugier", "neugierig",
    "die Niederlage", "noch einmal", "normalerweise",

    # O
    "oben", "obwohl", "die Öffnungszeiten", "öffentlich", "das öffentliche Verkehrsmittel",
    "ordnen", "die Organisation", "organisieren",

    # P
    "das Paket", "der Parkplatz", "die Pension", "die Pflicht", "der Plan",
    "planen", "die Planung", "plus", "politisch", "die Politik", "das Portemonnaie",
    "das Postfach", "die Praxis", "probieren", "professionell", "das Programm",
    "das Projekt", "pünktlich", "die Pünktlichkeit",

    # R
    "der Rat", "der Ratschlag", "reagieren", "recht haben", "die Regel", "regelmäßig",
    "das Regal", "reichen", "die Reinigung", "reservieren", "die Reservierung",
    "richten", "richtig", "riskieren", "das Risiko", "ruhig",

    # S
    "sammeln", "die Sammlung", "sanft", "der Satz", "schaffen", "schätzen",
    "die Schicht", "das Schild", "schimpfen", "schlimm", "der Schmerz", "schmerzen",
    "der Schnitt", "die Schokolade", "schützen", "der Schutz", "schwierig",
    "die Schwierigkeit", "das Selfie", "die Sendung", "sicher", "die Sicherheit",
    "sinnvoll", "der Sinn", "die Situation", "sogar", "sonst", "sorgen", "die Sorge",
    "sozial", "die Sozialversicherung", "der Spaß", "der Spaziergang", "spazieren",
    "die Speisekarte", "der Sportverein", "der Stadtplan", "stattfinden", "stecken",
    "stellen", "die Stelle", "die Stimmung", "stören", "der Stress", "streng",
    "die Stunde", "suchen", "surfen",

    # T
    "die Tablette", "das Tagebuch", "täglich", "tanken", "das Team", "teilnehmen",
    "die Teilnahme", "der Teilnehmer", "die Teilnehmerin", "das Thema", "toll",
    "touristisch", "traditionell", "die Tradition", "trainieren", "das Training",
    "treu", "trotzdem", "typisch",

    # U
    "die Überstunde", "die Umgebung", "umziehen", "der Umzug", "die Umwelt",
    "umweltfreundlich", "unbedingt", "unbekannt", "ungewöhnlich", "unterschiedlich",
    "unterstützen", "die Unterstützung", "unterwegs", "das Urteil",

    # V
    "die Verantwortung", "verantwortlich", "verbessern", "die Verbesserung",
    "vergleichen", "der Vergleich", "verlieren", "der Verlust", "vermissen",
    "verschieden", "verspäten", "die Verspätung", "verstecken", "versuchen",
    "der Versuch", "verwenden", "die Verwendung", "die Vorbereitung", "sich vorbereiten",
    "vorhaben", "das Vorhaben", "vorstellen", "das Vorstellungsgespräch",
    "der Vorteil", "der Vortrag",

    # W
    "wählen", "die Wahl", "wahrscheinlich", "der Weg", "wegen", "wehtun",
    "weinen", "weiterhelfen", "weiterhin", "die Werbung", "das Werkzeug",
    "wetten", "wie lange", "die Wiederholung", "wiederholen", "winken",
    "wissen", "das Wohlbefinden", "wütend", "die Wut",

    # Z
    "zeichnen", "die Zeichnung", "das Zeichen", "zeigen", "die Zeitung",
    "zögern", "zufrieden", "die Zufriedenheit", "zuhören", "die Zukunft",
    "zurückkommen", "zuständig", "die Zuständigkeit", "zuverlässig",
    "die Zuverlässigkeit", "zweimal",
]


def import_a2_words():
    print(f"Подключаюсь к базе для импорта {len(WORDS_A2)} слов A2...")
    conn = None
    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()

        added_count = 0
        skipped_count = 0

        for word in WORDS_A2:
            cur.execute("SELECT id FROM words WHERE de = %s;", (word,))
            if cur.fetchone():
                skipped_count += 1
                continue

            cur.execute(
                "INSERT INTO words (de, ru, level, topic, examples) VALUES (%s, %s, %s, %s, NULL);",
                (word, "перевод в процессе", "A2", "Goethe A2")
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
    import_a2_words()
