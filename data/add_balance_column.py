from .db_session import global_init, create_session
import sqlite3

db_path = "path/to/your/database.sqlite"
global_init(db_path)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(users)")
columns = [info[1] for info in cursor.fetchall()]

if "balance" not in columns:
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN balance FLOAT DEFAULT 0.0 NOT NULL")
        conn.commit()
        print("Added 'balance' column to users table")
    except Exception as e:
        print(f"Error adding column: {e}")
else:
    print("Column 'balance' already exists")

conn.close()
