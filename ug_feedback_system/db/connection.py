import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(BASE_DIR, "..", "sql", "schema.sql")

# Track if database has been initialized this session
_db_initialized = False

def initialize_database():
    """Initialize database only if not already initialized"""
    global _db_initialized
    
    if _db_initialized:
        return True
    
    try:
        # 1️⃣ Connect WITHOUT database
        temp_config = DB_CONFIG.copy()
        db_name = temp_config.pop("database")

        conn = mysql.connector.connect(**temp_config)
        cursor = conn.cursor()

        # 2️⃣ Ensure database exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        cursor.execute(f"USE {db_name}")
        
        # 3️⃣ Check if tables already exist (check for admins table as indicator)
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = 'admins'
        """, (db_name,))
        tables_exist = cursor.fetchone()[0] > 0
        
        if not tables_exist:
            # 4️⃣ Execute schema.sql only if tables don't exist
            with open(SCHEMA_PATH, "r") as file:
                schema_sql = file.read()

            for result in cursor.execute(schema_sql, multi=True):
                pass  # required to exhaust generator

            conn.commit()
            print("✅ Database and tables initialized successfully")
        else:
            print("✅ Database already initialized, skipping schema execution")

        cursor.close()
        conn.close()
        
        _db_initialized = True
        return True

    except Error as e:
        print("❌ Database initialization failed:", e)
        return False


def get_db_connection():
    """Get a database connection, initializing if needed"""
    initialize_database()
    return mysql.connector.connect(**DB_CONFIG)
