import pathlib

import lancedb
import pyarrow as pa
import os
#Подключение к базе

def create_lancedb():
    db_path = os.path.abspath(__file__) / ".lancedb"
    if db_path.exists():
        return
    table_name = "clear_embeddings"
    print("[*] Creating LanceDB...")
    #path = pathlib.Path(__file__).parent.parent.parent / ".lancedb"
    db = lancedb.connect(db_path)

    # Схема таблицы
    schema = pa.schema([
        pa.field("binary_name", pa.string()),
        pa.field("instruction_mode", pa.string()),
        pa.field("function_name", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), 100))
    ])

    table = db.create_table(str(table_name), schema=schema, exist_ok=True)
