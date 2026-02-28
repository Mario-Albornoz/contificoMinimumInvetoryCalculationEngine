import sqlite3
from sqlite3 import Cursor
from sqlite3 import Connection

from scripts.dataGathering import gather_warehouse_data_from_api

#TODO: create property to assert slef.conn and self.cursor are not None
class databaseManager:
    def __init__(self, db_path='historicalInventory.db', build_schema:bool=True):
        self.db_path = db_path
        self.conn: Connection =  sqlite3.connect(self.db_path)        
        self.cursor: Cursor = self.conn.cursor()
        self.build_schema:bool=build_schema
        if self.build_schema:
            self.initialize_schema()

    def connect(self) -> tuple[Cursor | None, Connection]:
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
        return self.cursor, self.conn

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()

    def execute(self, query, params = ()):
        self.connect()
        assert self.cursor is not None
        self.cursor.execute(query, params) 
        assert self.conn is not None
        self.conn.commit() 
        return self.cursor

    def initialize_schema(self) -> None:
        self.connect()
        assert self.cursor and self.conn is not None

        product_table = """
        CREATE TABLE IF NOT EXISTS product(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            product_code TEXT UNIQUE NOT NULL,
            contifico_id TEXT UNIQUE,
            unit_type TEXT NOT NULL
        )
        """

        """id: internal primary key
        name:name of warehouse
        contifico_id: id from contifico_api
        code: code from contifico_api
        internal_contifico_id: id used for retrivin excel report (saldos disponibles)
        """

        warehouse_table = """
        CREATE TABLE IF NOT EXISTS warehouse(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name STRING NOT NULL,
            contifico_id STRING,
            code STRING UNIQUE NOT NULL,
            internal_contifico_id INTEGER UNIQUE
        )
        """

        records_table = """
        CREATE TABLE IF NOT EXISTS period_record(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            warehouse_id INTEGER NOT NULL,
            FOREIGN KEY (warehouse_id) REFERENCES warehouse(id) ON DELETE CASCADE
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
        FOREIGN KEY (period_record_id) REFERENCES period_record(id) ON DELETE CASCADE,
        UNIQUE (product_id, period_record_id)
        )
        """

        index = [
            "CREATE INDEX IF NOT EXISTS idx_product_code ON product(product_code)",
            "CREATE INDEX IF NOT EXISTS idx_period_dates ON period_record(start_date, end_date)",
            "CREATE INDEX IF NOT EXISTS idx_inventory_product ON inventory_records(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_inventory_record ON inventory_records(period_record_id)",
        ]

        assert self.cursor is not None
        self.cursor.execute(product_table)
        self.cursor.execute(warehouse_table)
        self.cursor.execute(records_table)
        self.cursor.execute(inventory_records)


        for idx in index:
            self.cursor.execute(idx)

        assert self.conn is not None
        self.conn.commit()
        print("Database Schema intilized")

    def upsert_product(self, product_name:str, product_code:str, unit_type:str, contifico_id=None):
        query = """
        INSERT INTO product (product_name, product_code, unit_type, contifico_id)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(product_code) DO UPDATE SET
        product_name = excluded.product_name,
        unit_type = excluded.unit_type,
        contifico_id = excluded.contifico_id
        """

        try:
            self.execute(query, params=(product_name, product_code, unit_type, contifico_id))
        except sqlite3.IntegrityError as e:
            print(f"IntegrityError: {e}")
            print(f"  Incoming -> name: {product_name}, code: {product_code}")
            existing = self.cursor.execute(
                "SELECT * FROM product WHERE product_code = ? OR product_name = ?",
                (product_code, product_name)
            ).fetchall()
            print(f"  Conflicting rows in DB: {existing}")
            raise


        result = self.cursor.execute(
            "SELECT id FROM product WHERE product_code = ?",
            (product_code,)
        ).fetchone()

        return result[0] if result else None

    def upsert_warehouse(self, warehouse_name:str, warehouse_code:str, warehouse_contifico_id:str):
        #Returns the id of the created warehouse
        query = """
        INSERT INTO warehouse (name, contifico_id, code)
        VALUES(?,?,?)
        ON CONFLICT(code) DO UPDATE SET
        name = excluded.name,
        contifico_id = excluded.contifico_id,
        code = excluded.code
        """
        self.execute(query, params=(warehouse_name, warehouse_contifico_id, warehouse_code))

        result = self.cursor.execute(
            "SELECT id FROM warehouse WHERE code = ?",
            (warehouse_code,)
        ).fetchone()

        return result[0] if result else None

    def getStoreWarehouse(self):
        warehouses = []
        query = """
        SELECT * FROM warehouse
        WHERE name in ("Bodega Village", "Bodega Riocentro Ceibos", "Bodega Mall del Sol")
        """
        self.cursor.execute(query)
        columns = [col[0] for col in self.cursor.description]
        for row in self.cursor.fetchall():
            warehouses.append(dict(zip(columns, row)))

        return warehouses

    def insert_period_record(self, start_date, end_date, warehouse_id):
        #FUnction returns id for the period record created
        query = """
        INSERT INTO period_record (start_date, end_date, warehouse_id)
        VALUES(?,?,?)
        """
        self.execute(query, (start_date, end_date, warehouse_id))

        result = self.cursor.execute(
            "SELECT id FROM period_record WHERE start_date = ? AND end_date = ? AND warehouse_id = ?",
            (start_date, end_date, warehouse_id)
        ).fetchone()

        return result[0] if result else None

    def insert_inventory_record(self, product_id, period_id, initial_stock, final_stock):
        query = """
        INSERT INTO inventory_records 
        (product_id, period_record_id, initial_stock,  final_stock)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(product_id, period_record_id) DO UPDATE SET
            initial_stock = excluded.initial_stock,
            final_stock = excluded.final_stock
        """
        self.execute(query, (product_id, period_id, initial_stock, final_stock))

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
    def populate_warehouse_tables(self):
        warehouse_data = gather_warehouse_data_from_api()
        for warehouse in warehouse_data:
            self.upsert_warehouse(warehouse['nombre'],  warehouse['codigo'], warehouse['contifico_id'])
        self.execute("""
        UPDATE warehouse
        SET internal_contifico_id = 64035
        WHERE name = 'Bodega Village'
        """)
        self.execute("""
                UPDATE warehouse
                SET internal_contifico_id = 64730
                WHERE name = 'Bodega Riocentro Ceibos'
                """)
        self.execute("""
            UPDATE warehouse
            SET internal_contifico_id = 87729
            WHERE name = 'Bodega Mall del Sol'
            """)
        self.close()
    
    
