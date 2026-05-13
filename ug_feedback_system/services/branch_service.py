# Branch Service - Handles branch-related operations
from db.connection import get_db_connection


def get_all_branches():
    """Get all branches"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT * FROM branches ORDER BY branch_name
            """
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_branch_by_id(branch_id):
    """Get a branch by ID"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT * FROM branches WHERE branch_id = %s
            """,
            (branch_id,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def create_branch(branch_code, branch_name, department=None):
    """Create a new branch"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            INSERT INTO branches (branch_code, branch_name, department)
            VALUES (%s, %s, %s)
            """,
            (branch_code.upper(), branch_name, department)
        )
        conn.commit()
        return {"success": True, "message": "Branch created successfully"}
    except Exception as e:
        conn.rollback()
        if "Duplicate entry" in str(e):
            return {"success": False, "message": "Branch code already exists"}
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()
