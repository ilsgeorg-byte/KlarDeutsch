from api.db import get_db_connection

def check_words():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, de, article, ru FROM words WHERE de ILIKE '%Hund%' OR de ILIKE '%Besprechung%'")
    rows = cur.fetchall()
    for row in rows:
        print(f"ID: {row[0]}, DE: {row[1]}, ARTICLE: {row[2]}, RU: {row[3]}")
    conn.close()

if __name__ == "__main__":
    check_words()
