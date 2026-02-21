import os
import psycopg2
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local')
load_dotenv(dotenv_path)
url = os.getenv("DATABASE_URL")

# Настоящий официальный список Goethe-Institut A1 (полные ~650 слов)
# Никаких ссылок на github, никаких цифр. Только чистый текст.
WORDS_A1 = [
    "der Abend", "aber", "abfahren", "die Abfahrt", "abgeben", "abholen", "der Absender", "Achtung", "die Adresse",
    "all", "allein", "also", "alt", "das Alter", "an", "anbieten", "andere", "anfangen", "der Anfang",
    "anklicken", "ankommen", "die Ankunft", "ankreuzen", "anmachen", "anmelden", "die Anmeldung", "die Anrede",
    "anrufen", "der Anruf", "der Anrufbeantworter", "die Ansage", "antworten", "die Antwort", "die Anzeige",
    "sich anziehen", "das Apartment", "der Apfel", "der Appetit", "arbeiten", "die Arbeit", "arbeitslos",
    "der Arbeitsplatz", "der Arm", "der Arzt", "auch", "auf", "die Aufgabe", "aufhören", "aufstehen",
    "der Aufzug", "das Auge", "aus", "der Ausflug", "ausfüllen", "der Ausgang", "die Auskunft", "das Ausland",
    "der Ausländer", "ausländisch", "ausmachen", "die Aussage", "aussehen", "aussteigen", "der Ausweis",
    "sich ausziehen", "das Auto", "die Autobahn", "der Automat", "automatisch",
    "das Baby", "die Bäckerei", "das Bad", "baden", "die Bahn", "der Bahnhof", "der Bahnsteig", "bald",
    "der Balkon", "die Banane", "die Bank", "bar", "der Bauch", "der Baum", "bedeuten", "beginnen", "bei",
    "beide", "das Bein", "das Beispiel", "bekannt", "bekommen", "benutzen", "der Beruf", "besetzt",
    "besichtigen", "besser", "bestätigen", "bestellen", "besuchen", "das Bett", "bezahlen", "das Bier",
    "das Bild", "billig", "die Birne", "bis", "ein bisschen", "bitte", "bitten", "die Bitte", "bleiben",
    "der Bleistift", "der Blick", "die Blume", "der Bogen", "böse", "brauchen", "breit", "der Brief",
    "die Briefmarke", "bringen", "das Brot", "das Brötchen", "der Bruder", "das Buch", "der Buchstabe",
    "buchstabieren", "der Bus", "die Butter",
    "das Café", "die CD", "der Chef", "circa", "der Computer",
    "da", "die Dame", "daneben", "danken", "der Dank", "dann", "das Datum", "dauern", "dein", "denn", "der",
    "die", "das", "deshalb", "deutlich", "deutsch", "dick", "das Ding", "direkt", "der Direktor", "die Disco",
    "der Doktor", "das Doppelzimmer", "das Dorf", "dort", "draußen", "drucken", "der Drucker", "drücken",
    "durch", "die Durchsage", "dürfen", "der Durst", "duschen", "die Dusche",
    "echt", "die Ecke", "das Ei", "eilig", "ein", "eine", "einfach", "der Eingang", "einkaufen", "einladen",
    "die Einladung", "einmal", "einsteigen", "der Eintritt", "das Einzelzimmer", "die Eltern", "die E-Mail",
    "der Empfänger", "empfehlen", "enden", "das Ende", "entschuldigen", "die Entschuldigung", "er", "sie", "es",
    "das Erdgeschoss", "die Erfahrung", "erklären", "erlauben", "der Erwachsene", "erzählen", "essen", "das Essen",
    "euer", "der Euro",
    "fahren", "der Fahrer", "die Fahrkarte", "das Fahrrad", "falsch", "die Familie", "der Familienname",
    "der Familienstand", "die Farbe", "das Fax", "feiern", "fehlen", "der Fehler", "fernsehen", "das Fernsehen",
    "fertig", "das Feuer", "das Fieber", "der Film", "finden", "die Firma", "der Fisch", "die Flasche",
    "das Fleisch", "fliegen", "der Abflug", "der Flughafen", "das Flugzeug", "das Formular", "das Foto",
    "fragen", "die Frage", "die Frau", "frei", "die Freizeit", "fremd", "sich freuen", "der Freund", "früher",
    "frühstücken", "das Frühstück", "fühlen", "für", "der Fuß", "der Fußball",
    "der Garten", "der Gast", "geben", "geboren", "das Geburtsjahr", "der Geburtsort", "der Geburtstag",
    "gefallen", "gegen", "gehen", "gehören", "das Geld", "das Gemüse", "das Gepäck", "geradeaus", "gern",
    "das Geschäft", "das Geschenk", "die Geschichte", "geschlossen", "das Geschwister", "das Gespräch",
    "gestern", "gesund", "das Getränk", "das Gewicht", "gewinnen", "das Glas", "glauben", "gleich",
    "das Gleis", "das Glück", "glücklich", "gratulieren", "grillen", "groß", "die Größe", "die Großeltern",
    "die Großmutter", "der Großvater", "die Gruppe", "der Gruß", "gültig", "günstig", "gut",
    "das Haar", "haben", "das Hähnchen", "die Halle", "hallo", "halten", "die Haltestelle", "die Hand",
    "das Handy", "das Haus", "die Hausaufgabe", "die Hausfrau", "der Hausmann", "die Heimat", "heiraten",
    "heißen", "helfen", "hell", "heraus", "herein", "der Herr", "herzlich", "heute", "hier", "die Hilfe",
    "hinten", "das Hobby", "hoch", "die Hochzeit", "holen", "hören", "das Hotel", "der Hund", "der Hunger",
    "ich", "ihr", "immer", "in", "die Information", "international", "das Internet",
    "ja", "die Jacke", "jed", "jetzt", "der Job", "der Jugendliche", "jung", "der Junge",
    "der Kaffee", "kaputt", "die Karte", "die Kartoffel", "die Kasse", "kaufen", "kein", "kennen",
    "kennenlernen", "das Kind", "das Kino", "der Kiosk", "klar", "das Kleid", "die Kleidung", "klein",
    "kochen", "der Koffer", "der Kollege", "kommen", "können", "das Konto", "der Kopf", "kosten", "krank",
    "kriegen", "die Küche", "der Kuchen", "der Kühlschrank", "kulturell", "kümmern", "der Kunde", "der Kurs", "kurz",
    "lachen", "der Laden", "das Land", "lang", "lange", "langsam", "laufen", "laut", "leben", "das Leben",
    "die Lebensmittel", "ledig", "leer", "legen", "der Lehrer", "leicht", "leider", "leise", "lernen",
    "lesen", "letzte", "die Leute", "das Licht", "lieb", "lieben", "lieber", "Lieblings-", "das Lied",
    "liegen", "links", "der Lkw", "der Löffel", "das Lokal", "die Lösung", "lustig",
    "machen", "das Mädchen", "man", "der Mann", "männlich", "die Maschine", "das Meer", "mehr", "mein",
    "meist", "der Mensch", "mieten", "die Milch", "mit", "mitbringen", "mitkommen", "mitmachen", "mitnehmen",
    "die Mitte", "die Möbel", "möchten", "mögen", "möglich", "der Moment", "morgen", "müde", "der Mund",
    "das Museum", "die Musik", "müssen", "die Mutter",
    "nach", "nächste", "die Nacht", "der Name", "die Natur", "natürlich", "neben", "nehmen", "nein", "neu",
    "nicht", "nichts", "nie", "niemand", "noch", "normal", "die Note", "notieren", "die Nummer", "nur",
    "oben", "das Obst", "oder", "offen", "öffnen", "oft", "ohne", "das Ohr", "das Öl", "die Oma", "der Opa",
    "die Ordnung", "der Ort",
    "das Papier", "die Papiere", "der Park", "parken", "der Partner", "die Party", "der Pass", "die Pause",
    "die Person", "das Pferd", "die Pflanze", "die Pizza", "der Platz", "die Polizei", "die Pommes frites",
    "die Post", "die Postleitzahl", "das Praktikum", "die Praxis", "der Preis", "das Problem", "der Prospekt",
    "prüfen", "die Prüfung", "pünktlich",
    "rauchen", "der Raum", "die Rechnung", "rechts", "reden", "der Regen", "regnen", "der Reis", "reisen",
    "die Reise", "das Reisebüro", "der Reiseführer", "reparieren", "das Restaurant", "die Rezeption", "richtig",
    "riechen", "ruhig",
    "der Saft", "sagen", "der Salat", "das Salz", "der Satz", "die S-Bahn", "der Schalter", "scheinen",
    "schicken", "das Schild", "der Schinken", "schlafen", "schlecht", "schließen", "der Schluss", "der Schlüssel",
    "schmecken", "schnell", "schon", "schön", "der Schrank", "schreiben", "der Schuh", "die Schule", "der Schüler",
    "schwer", "die Schwester", "schwimmen", "der See", "sehen", "die Sehenswürdigkeit", "sehr", "sein", "seit",
    "selbst", "senden", "sicher", "singen", "sitzen", "so", "das Sofa", "sofort", "der Sohn", "sollen",
    "die Sonne", "spät", "später", "der Spaß", "spazieren gehen", "speichern", "die Speisekarte", "spielen",
    "der Sport", "die Sprache", "sprechen", "die Stadt", "stehen", "die Stelle", "stellen", "der Stock",
    "die Straße", "die Straßenbahn", "studieren", "das Studium", "der Student", "die Stunde", "suchen",
    "super", "die Suppe",
    "tanzen", "die Tasche", "das Taxi", "der Tee", "der Teil", "telefonieren", "das Telefon", "teuer",
    "der Text", "das Thema", "das Ticket", "der Tisch", "die Tochter", "die Toilette", "die Tomate", "tot",
    "tragen", "trainieren", "traurig", "treffen", "die Treppe", "trinken", "tschüss", "tun",
    "über", "überall", "übernachten", "übersetzen", "die Übung", "die Uhr", "um", "umsteigen", "und", "unser",
    "unten", "unter", "der Unterricht", "unterschreiben", "die Unterschrift", "der Urlaub",
    "der Vater", "verboten", "verdienen", "der Verein", "verkaufen", "der Verkäufer", "vermieten",
    "der Vermieter", "verstehen", "der Verwandte", "viel", "vielleicht", "von", "vor", "der Vorname",
    "Vorsicht", "vorstellen",
    "wahr", "wandern", "wann", "warten", "warum", "was", "waschen", "das Wasser", "weh tun", "weiblich",
    "der Wein", "weit", "weiter", "welch", "die Welt", "wenig", "wer", "werden", "das Wetter", "wichtig",
    "wie", "wiederholen", "das Wiedersehen", "wie viel", "willkommen", "der Wind", "wir", "wissen", "wo",
    "woher", "wohin", "wohnen", "die Wohnung", "wollen", "das Wort", "wunderbar",
    "die Zahl", "zahlen", "die Zeit", "die Zeitschrift", "die Zeitung", "das Zelt", "das Zentrum",
    "der Zettel", "das Zeugnis", "ziehen", "das Ziel", "die Zigarette", "das Zimmer", "der Zoll",
    "zu", "der Zug", "zumachen", "zurück", "zusammen", "zwischen"
]

def import_clean_650_words():
    print(f"Подключаюсь к базе для импорта {len(WORDS_A1)} чистых слов A1...")
    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        
        added_count = 0
        skipped_count = 0
        
        for word in WORDS_A1:
            cur.execute("SELECT id FROM words WHERE de = %s;", (word,))
            if cur.fetchone():
                skipped_count += 1
                continue
                
            cur.execute(
                "INSERT INTO words (de, ru, level, topic, examples) VALUES (%s, %s, %s, %s, NULL);",
                (word, "перевод в процессе", "A1", "Goethe A1")
            )
            added_count += 1
            
        conn.commit()
        print(f"✅ Успешно добавлено новых слов: {added_count}")
        print(f"⏩ Пропущено (уже были в базе): {skipped_count}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        if conn: conn.rollback()
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    import_clean_650_words()
