import os
import psycopg2
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.local')
load_dotenv(dotenv_path)
url = os.getenv("DATABASE_URL")

def get_base_word(word):
    """Очищает слово от артиклей и пробелов для точного сравнения"""
    if not word: return ""
    w = word.strip().lower()
    for article in ["der ", "die ", "das "]:
        if w.startswith(article):
            return w[4:].strip()
    return w

def remove_smart_duplicates():
    conn = None
    cur = None
    try:
        print("Подключаюсь к базе для умного поиска дубликатов...")
        conn = psycopg2.connect(url)
        cur = conn.cursor()

        # Вытаскиваем вообще все слова
        cur.execute("SELECT id, de, level FROM words ORDER BY id ASC;")
        all_words = cur.fetchall()

        # Группируем слова по их очищенному корню (например 'schule')
        word_groups = {}
        for row in all_words:
            w_id, de, level = row
            base = get_base_word(de)
            if base not in word_groups:
                word_groups[base] = []
            word_groups[base].append(row)

        total_deleted = 0

        # Проходим по группам, где больше 1 слова
        for base_word, group in word_groups.items():
            if len(group) > 1:
                print(f"⚠️ Найден дубликат: {base_word} -> {[w[1] for w in group]}")
                
                # Сортируем: сначала по уровню (A1 -> A2 -> B1 -> B2), потом по ID
                # Чтобы сохранить слово с самым ранним уровнем и самым старым ID
                level_order = {"A1": 1, "A2": 2, "B1": 3, "B2": 4}
                group.sort(key=lambda x: (level_order.get(x[2], 99), x[0]))

                keep_id = group[0][0]
                delete_ids = [w[0] for w in group[1:]]

                for del_id in delete_ids:
                    # Список таблиц, которые нужно "почистить" перед удалением слова
                    referencing_tables = ["user_words", "user_favorites", "user_word_notes"]
                    
                    for table in referencing_tables:
                        # Разрешаем конфликты (если у юзера есть и эталонное слово, и дубликат)
                        cur.execute(f"SELECT user_id FROM {table} WHERE word_id = %s;", (keep_id,))
                        users_with_keep = [r[0] for r in cur.fetchall()]
                        
                        if users_with_keep:
                            # Удаляем дубликат у этих юзеров, так как у них уже есть "основное" слово
                            cur.execute(
                                f"DELETE FROM {table} WHERE word_id = %s AND user_id = ANY(%s);",
                                (del_id, users_with_keep)
                            )
                        
                        # Перепривязываем всех остальных юзеров от дубликата к эталону
                        cur.execute(
                            f"UPDATE {table} SET word_id = %s WHERE word_id = %s;",
                            (keep_id, del_id)
                        )
                    
                    # Теперь, когда все связи перенесены, удаляем дубликат из основной таблицы
                    cur.execute("DELETE FROM words WHERE id = %s;", (del_id,))
                    total_deleted += 1
                    
        conn.commit()
        if total_deleted > 0:
            print(f"🎉 Успешно вычищено {total_deleted} скрытых дубликатов!")
        else:
            print("✅ Скрытых дубликатов не найдено.")

    except Exception as e:
        print(f"❌ Ошибка при удалении: {e}")
        if conn: conn.rollback()
    finally:
        if cur: cur.close()
        if conn: conn.close()

if __name__ == "__main__":
    remove_smart_duplicates()
