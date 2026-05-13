# Business logic for courses
from db.connection import get_db_connection


def create_course(course_name, course_code=None, department=None, semester=1, credits=3):
    """Create a new course"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO courses (course_name, course_code, department, semester, credits)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (course_name, course_code, department, semester, credits)
        )
        conn.commit()
        return {"success": True, "course_id": cursor.lastrowid}
    except Exception as e:
        conn.rollback()
        if "Duplicate entry" in str(e):
            return {"success": False, "message": "Course code already exists"}
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def list_all_courses():
    """Get all courses with CO count"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT c.*, COUNT(co.co_id) as co_count 
        FROM courses c
        LEFT JOIN course_outcomes co ON c.course_id = co.course_id
        GROUP BY c.course_id
        ORDER BY c.semester, c.course_code
    """)
    courses = cursor.fetchall()

    cursor.close()
    conn.close()
    return courses


def get_all_courses_with_outcomes():
    """Get all courses with their course outcomes"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get courses
        cursor.execute("""
            SELECT c.*, COUNT(co.co_id) as co_count 
            FROM courses c
            LEFT JOIN course_outcomes co ON c.course_id = co.course_id
            GROUP BY c.course_id
            ORDER BY c.semester, c.course_code
        """)
        courses = cursor.fetchall()
        
        # Get outcomes for each course
        for course in courses:
            cursor.execute(
                "SELECT * FROM course_outcomes WHERE course_id = %s ORDER BY co_number",
                (course['course_id'],)
            )
            course['outcomes'] = cursor.fetchall()
        
        return courses
    finally:
        cursor.close()
        conn.close()


def get_courses_by_semester(semester):
    """Get courses for a specific semester"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            "SELECT * FROM courses WHERE semester = %s ORDER BY course_code",
            (semester,)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_course_by_id(course_id):
    """Get course by ID"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM courses WHERE course_id = %s", (course_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_courses_with_outcomes():
    """Get courses that have course outcomes defined"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT DISTINCT c.* FROM courses c
            JOIN course_outcomes co ON c.course_id = co.course_id
            ORDER BY c.course_name
            """
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def add_course_outcome(course_id, co_number, co_description, bloom_level=None):
    """Add a course outcome to a course"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            INSERT INTO course_outcomes (course_id, co_number, co_description, bloom_level)
            VALUES (%s, %s, %s, %s)
            """,
            (course_id, co_number, co_description, bloom_level)
        )
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        if "Duplicate entry" in str(e):
            return {"success": False, "message": "Course outcome number already exists for this course"}
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def get_course_outcomes(course_id):
    """Get all course outcomes for a course"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT * FROM course_outcomes WHERE course_id = %s ORDER BY co_number
            """,
            (course_id,)
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def delete_course_outcome(co_id):
    """Delete a course outcome"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM course_outcomes WHERE co_id = %s", (co_id,))
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()
