import os
import sys

# Add the current directory to sys.path
sys.path.append(os.path.dirname(__file__))

from api.db import get_db_connection

# Common verbs and their forms (3rd person singular present, präteritum, perfekt)
VERB_FORMS_DATA = [
    {"de": "anfangen", "forms": "fängt an, fing an, hat angefangen"},
    {"de": "anrufen", "forms": "ruft an, rief an, hat angerufen"},
    {"de": "antworten", "forms": "antwortet, antwortete, hat geantwortet"},
    {"de": "arbeiten", "forms": "arbeitet, arbeitete, hat gearbeitet"},
    {"de": "aufhören", "forms": "hört auf, hörte auf, hat aufgehört"},
    {"de": "aufstehen", "forms": "steht auf, stand auf, ist aufgestanden"},
    {"de": "bekommen", "forms": "bekommt, bekam, hat bekommen"},
    {"de": "bestellen", "forms": "bestellt, bestellte, hat bestellt"},
    {"de": "bleiben", "forms": "bleibt, blieb, ist geblieben"},
    {"de": "brauchen", "forms": "braucht, brauchte, hat gebraucht"},
    {"de": "bringen", "forms": "bringt, brachte, hat gebracht"},
    {"de": "danken", "forms": "dankt, dankte, hat gedankt"},
    {"de": "denken", "forms": "denkt, dachte, hat gedacht"},
    {"de": "essen", "forms": "isst, aß, hat gegessen"},
    {"de": "fahren", "forms": "fährt, fuhr, ist gefahren"},
    {"de": "finden", "forms": "findet, fand, hat gefunden"},
    {"de": "fragen", "forms": "fragt, fragte, hat gefragt"},
    {"de": "geben", "forms": "gibt, gab, hat gegeben"},
    {"de": "gehen", "forms": "geht, ging, ist gegangen"},
    {"de": "helfen", "forms": "hilft, half, hat geholfen"},
    {"de": "hören", "forms": "hört, hörte, hat gehört"},
    {"de": "kaufen", "forms": "kauft, kaufte, hat gekauft"},
    {"de": "kochen", "forms": "kocht, kochte, hat gekocht"},
    {"de": "kommen", "forms": "kommt, kam, ist gekommen"},
    {"de": "lernen", "forms": "lernt, lernte, hat gelernt"},
    {"de": "lesen", "forms": "liest, las, hat gelesen"},
    {"de": "machen", "forms": "macht, machte, hat gemacht"},
    {"de": "nehmen", "forms": "nimmt, nahm, hat genommen"},
    {"de": "schreiben", "forms": "schreibt, schrieb, hat geschrieben"},
    {"de": "sehen", "forms": "sieht, sah, hat gesehen"},
    {"de": "spielen", "forms": "spielt, spielte, hat gespielt"},
    {"de": "sprechen", "forms": "spricht, sprach, hat gesprochen"},
    {"de": "trinken", "forms": "trinkt, trank, hat getrunken"},
    {"de": "verstehen", "forms": "versteht, verstand, hat verstanden"},
    {"de": "warten", "forms": "wartet, wartete, hat gewartet"},
    {"de": "wohnen", "forms": "wohnt, wohnte, hat gewohnt"}
]

def update_verb_forms():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        count = 0
        for item in VERB_FORMS_DATA:
            cur.execute("""
                UPDATE words 
                SET verb_forms = %s 
                WHERE de = %s
            """, (item['forms'], item['de']))
            count += cur.rowcount
            
        conn.commit()
        cur.close()
        conn.close()
        print(f"Successfully updated verb forms for {count} verbs.")
        
    except Exception as e:
        print(f"Error updating verb forms: {e}")

if __name__ == "__main__":
    update_verb_forms()
