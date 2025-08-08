import sqlite3
from contextlib import closing

DB_NAME = "flights.db"

def init_db():
    """Tworzy (jeśli nie istnieje) tabelę flights w SQLite."""
    with closing(sqlite3.connect(DB_NAME)) as conn, conn, closing(conn.cursor()) as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS flights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                origin TEXT,
                destination TEXT,
                depart_date TEXT,
                return_date TEXT,
                depart_time TEXT,
                depart_airport TEXT,
                arrive_time TEXT,
                arrive_airport TEXT,
                price INTEGER,
                currency TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
    print("✅ Baza danych zainicjowana:", DB_NAME)

def save_flight(origin, destination, dep_date, ret_date,
                dep_time, dep_airport, arr_time, arr_airport,
                price, currency):
    """Zapisuje pojedynczy rekord lotu do bazy."""
    with closing(sqlite3.connect(DB_NAME)) as conn, conn, closing(conn.cursor()) as cur:
        cur.execute("""
            INSERT INTO flights
                (origin, destination, depart_date, return_date,
                 depart_time, depart_airport, arrive_time, arrive_airport,
                 price, currency)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            origin, destination, dep_date, ret_date,
            dep_time, dep_airport, arr_time, arr_airport,
            price, currency
        ))
    # nie drukujemy nic tu, bo będzie dużo rekordów
