import os
import sqlite3
from contextlib import contextmanager


@contextmanager
def db():
    connection = sqlite3.connect(os.getenv('DATABASE_PATH', 'septimatica.sqlite3'), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.executescript('''
    CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, email TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, user_id TEXT, expires REAL);
    CREATE TABLE IF NOT EXISTS graphs (id TEXT PRIMARY KEY, owner TEXT, name TEXT, data TEXT);
    CREATE TABLE IF NOT EXISTS grants (owner TEXT, fingerprint TEXT, topic TEXT, PRIMARY KEY(owner,fingerprint,topic));
    CREATE TABLE IF NOT EXISTS submissions (id TEXT PRIMARY KEY, owner TEXT, fingerprint TEXT, topic TEXT, proof TEXT, status TEXT);
    CREATE TABLE IF NOT EXISTS policy (id INTEGER PRIMARY KEY CHECK(id=1), data TEXT);
    ''')
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
