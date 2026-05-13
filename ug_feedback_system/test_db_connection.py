from db.connection import get_db_connection

conn = get_db_connection()

if conn:
    print("✅ Database connection successful")
    conn.close()
else:
    print("❌ Database connection failed")
