import sqlite3
from sqlite3 import Cursor
from sqlite3 import Connection


class databaseManager:
    def __init__(self, db_path='historicalInventory.db'):
        self.db_path = db_path
        self.cursor: Cursor | None = None
        self.conn: Connection | None = None
        self.initialize_schema()

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

    def initialize_schema(self) -> None:
        self.connect()

        product_table = """
        CREATE TABLE IF NOT EXISTS product(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT UNIQUE NOT NULL,
            product_code TEXT UNIQUE NOT NULL,
            contifico_id TEXT UNIQUE,
            unit_type TEXT UNIQUE NOT NULL,
        )
        """

        records_table = """
        CREATE TABLE IF NOT EXISTS period_record(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            warehouse TEXT NOT NULL
        )
        """

        inventory_records = """
        CREATE TABLE IF NOT EXISTS inventory_records(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        period_record_id INTEGER NOT NULL,
        initial_stock DOUBLE NOT NULL,
        final_stock DOUBLE NOT NULL,
        FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE,
        FOREIGN KEY (period_record_id) REFERENCES period_records(id) ON DELETE CASCADE,
        UNIQUE (product_id, record_id)
        )
        """

        index = [
            "CREATE INDEX IF NOT EXISTS idx_product_code ON product(product_code)",
            "CREATE INDEX IF NOT EXISTS idx_period_dates ON period_record(start_date, end_date)",
            "CREATE INDEX IF NOT EXISTS idx_inventory_product ON inventory_records(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_inventory_record ON inventory_records(record_id)",
        ]

        self.cursor.execute(product_table)
        self.cursor.execute(records_table)
        self.cursor.execute(inventory_records)


        for idx in index:
            self.cursor.execute(idx)

        self.conn.commit()

    def upsert_product(self, product_name:str, product_code:str, unit_type:str, contifico_id=None):
        query = """
        INSERT INTO product (product_name, product_code, contifico_id, unite_type)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(product_code) DO UPDATE SET
        product_name = excluded.product_name,
        unit_type = excluded.unit_type,
        contifico_id = excluded.contifico_id
        """

        self.execute(query, params=(product_name, product_code, unit_type, contifico_id))

        return self.cursor.execute(
            "SELECT id FROM product WHERE product_code= ?",
            product_code
        )

    def insert_period_record(self, start_date, end_date, warehouse):
        #FUnction returns id for the period record created
        query = """
        INSERT INTO period_records (start_date, end_date, warehouse)
        VALUES(?,?,?)
        """
        self.execute(query, (start_date, end_date, warehouse))

        return self.cursor.execute(
            "SELECT id FROM period_records WHERE start_date = ? AND end_date = ? AND warehouse is ?",
            (start_date, end_date, warehouse)
        )

    def insert_inventory_record(self, product_id, period_id, initial_stock, final_stock):
        query = """
        INSERT INTO inventory_records 
        (product_id, period_id, initial_stock,  final_stock)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(product_id, period_id) DO UPDATE SET
            initial_stock = excluded.initial_stock,
            final_stock = excluded.final_stock,
            created_at = CURRENT_TIMESTAMP
        """
        self.execute(query, (product_id, period_id, initial_stock))

    def insert_report(self,start_date, end_date, warehouse, products_table):
        period_id = self.insert_period_record(start_date, end_date, warehouse)

        for product in products_table:
            product_id = self.upsert_product(
                product_code=product['product_code'],
                product_name=product['product_name'],
                unit_type=product['unit_type']
            )

            self.insert_inventory_record(
                product_id=product_id,
                period_id=period_id,
                initial_stock=product['initial_stock'],
                final_stock=product['final_stock']
            )