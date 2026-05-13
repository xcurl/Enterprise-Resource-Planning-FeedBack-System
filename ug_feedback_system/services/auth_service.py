# Authentication Service - Handles user login, registration, password hashing
import bcrypt
from functools import wraps
from flask import session, redirect, url_for, flash, request
from db.connection import get_db_connection
from config import BCRYPT_ROUNDS


def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(BCRYPT_ROUNDS)).decode('utf-8')


def verify_password(password, password_hash):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


# ==================== STUDENT AUTHENTICATION ====================

def register_new_student(student_name, email, password, usn, branch_id, year, semester, section=None):
    """Register a new student with hashed password"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(password)
        cursor.execute(
            """
            INSERT INTO students (student_name, email, password_hash, usn, branch_id, year, semester, section)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (student_name, email, password_hash, usn, branch_id, year, semester, section)
        )
        conn.commit()
        return {"success": True, "message": "Student registered successfully"}
    except Exception as e:
        conn.rollback()
        if "Duplicate entry" in str(e):
            if "email" in str(e):
                return {"success": False, "message": "Email already registered"}
            elif "usn" in str(e):
                return {"success": False, "message": "USN already registered"}
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def authenticate_student(email, password):
    """Authenticate a student by email and password"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT s.*, b.branch_name, b.branch_code 
            FROM students s
            LEFT JOIN branches b ON s.branch_id = b.branch_id
            WHERE s.email = %s
            """,
            (email,)
        )
        student = cursor.fetchone()
        
        if student and verify_password(password, student['password_hash']):
            # Remove sensitive data before returning
            del student['password_hash']
            return {"success": True, "user": student}
        return {"success": False, "message": "Invalid email or password"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def get_student_by_id(student_id):
    """Get student details by ID"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT s.student_id, s.student_name, s.email, s.usn, s.branch_id, 
                   s.year, s.semester, s.is_eligible, b.branch_name, b.branch_code
            FROM students s
            LEFT JOIN branches b ON s.branch_id = b.branch_id
            WHERE s.student_id = %s
            """,
            (student_id,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


# ==================== ADMIN AUTHENTICATION ====================

def authenticate_admin(username, password):
    """Authenticate an admin by username and password"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT * FROM admins WHERE username = %s AND is_active = TRUE
            """,
            (username,)
        )
        admin = cursor.fetchone()
        
        if admin and verify_password(password, admin['password_hash']):
            del admin['password_hash']
            return {"success": True, "user": admin}
        return {"success": False, "message": "Invalid username or password"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def create_admin(username, email, password, full_name, role='admin', created_by=None):
    """Create a new admin user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(password)
        cursor.execute(
            """
            INSERT INTO admins (username, email, password_hash, full_name, role)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (username, email, password_hash, full_name, role)
        )
        conn.commit()
        return {"success": True, "message": "Admin created successfully"}
    except Exception as e:
        conn.rollback()
        if "Duplicate entry" in str(e):
            return {"success": False, "message": "Username or email already exists"}
        return {"success": False, "message": str(e)}
    finally:
        cursor.close()
        conn.close()


def get_admin_by_id(admin_id):
    """Get admin details by ID"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute(
            """
            SELECT admin_id, username, email, full_name, role, is_active, created_at
            FROM admins WHERE admin_id = %s
            """,
            (admin_id,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


# ==================== SESSION MANAGEMENT ====================

def login_student(student):
    """Create session for student"""
    session.clear()
    session['user_id'] = student['student_id']
    session['user_type'] = 'student'
    session['user_name'] = student['student_name']
    session['user_email'] = student['email']
    session['usn'] = student['usn']
    session['branch_id'] = student['branch_id']
    session['branch_name'] = student.get('branch_name', '')
    session['semester'] = student.get('semester', 1)
    session['is_eligible'] = student['is_eligible']
    session.permanent = True


def login_admin(admin):
    """Create session for admin"""
    session.clear()
    session['user_id'] = admin['admin_id']
    session['user_type'] = 'admin'
    session['user_name'] = admin['full_name']
    session['user_email'] = admin['email']
    session['admin_role'] = admin['role']
    session.permanent = True


def logout_user():
    """Clear user session"""
    session.clear()


def get_current_user():
    """Get current logged in user info from session"""
    if 'user_id' not in session:
        return None
    return {
        'user_id': session.get('user_id'),
        'user_type': session.get('user_type'),
        'user_name': session.get('user_name'),
        'user_email': session.get('user_email'),
        'admin_role': session.get('admin_role'),
        'usn': session.get('usn'),
        'branch_id': session.get('branch_id'),
        'branch_name': session.get('branch_name'),
        'semester': session.get('semester'),
        'is_eligible': session.get('is_eligible')
    }


def is_logged_in():
    """Check if user is logged in"""
    return 'user_id' in session


def is_admin():
    """Check if current user is admin"""
    return session.get('user_type') == 'admin'


def is_student():
    """Check if current user is student"""
    return session.get('user_type') == 'student'


# ==================== ROUTE DECORATORS ====================

def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated_function


def student_required(f):
    """Decorator to require student login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth.login_page'))
        if not is_student():
            flash('This page is only accessible to students', 'error')
            return redirect(url_for('home'))
        if session.get('is_eligible') is False and request.endpoint != 'student.dashboard':
            flash('Your student access is currently disabled. Please contact the administrator.', 'error')
            return redirect(url_for('student.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth.admin_login_page'))
        if not is_admin():
            flash('This page is only accessible to administrators', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


def eligible_student_required(f):
    """Decorator to require eligible student for feedback"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth.login_page'))
        if not is_student():
            flash('This page is only accessible to students', 'error')
            return redirect(url_for('home'))
        if not session.get('is_eligible', False):
            flash('You are not eligible to submit feedback. Please contact administrator.', 'error')
            return redirect(url_for('student.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== AUDIT LOGGING ====================

def log_admin_action(admin_id, action, entity_type=None, entity_id=None, old_value=None, new_value=None):
    """Log admin actions for audit trail"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        ip_address = request.remote_addr if request else None
        cursor.execute(
            """
            INSERT INTO audit_log (admin_id, action, entity_type, entity_id, old_value, new_value, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (admin_id, action, entity_type, entity_id, old_value, new_value, ip_address)
        )
        conn.commit()
    except Exception as e:
        print(f"Failed to log action: {e}")
    finally:
        cursor.close()
        conn.close()
