import sqlite3
from typing import Tuple, List, Optional
from config import DB_NAME


def init_db():
    """Ініціалізує базу даних та створює необхідні таблиці."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Таблиця користувачів
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            city TEXT,
            notify_time TEXT,
            notify_days TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()


def get_user_settings(user_id: int) -> Tuple[Optional[str], Optional[str]]:
    """Отримує налаштування користувача."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('SELECT city, notify_time FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    
    conn.close()
    return result if result else (None, None)


def get_user_notify_days(user_id: int) -> List[int]:
    """Отримує дні сповіщень користувача."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('SELECT notify_days FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    
    conn.close()
    if result and result[0]:
        return [int(d) for d in result[0].split(',')]
    return []


def set_city(user_id: int, city: str):
    """Встановлює місто для користувача."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO users (user_id, city)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET city = ?
    ''', (user_id, city, city))
    
    conn.commit()
    conn.close()


def set_notify_time(user_id: int, time: str):
    """Встановлює час сповіщень для користувача."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO users (user_id, notify_time)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET notify_time = ?
    ''', (user_id, time, time))
    
    conn.commit()
    conn.close()


def set_notify_days(user_id: int, days: List[int]):
    """Встановлює дні сповіщень для користувача."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    days_str = ','.join(map(str, sorted(days)))
    c.execute('''
        INSERT INTO users (user_id, notify_days)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET notify_days = ?
    ''', (user_id, days_str, days_str))
    
    conn.commit()
    conn.close()


def get_all_users() -> List[Tuple[int, str, str, str]]:
    """Отримує список всіх користувачів з їх налаштуваннями."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('SELECT user_id, city, notify_time, notify_days FROM users')
    users = c.fetchall()
    
    conn.close()
    return users


def delete_user(user_id: int):
    """Видаляє користувача з бази даних."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    
    conn.commit()
    conn.close()


# Ініціалізуємо базу даних при імпорті модуля
init_db()
