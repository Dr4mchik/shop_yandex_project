from .db_session import global_init, create_session
import sqlite3

# Initialize your database connection
db_path = "path/to/your/database.sqlite"  # Replace with actual path
global_init(db_path)

# Connect directly with sqlite3 to modify the table structure
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if the column already exists
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