import sqlite3
import os
from database.db import get_db

print("--- Validating Data counts ---")
with get_db() as conn:
    cursor = conn.cursor()
    users = cursor.execute("SELECT id, name, email, password_hash FROM users;").fetchall()
    print(f"Users Count: {len(users)}")
    if len(users) > 0:
        print(f"Demo User: {users[0]['email']}, PassHash prefix: {users[0]['password_hash'][:10]}...")
    
    expenses_count = cursor.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
    print(f"Expenses Count: {expenses_count}")

print("\n--- Validating Duplicate Seed (Running seed_db again) ---")
from database.db import seed_db
seed_db()
with get_db() as conn:
    cursor = conn.cursor()
    users_count2 = cursor.execute("SELECT COUNT(*) FROM users;").fetchone()[0]
    expenses_count2 = cursor.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
    print(f"Users Count after second seed: {users_count2}")
    print(f"Expenses Count after second seed: {expenses_count2}")

print("\n--- Validating Foreign Key Enforcement ---")
try:
    with get_db() as conn:
        conn.execute("INSERT INTO expenses (user_id, category_id, amount, date) VALUES (9999, 9999, 10.0, '2025-01-01')")
    print("WARNING: Foreign key enforcement FAILED. Insert succeeded for bad IDs.")
except sqlite3.IntegrityError as e:
    print(f"SUCCESS: Foreign key enforcement works. Caught error: {e}")
