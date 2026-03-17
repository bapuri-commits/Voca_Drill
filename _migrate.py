#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect("/app/data/voca_drill.db")
c = conn.cursor()

migrations = [
    ("word_progress", "user_id", "ALTER TABLE word_progress ADD COLUMN user_id INTEGER DEFAULT 1"),
    ("learning_sessions", "user_id", "ALTER TABLE learning_sessions ADD COLUMN user_id INTEGER DEFAULT 1"),
    ("daily_stats", "user_id", "ALTER TABLE daily_stats ADD COLUMN user_id INTEGER DEFAULT 1"),
    ("word_progress", "first_studied_at", "ALTER TABLE word_progress ADD COLUMN first_studied_at DATETIME"),
]

for table, col, sql in migrations:
    try:
        c.execute(sql)
        print(f"OK: {table}.{col} added")
    except Exception as e:
        print(f"SKIP: {table}.{col} - {e}")

# Create index on user_id
for table in ["word_progress", "learning_sessions", "daily_stats"]:
    try:
        c.execute(f"CREATE INDEX IF NOT EXISTS ix_{table}_user_id ON {table}(user_id)")
        print(f"OK: index on {table}.user_id")
    except Exception as e:
        print(f"SKIP: index {table} - {e}")

conn.commit()
conn.close()
print("Migration complete")
