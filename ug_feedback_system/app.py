from flask import Flask, render_template, redirect, url_for, jsonify
from config import SECRET_KEY, SESSION_LIFETIME, DEBUG, HOST, PORT

from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.student_routes import student_bp
from routes.course_routes import course_bp
from routes.faculty_routes import faculty_bp
from routes.feedback_routes import feedback_bp

from services.auth_service import get_current_user, is_logged_in, is_admin, is_student
from services.admin_service import auto_activate_scheduled_periods


def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.permanent_session_lifetime = SESSION_LIFETIME
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(course_bp)
    app.register_blueprint(faculty_bp)
    app.register_blueprint(feedback_bp)

    # Auto-activate scheduled feedback periods before every request
    @app.before_request
    def auto_activate_periods():
        """Automatically activate/deactivate periods based on schedule"""
        try:
            auto_activate_scheduled_periods()
        except Exception as e:
            # Log error but don't break the app
            print(f"Error in auto-activation: {e}")

    # Context processor to make user info available in all templates
    @app.context_processor
    def inject_user():
        return {
            'current_user': get_current_user(),
            'is_logged_in': is_logged_in(),
            'is_admin': is_admin(),
            'is_student': is_student()
        }

    @app.route("/")
    def home():
        """Home page - redirect based on login status"""
        if is_logged_in():
            if is_admin():
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('student.dashboard'))
        return render_template("landing.html")

    @app.route("/health")
    def health():
        """Health endpoint for deployment checks."""
        return jsonify({"status": "ok"}), 200

    # Legacy routes for backward compatibility - redirect to proper pages
    @app.route("/register-student")
    def register_student_page():
        return redirect(url_for('auth.register_page'))

    @app.route("/add-course")
    def add_course_page():
        if not is_admin():
            return redirect(url_for('auth.admin_login_page'))
        return redirect(url_for('admin.courses'))

    @app.route("/add-faculty")
    def add_faculty_page():
        if not is_admin():
            return redirect(url_for('auth.admin_login_page'))
        return redirect(url_for('admin.faculty'))

    @app.route("/submit-feedback")
    def submit_feedback_page():
        if not is_logged_in():
            return redirect(url_for('auth.login_page'))
        if is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.faculty_feedback'))

    @app.route("/view-feedback")
    def view_feedback_page():
        if not is_admin():
            return redirect(url_for('auth.admin_login_page'))
        return redirect(url_for('admin.reports'))

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('errors/500.html'), 500

    return app


if __name__ == "__main__":
    create_app().run(host=HOST, port=PORT, debug=DEBUG)
