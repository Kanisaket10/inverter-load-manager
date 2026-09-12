import sqlites3

DATABASE = "inverter.db"

def get_connection():
    conn = sqlite3.connec(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appliances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            wattage INTEGER NOT NULL,
            priority INTEGER NOT NULL,
            state TEXT NOT NULL DEFAULT 'OFF',
            desired_on INTEGER NOT NULL DEFAULT 0,
            shed_order INTEGER
        )
    """)
    conn.commit()
    conn.close()    