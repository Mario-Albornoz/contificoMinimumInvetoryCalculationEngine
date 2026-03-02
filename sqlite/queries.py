get_records_for_data_frame_query = """SELECT
                                    p.contifico_id as product_id,
                                    w.name as warehouse_name,
                                    w.contifico_id as warehouse_contifico_id,
                                    ir.initial_stock as initial_stock,
                                    ir.final_stock as final_stock,
                                    pr.start_date as start_date,
                                FROM  inventory_records ir,
                                INNER JOIN product p ON ir.product_id = p.id
                                INNER JOIN period_record pr ON ir.period_record_id = pr.id 
                                INNER JOIN warehouse w ON ir.warehouse_id = w.id"""

insert_inventory_records_query  = """
                                    INSERT INTO inventory_records 
                                    (product_id, period_record_id, initial_stock,  final_stock)
                                    VALUES (?, ?, ?, ?)
                                    ON CONFLICT(product_id, period_record_id) DO UPDATE SET
                                        initial_stock = excluded.initial_stock,
                                        final_stock = excluded.final_stock
                                    """
 
upsert_warehouse_query =  """
        INSERT INTO warehouse (name, contifico_id, code)
        VALUES(?,?,?)
        ON CONFLICT(code) DO UPDATE SET
        name = excluded.name,
        contifico_id = excluded.contifico_id,
        code = excluded.code
        """

product_table_schema_query = """
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
warehouse_table_schema_query = """
        CREATE TABLE IF NOT EXISTS warehouse(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name STRING NOT NULL,
            contifico_id STRING,
            code STRING UNIQUE NOT NULL,
            internal_contifico_id INTEGER UNIQUE
        )
        """

records_table_schema_query = """
        CREATE TABLE IF NOT EXISTS period_record(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            warehouse_id INTEGER NOT NULL,
            FOREIGN KEY (warehouse_id) REFERENCES warehouse(id) ON DELETE CASCADE
        )
        """

inventory_records_table_schema_query = """
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

