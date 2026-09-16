import os
import sqlite3
import threading
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional

DEFAULT_SQLITE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "thpay.db"
)

_thread_local = threading.local()

class DatabaseConnection:
    """
    Abstracao de conexao transacional para o ThPay.
    Suporta SQLite embutido com WAL e chaves estrangeiras ativadas,
    alem de PostgreSQL via DATABASE_URL quando configurado.
    """
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.environ.get("DATABASE_PATH", DEFAULT_SQLITE_PATH)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.database_url = os.environ.get("DATABASE_URL")
        self.is_postgres = bool(self.database_url and ("postgres" in self.database_url))

    def get_connection(self):
        if self.is_postgres:
            import pg8000.native
            # Conexao PostgreSQL via pg8000 nativo
            # Parse simples ou conexao direta via URL
            import urllib.parse
            result = urllib.parse.urlparse(self.database_url)
            conn = pg8000.native.Connection(
                user=result.username or "postgres",
                password=result.password or "",
                host=result.hostname or "localhost",
                port=result.port or 5432,
                database=result.path.lstrip("/") or "thpay"
            )
            return conn
        else:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA journal_mode = WAL;")
            return conn

class DBContext:
    def __init__(self, conn, is_postgres: bool = False):
        self.conn = conn
        self.is_postgres = is_postgres

    def execute(self, sql: str, params: Optional[Any] = None) -> Any:
        if self.is_postgres:
            # Converter placeholders ? para :1, :2 etc ou executar com pg8000
            # Para testes locais usamos SQLite
            return self.conn.run(sql, **(params or {}))
        else:
            cursor = self.conn.cursor()
            if params is not None:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor

    def fetchall(self, sql: str, params: Optional[Any] = None) -> List[Dict[str, Any]]:
        cursor = self.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def fetchone(self, sql: str, params: Optional[Any] = None) -> Optional[Dict[str, Any]]:
        cursor = self.execute(sql, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

_db_instance: Optional[DatabaseConnection] = None

def get_db_instance(db_path: Optional[str] = None) -> DatabaseConnection:
    global _db_instance
    if _db_instance is None or db_path is not None:
        _db_instance = DatabaseConnection(db_path)
    return _db_instance

@contextmanager
def get_db(db_path: Optional[str] = None) -> Generator[DBContext, None, None]:
    instance = get_db_instance(db_path)
    conn = instance.get_connection()
    ctx = DBContext(conn, is_postgres=instance.is_postgres)
    try:
        yield ctx
        ctx.commit()
    except Exception:
        ctx.rollback()
        raise
    finally:
        conn.close()
