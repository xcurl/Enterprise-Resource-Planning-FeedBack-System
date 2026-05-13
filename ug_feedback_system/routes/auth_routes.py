# Authentication Routes
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from services.auth_service import (
    authenticate_student, authenticate_admin, register_new_student,
    login_student, login_admin, logout_user, is_logged_in, is_admin, is_student
)
from services.branch_service import get_all_branches

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login')
def login_page():
    """Student login page"""
    if is_logged_in():
        if is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))
    return render_template('auth/login.html')


@auth_bp.route('/login', methods=['POST'])
def login():
    """Handle student login"""
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    
    if not email or not password:
        flash('Please enter both email and password', 'error')
        return redirect(url_for('auth.login_page'))
    
    result = authenticate_student(email, password)
    
    if result['success']:
        login_student(result['user'])
        flash(f'Welcome back, {result["user"]["student_name"]}!', 'success')
        return redirect(url_for('student.dashboard'))
    else:
        flash(result['message'], 'error')
        return redirect(url_for('auth.login_page'))


@auth_bp.route('/register')
def register_page():
    """Student registration page"""
    if is_logged_in():
        return redirect(url_for('student.dashboard'))
    branches = get_all_branches()
    return render_template('auth/register.html', branches=branches)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Handle student registration"""
    student_name = request.form.get('student_name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    usn = request.form.get('usn', '').strip().upper()
    branch_id = request.form.get('branch_id')
    year = request.form.get('year')
    semester = request.form.get('semester')
    
    # Validation
    if not all([student_name, email, password, usn, branch_id, year, semester]):
        flash('Please fill in all required fields', 'error')
        return redirect(url_for('auth.register_page'))
    
    if password != confirm_password:
        flash('Passwords do not match', 'error')
        return redirect(url_for('auth.register_page'))
    
    if len(password) < 6:
        flash('Password must be at least 6 characters', 'error')
        return redirect(url_for('auth.register_page'))
    
    # Validate year/semester mapping (1st year: sem 1-2, 2nd year: sem 3-4, etc.)
    year = int(year)
    semester = int(semester)
    expected_semesters = [(year * 2) - 1, year * 2]
    if semester not in expected_semesters:
        flash(f'Year {year} students should be in semester {expected_semesters[0]} or {expected_semesters[1]}', 'error')
        return redirect(url_for('auth.register_page'))
    
    # Get optional section
    section = request.form.get('section', '').strip() or None
    
    result = register_new_student(student_name, email, password, usn, branch_id, year, semester, section)
    
    if result['success']:
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login_page'))
    else:
        flash(result['message'], 'error')
        return redirect(url_for('auth.register_page'))


@auth_bp.route('/admin/login')
def admin_login_page():
    """Admin login page"""
    if is_logged_in() and is_admin():
        return redirect(url_for('admin.dashboard'))
    return render_template('auth/admin_login.html')


@auth_bp.route('/admin/login', methods=['POST'])
def admin_login():
    """Handle admin login"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    if not username or not password:
        flash('Please enter both username and password', 'error')
        return redirect(url_for('auth.admin_login_page'))
    
    result = authenticate_admin(username, password)
    
    if result['success']:
        login_admin(result['user'])
        flash(f'Welcome, {result["user"]["full_name"]}!', 'success')
        return redirect(url_for('admin.dashboard'))
    else:
        flash(result['message'], 'error')
        return redirect(url_for('auth.admin_login_page'))


@auth_bp.route('/logout')
def logout():
    """Handle logout for both students and admins"""
    user_type = session.get('user_type', 'student')
    logout_user()
    flash('You have been logged out successfully', 'info')
    
    if user_type == 'admin':
        return redirect(url_for('auth.admin_login_page'))
    return redirect(url_for('auth.login_page'))
