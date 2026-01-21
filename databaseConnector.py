import sqlite3
from sqlite3 import Cursor
from sqlite3 import Connection


class databaseManager:
    def __init__(self, db_path='historicalInventory.db'):
        self.db_path = db_path
        self.cursor: Cursor | None = None
        self.conn: Connection | None = None

    def connect(self) -> tuple[Cursor, Connection]:
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
        return self.cursor, self.conn

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def execute(self, query, params = ()):
        self.connect()
        self.cursor.execute(query, params)
        self.conn.commit()
        return self.cursor



