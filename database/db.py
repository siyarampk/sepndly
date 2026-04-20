import sqlite3
import os
from flask import Flask
from werkzeug.security import generate_password_hash

DATABASE = os.path.join(os.path.dirname(__file__), '..', 'spendly.db')


def get_db():
    """Returns a SQLite connection with row_factory and foreign keys enabled."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Creates all tables using CREATE TABLE IF NOT EXISTS."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            icon TEXT DEFAULT '₹',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create expenses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)
    
    conn.commit()
    conn.close()


def seed_db():
    """Inserts sample data for development."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if users already exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    # Insert default categories
    categories = [
        ('Food', '🍔'),
        ('Transport', '🚌'),
        ('Bills', '💡'),
        ('Health', '💊'),
        ('Entertainment', '🎬'),
        ('Shopping', '🛒'),
        ('Education', '📚'),
        ('Other', '📦')
    ]
    
    cursor.executemany(
        "INSERT INTO categories (name, icon) VALUES (?, ?)",
        categories
    )
    
    # Insert demo user
    password_hash = generate_password_hash('demo123')
    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", password_hash)
    )
    demo_user_id = cursor.lastrowid
    
    # Get category IDs to map correctly
    cursor.execute("SELECT id, name FROM categories")
    cat_map = {row['name']: row['id'] for row in cursor.fetchall()}
    
    # Prepare 8 sample expenses using recent dates
    import datetime
    today = datetime.date.today()
    
    sample_expenses = [
        (demo_user_id, cat_map.get('Food', 1), 250.0, 'Lunch at local cafe', (today - datetime.timedelta(days=1)).isoformat()),
        (demo_user_id, cat_map.get('Transport', 2), 120.0, 'Uber to office', (today - datetime.timedelta(days=2)).isoformat()),
        (demo_user_id, cat_map.get('Bills', 3), 1500.0, 'Electricity bill', (today - datetime.timedelta(days=3)).isoformat()),
        (demo_user_id, cat_map.get('Health', 4), 500.0, 'Pharmacy', (today - datetime.timedelta(days=5)).isoformat()),
        (demo_user_id, cat_map.get('Entertainment', 5), 800.0, 'Movie tickets', (today - datetime.timedelta(days=7)).isoformat()),
        (demo_user_id, cat_map.get('Shopping', 6), 2000.0, 'New shirt', (today - datetime.timedelta(days=8)).isoformat()),
        (demo_user_id, cat_map.get('Food', 1), 450.0, 'Dinner', (today - datetime.timedelta(days=9)).isoformat()),
        (demo_user_id, cat_map.get('Other', 8), 100.0, 'Miscellaneous', (today - datetime.timedelta(days=10)).isoformat())
    ]
    
    cursor.executemany(
        "INSERT INTO expenses (user_id, category_id, amount, description, date) VALUES (?, ?, ?, ?, ?)",
        sample_expenses
    )
    
    conn.commit()
    conn.close()


def get_user_by_email(email):
    """Get a user by email address."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user


def create_user(name, email, password_hash):
    """Create a new user."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, password_hash)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id


def get_user_by_id(user_id):
    """Get a user by ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def get_expenses_by_user(user_id, start_date=None, end_date=None):
    """Get all expenses for a user, optionally filtered by date range."""
    conn = get_db()
    cursor = conn.cursor()
    
    query = """
        SELECT e.id, e.amount, e.description, e.date, e.created_at,
               c.name as category_name, c.icon as category_icon
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = ?
    """
    params = [user_id]
    
    if start_date:
        query += " AND e.date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND e.date <= ?"
        params.append(end_date)
    
    query += " ORDER BY e.date DESC, e.created_at DESC"
    
    cursor.execute(query, params)
    expenses = cursor.fetchall()
    conn.close()
    return expenses


def get_expense_by_id(expense_id, user_id):
    """Get a single expense by ID for a specific user."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id, e.amount, e.description, e.date, e.user_id, e.category_id,
               c.name as category_name, c.icon as category_icon
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.id = ? AND e.user_id = ?
    """, (expense_id, user_id))
    expense = cursor.fetchone()
    conn.close()
    return expense


def add_expense(user_id, category_id, amount, description, date):
    """Add a new expense."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO expenses (user_id, category_id, amount, description, date)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, category_id, amount, description, date))
    expense_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return expense_id


def update_expense(expense_id, user_id, category_id, amount, description, date):
    """Update an existing expense."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE expenses
        SET category_id = ?, amount = ?, description = ?, date = ?
        WHERE id = ? AND user_id = ?
    """, (category_id, amount, description, date, expense_id, user_id))
    conn.commit()
    conn.close()


def delete_expense(expense_id, user_id):
    """Delete an expense."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id))
    conn.commit()
    conn.close()


def get_categories():
    """Get all categories."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories ORDER BY name")
    categories = cursor.fetchall()
    conn.close()
    return categories


def get_expense_summary(user_id, start_date=None, end_date=None):
    """Get expense summary by category."""
    conn = get_db()
    cursor = conn.cursor()
    
    query = """
        SELECT c.name as category_name, c.icon as category_icon,
               SUM(e.amount) as total, COUNT(*) as count
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = ?
    """
    params = [user_id]
    
    if start_date:
        query += " AND e.date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND e.date <= ?"
        params.append(end_date)
    
    query += " GROUP BY c.id ORDER BY total DESC"
    
    cursor.execute(query, params)
    summary = cursor.fetchall()
    conn.close()
    return summary


def get_total_expenses(user_id, start_date=None, end_date=None):
    """Get total expenses for a user."""
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT SUM(amount) as total FROM expenses WHERE user_id = ?"
    params = [user_id]
    
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    
    cursor.execute(query, params)
    result = cursor.fetchone()
    conn.close()
    return result['total'] if result['total'] else 0
