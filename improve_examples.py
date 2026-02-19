import os
import sys

# Add the current directory to sys.path
sys.path.append(os.path.dirname(__file__))

from api.db import get_db_connection

# A selection of improved, more "interesting" examples
IMPROVED_EXAMPLES = [
    {
        "de": "anfangen",
        "ex_de": "Wir müssen pünktlich anfangen, sonst verpassen wir den Anfang des Konzerts.",
        "ex_ru": "Нам нужно начать вовремя, иначе мы пропустим начало концерта."
    },
    {
        "de": "Tisch",
        "ex_de": "Wir sitzen jeden Abend gemeinsam an dem großen Holztisch in der Küche.",
        "ex_ru": "Мы каждый вечер сидим вместе за большим деревянным столом на кухне."
    },
    {
        "de": "Fenster",
        "ex_de": "Könntest du bitte das Fenster öffnen? Die Luft im Zimmer ist sehr stickig.",
        "ex_ru": "Не мог бы ты открыть окно? В комнате очень душно."
    },
    {
        "de": "arbeiten",
        "ex_de": "Ich arbeite momentan an einem sehr interessanten Projekt bei einer internationalen Firma.",
        "ex_ru": "В данный момент я работаю над очень интересным проектом в международной компании."
    },
    {
        "de": "essen",
        "ex_de": "Am Wochenende essen wir oft in einem kleinen italienischen Restaurant um die Ecke.",
        "ex_ru": "По выходным мы часто едим в маленьком итальянском ресторанчике за углом."
    },
    {
        "de": "fahren",
        "ex_de": "Morgen fahren wir mit dem Zug nach München, um unsere Großeltern zu besuchen.",
        "ex_ru": "Завтра we едем на поезде в Мюнхен, чтобы навестить наших бабушку и дедушку."
    },
    {
        "de": "helfen",
        "ex_de": "Könntest du mir bitte dabei helfen, diese schweren Kisten in den Keller zu tragen?",
        "ex_ru": "Не мог бы ты помочь мне отнести эти тяжелые коробки в подвал?"
    },
    {
        "de": "lernen",
        "ex_de": "Ich lerne jeden Tag eine Stunde Deutsch, um mich bald mit meinen Nachbarn unterhalten zu können.",
        "ex_ru": "Я учу немецкий каждый день по часу, чтобы скоро иметь возможность общаться с соседями."
    },
    {
        "de": "schreiben",
        "ex_de": "Ich schreibe meiner Freundin in Berlin jede Woche einen langen Brief per Post.",
        "ex_ru": "Я каждую неделю пишу своей подруге в Берлине длинное письмо по почте."
    },
    {
        "de": "lesen",
        "ex_de": "Im Urlaub lese ich am liebsten spannende Krimis am Strand.",
        "ex_ru": "В отпуске я больше всего люблю читать захватывающие детективы на пляже."
    },
    {
        "de": "Haus",
        "ex_de": "Hinter unserem Haus gibt es einen wunderschönen Garten mit vielen Blumen und Bäumen.",
        "ex_ru": "За нашим домом есть чудесный сад с множеством цветов и деревьев."
    },
    {
        "de": "Schule",
        "ex_de": "Nach der Schule gehen die Kinder oft zusammen auf den Spielplatz im Park.",
        "ex_ru": "После школы дети часто ходят вместе на игровую площадку в парке."
    },
    {
        "de": "Freund",
        "ex_de": "Mein bester Freund wohnt schon seit zehn Jahren in Hamburg und arbeitet dort als Arzt.",
        "ex_ru": "Мой лучший друг живет в Гамбурге уже десять лет и работает там врачом."
    },
    {
        "de": "Wetter",
        "ex_de": "Trotz des schlechten Wetters haben wir uns entschieden, einen langen Spaziergang zu machen.",
        "ex_ru": "Несмотря на плохую погоду, мы решили совершить долгую прогулку."
    },
    {
        "de": "Stadt",
        "ex_de": "In der Innenstadt gibt es viele historische Gebäude und gemütliche Cafés.",
        "ex_ru": "В центре города много исторических зданий и уютных кафе."
    }
]

def improve_examples():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        count = 0
        for item in IMPROVED_EXAMPLES:
            cur.execute("""
                UPDATE words 
                SET example_de = %s, example_ru = %s 
                WHERE de = %s
            """, (item['ex_de'], item['ex_ru'], item['de']))
            count += cur.rowcount
            
        conn.commit()
        cur.close()
        conn.close()
        print(f"Successfully improved examples for {count} words.")
        
    except Exception as e:
        print(f"Error improving examples: {e}")

if __name__ == "__main__":
    improve_examples()
