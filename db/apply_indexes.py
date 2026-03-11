#!/usr/bin/env python3
"""
Script to apply strategic indexes for optimal database performance
"""
import os
import sys
import logging
from contextlib import contextmanager

# Add parent directory to path
api_dir = os.path.dirname(os.path.abspath(__file__))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from db import get_db_connection

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_indexes():
    """Apply strategic indexes for optimal query performance"""
    conn = None
    cur = None
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        logger.info("Applying strategic indexes for optimal performance...")
        
        # Indexes for the words table
        logger.info("Creating indexes for words table...")
        
        # Index for level-based queries (used in GET /api/words and trainer)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_words_level 
            ON words (level)
        """)
        logger.info("✓ Created index on words.level")
        
        # Index for topic-based queries (used in GET /api/words/by-topic/<topic>)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_words_topic 
            ON words (topic)
        """)
        logger.info("✓ Created index on words.topic")
        
        # Composite index for level + user_id (used in most word queries)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_words_level_user_id 
            ON words (level, user_id)
        """)
        logger.info("✓ Created composite index on words (level, user_id)")
        
        # Index for user_id (used in personal word queries)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_words_user_id 
            ON words (user_id)
        """)
        logger.info("✓ Created index on words.user_id")
        
        # Indexes for text search (used in GET /api/words/search)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_words_de_gin 
            ON words USING gin(to_tsvector('german', de))
        """)
        logger.info("✓ Created GIN index for German text search")
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_words_ru_gin 
            ON words USING gin(to_tsvector('russian', ru))
        """)
        logger.info("✓ Created GIN index for Russian text search")
        
        # Alternative pattern matching indexes for search
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_words_de_text_pattern_ops 
            ON words (de varchar_pattern_ops)
        """)
        logger.info("✓ Created pattern index for German text search")
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_words_ru_text_pattern_ops 
            ON words (ru varchar_pattern_ops)
        """)
        logger.info("✓ Created pattern index for Russian text search")
        
        # Index for ID ordering (used in pagination)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_words_id 
            ON words (id)
        """)
        logger.info("✓ Created index on words.id")
        
        # Indexes for the user_words table (used in trainer functionality)
        logger.info("Creating indexes for user_words table...")
        
        # Index for next_review (critical for trainer - finding words to review)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_words_next_review 
            ON user_words (next_review)
        """)
        logger.info("✓ Created index on user_words.next_review")
        
        # Composite index for user_id + next_review (used in trainer queries)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_words_user_review 
            ON user_words (user_id, next_review)
        """)
        logger.info("✓ Created composite index on user_words (user_id, next_review)")
        
        # Index for user_id + status (used in trainer and stats)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_words_user_status 
            ON user_words (user_id, status)
        """)
        logger.info("✓ Created composite index on user_words (user_id, status)")
        
        # Index for user_id (used in various queries)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_words_user_id 
            ON user_words (user_id)
        """)
        logger.info("✓ Created index on user_words.user_id")
        
        # Index for word_id (used in joins)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_words_word_id 
            ON user_words (word_id)
        """)
        logger.info("✓ Created index on user_words.word_id")
        
        # Indexes for the user_favorites table
        logger.info("Creating indexes for user_favorites table...")
        
        # Index for user_id (used in GET /api/favorites)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_favorites_user_id 
            ON user_favorites (user_id)
        """)
        logger.info("✓ Created index on user_favorites.user_id")
        
        # Index for word_id (used in joins and favorite toggling)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_favorites_word_id 
            ON user_favorites (word_id)
        """)
        logger.info("✓ Created index on user_favorites.word_id")
        
        # Composite index for user-word pairs (used in toggle_favorite)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_favorites_user_word 
            ON user_favorites (user_id, word_id)
        """)
        logger.info("✓ Created composite index on user_favorites (user_id, word_id)")
        
        # Indexes for the user_word_notes table
        logger.info("Creating indexes for user_word_notes table...")
        
        # Composite index for user-word pairs (used in notes queries)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_word_notes_user_word 
            ON user_word_notes (user_id, word_id)
        """)
        logger.info("✓ Created composite index on user_word_notes (user_id, word_id)")
        
        # Index for the recordings table
        logger.info("Creating indexes for recordings table...")
        
        # Index for user_id (used in audio functionality)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_recordings_user_id 
            ON recordings (user_id)
        """)
        logger.info("✓ Created index on recordings.user_id")
        
        # Commit all changes
        conn.commit()
        logger.info("✅ All strategic indexes applied successfully!")
        
        # Show some statistics about the indexes
        logger.info("\n📊 Index statistics:")
        
        # Count total words
        cur.execute("SELECT COUNT(*) FROM words")
        total_words = cur.fetchone()[0]
        logger.info(f"Total words in database: {total_words}")
        
        # Count total user_words
        cur.execute("SELECT COUNT(*) FROM user_words")
        total_user_words = cur.fetchone()[0]
        logger.info(f"Total user-word progress records: {total_user_words}")
        
        # Show index information
        cur.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename IN ('words', 'user_words', 'user_favorites', 'user_word_notes', 'recordings')
            ORDER BY tablename, indexname
        """)
        indexes = cur.fetchall()
        logger.info(f"Total indexes created: {len(indexes)}")
        
        for idx in indexes:
            logger.info(f"  - {idx[0]}")
        
    except Exception as e:
        logger.error(f"Error applying indexes: {str(e)}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            from db import return_db_connection
            return_db_connection(conn)

def validate_indexes():
    """Validate that all expected indexes exist"""
    conn = None
    cur = None
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        logger.info("\n🔍 Validating indexes...")
        
        # Check for critical indexes
        critical_indexes = [
            ('words', 'idx_words_level'),
            ('words', 'idx_words_level_user_id'),
            ('user_words', 'idx_user_words_next_review'),
            ('user_words', 'idx_user_words_user_review'),
            ('user_favorites', 'idx_user_favorites_user_id'),
            ('user_favorites', 'idx_user_favorites_word_id')
        ]
        
        all_good = True
        for table_name, index_name in critical_indexes:
            cur.execute("""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = %s AND indexname = %s
            """, (table_name, index_name))
            
            if not cur.fetchone():
                logger.warning(f"❌ Missing critical index: {index_name} on {table_name}")
                all_good = False
            else:
                logger.info(f"✓ Found critical index: {index_name}")
        
        if all_good:
            logger.info("✅ All critical indexes are present!")
        else:
            logger.warning("⚠️  Some critical indexes are missing!")
            
    except Exception as e:
        logger.error(f"Error validating indexes: {str(e)}")
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            from db import return_db_connection
            return_db_connection(conn)

if __name__ == "__main__":
    logger.info("🚀 Starting strategic indexing process...")
    apply_indexes()
    validate_indexes()
    logger.info("✅ Strategic indexing completed successfully!")
