from flask import Blueprint, request, redirect
from services.feedback_service import submit_student_feedback

feedback_bp = Blueprint("feedback", __name__)

@feedback_bp.route("/feedback/submit", methods=["POST"])
def submit_feedback_route():
    submit_student_feedback(
        request.form["student_id"],
        request.form["faculty_id"],
        request.form["rating"],
        request.form["comments"]
    )
    return redirect("/")
