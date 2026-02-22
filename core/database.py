import sqlite3
from contextlib import closing
from pathlib import Path
import pandas as pd

from config.settings import DB_FILE


class DatabaseManager:
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def table_exists(self, table_name: str) -> bool:
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        with sqlite3.connect(self.db_path) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute(query, (table_name,))
                return cur.fetchone() is not None

    def save_dataframe(self, table_name: str, df: pd.DataFrame):
        if df is None:
            return
        with sqlite3.connect(self.db_path) as conn:
            df.to_sql(table_name, conn, if_exists="replace", index=False)

    def load_dataframe(self, table_name: str) -> pd.DataFrame:
        if not self.table_exists(table_name):
            return pd.DataFrame()
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)

