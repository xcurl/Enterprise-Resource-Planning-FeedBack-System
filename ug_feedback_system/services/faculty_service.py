# Business logic for faculty
from db.connection import get_db_connection


def add_faculty(faculty_name, email=None, department=None, designation=None):
    """Add a new faculty member"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO faculty (faculty_name, email, department, designation)
            VALUES (%s, %s, %s, %s)
            """,
            (faculty_name, email, department, designation)
        )
        conn.commit()
        return {"success": True, "faculty_id": cursor.lastrowid}
    except Exception as e:
        conn.rollback()
        if "Duplicate entry" in str(e):
            return {"success": False, "message": "Email already exists"}
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def assign_faculty_to_course(faculty_name, course_id):
    """Legacy function - Add faculty and assign to a course"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO faculty (faculty_name, course_id)
        VALUES (%s, %s)
        """,
        (faculty_name, course_id)
    )

    conn.commit()
    cursor.close()
    conn.close()


def get_faculty_by_course(course_id):
    """Get faculty assigned to a course"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT f.* FROM faculty f
        JOIN faculty_course_assignments fca ON f.faculty_id = fca.faculty_id
        WHERE fca.course_id = %s AND fca.is_active = TRUE AND f.is_active = TRUE
        """,
        (course_id,)
    )

    faculty = cursor.fetchall()
    cursor.close()
    conn.close()
    return faculty


def get_all_faculty():
    """Get all active faculty"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM faculty WHERE is_active = TRUE ORDER BY faculty_name")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def get_faculty_by_id(faculty_id):
    """Get faculty by ID"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM faculty WHERE faculty_id = %s", (faculty_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_faculty_performance_report(faculty_id):
    """Get detailed performance report for a faculty member"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get overall stats
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_feedbacks,
                ROUND(AVG(teaching_quality), 2) as avg_teaching,
                ROUND(AVG(communication), 2) as avg_communication,
                ROUND(AVG(punctuality), 2) as avg_punctuality,
                ROUND(AVG(subject_knowledge), 2) as avg_knowledge,
                ROUND(AVG(helping_nature), 2) as avg_helping,
                ROUND(AVG(overall_rating), 2) as avg_overall
            FROM faculty_feedback
            WHERE faculty_id = %s
            """,
            (faculty_id,)
        )
        overall = cursor.fetchone()
        
        # Get by course
        cursor.execute(
            """
            SELECT 
                c.course_name, c.course_code,
                COUNT(*) as feedback_count,
                ROUND(AVG(ff.overall_rating), 2) as avg_rating
            FROM faculty_feedback ff
            JOIN courses c ON ff.course_id = c.course_id
            WHERE ff.faculty_id = %s
            GROUP BY ff.course_id
            ORDER BY avg_rating DESC
            """,
            (faculty_id,)
        )
        by_course = cursor.fetchall()
        
        # Get recent comments (anonymous)
        cursor.execute(
            """
            SELECT comments, overall_rating, submitted_at
            FROM faculty_feedback
            WHERE faculty_id = %s AND comments IS NOT NULL AND comments != ''
            ORDER BY submitted_at DESC
            LIMIT 10
            """,
            (faculty_id,)
        )
        comments = cursor.fetchall()
        
        return {
            'overall': overall,
            'by_course': by_course,
            'recent_comments': comments
        }
    finally:
        cursor.close()
        conn.close()
