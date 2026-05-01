from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = "change_this_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "static/uploads"

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="student")


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)


class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    video_url = db.Column(db.String(300), nullable=True)
    pdf_file = db.Column(db.String(300), nullable=True)

    course = db.relationship("Course", backref=db.backref("lessons", lazy=True))


class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    question = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_answer = db.Column(db.String(10), nullable=False)

    course = db.relationship("Course", backref=db.backref("quizzes", lazy=True))


class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    score = db.Column(db.Integer, nullable=False)

    user = db.relationship("User", backref=db.backref("results", lazy=True))
    course = db.relationship("Course", backref=db.backref("results", lazy=True))


class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)

    user = db.relationship("User", backref=db.backref("enrollments", lazy=True))
    course = db.relationship("Course", backref=db.backref("enrollments", lazy=True))


class LessonProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lesson.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)

    user = db.relationship("User", backref=db.backref("lesson_progress", lazy=True))
    lesson = db.relationship("Lesson", backref=db.backref("lesson_progress", lazy=True))
    course = db.relationship("Course", backref=db.backref("lesson_progress", lazy=True))


def login_required():
    return "user_id" in session


def admin_required():
    return session.get("role") == "admin"


@app.route("/")
def index():
    courses = Course.query.all()
    return render_template("index.html", courses=courses)


@app.route("/register", methods=["GET", "POST"])
def register():
    if not login_required():
        flash("Please login first")
        return redirect(url_for("login"))

    if not admin_required():
        flash("Only admin can create accounts")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already exists")
            return redirect(url_for("register"))

        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully")
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["role"] = user.role
            return redirect(url_for("dashboard"))

        flash("Invalid email or password")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))

    results = Result.query.filter_by(user_id=session["user_id"]).all()

    if session.get("role") == "admin":
        courses = Course.query.all()
        return render_template("admin_dashboard.html", courses=courses, results=results)

    enrollments = Enrollment.query.filter_by(user_id=session["user_id"]).all()
    courses = [enrollment.course for enrollment in enrollments]

    return render_template("dashboard.html", courses=courses, results=results)


@app.route("/profile")
def profile():
    if not login_required():
        return redirect(url_for("login"))

    user = User.query.get_or_404(session["user_id"])
    results = Result.query.filter_by(user_id=user.id).all()

    return render_template("profile.html", user=user, results=results)


@app.route("/profile/edit", methods=["GET", "POST"])
def edit_profile():
    if not login_required():
        return redirect(url_for("login"))

    user = User.query.get_or_404(session["user_id"])

    if request.method == "POST":
        name = request.form["name"]
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if not check_password_hash(user.password, current_password):
            flash("Current password is incorrect")
            return redirect(url_for("edit_profile"))

        user.name = name

        if new_password:
            if new_password != confirm_password:
                flash("New passwords do not match")
                return redirect(url_for("edit_profile"))

            user.password = generate_password_hash(new_password)

        db.session.commit()

        session["user_name"] = user.name

        flash("Profile updated successfully")
        return redirect(url_for("profile"))

    return render_template("edit_profile.html", user=user)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/add-course", methods=["GET", "POST"])
def add_course():
    if not login_required():
        return redirect(url_for("login"))

    if not admin_required():
        flash("Only admin can add courses")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        course = Course(
            title=request.form["title"],
            description=request.form["description"],
            category=request.form["category"]
        )

        db.session.add(course)
        db.session.commit()

        flash("Course added successfully")
        return redirect(url_for("dashboard"))

    return render_template("add_course.html")


@app.route("/course/<int:course_id>/edit", methods=["GET", "POST"])
def edit_course(course_id):
    if not login_required():
        return redirect(url_for("login"))

    if not admin_required():
        flash("Only admin can edit courses")
        return redirect(url_for("dashboard"))

    course = Course.query.get_or_404(course_id)

    if request.method == "POST":
        course.title = request.form["title"]
        course.description = request.form["description"]
        course.category = request.form["category"]

        db.session.commit()

        flash("Course updated successfully")
        return redirect(url_for("dashboard"))

    return render_template("edit_course.html", course=course)


@app.route("/course/<int:course_id>/delete", methods=["POST"])
def delete_course(course_id):
    if not login_required():
        return redirect(url_for("login"))

    if not admin_required():
        flash("Only admin can delete courses")
        return redirect(url_for("dashboard"))

    course = Course.query.get_or_404(course_id)

    Lesson.query.filter_by(course_id=course.id).delete()
    Quiz.query.filter_by(course_id=course.id).delete()
    Result.query.filter_by(course_id=course.id).delete()
    Enrollment.query.filter_by(course_id=course.id).delete()
    LessonProgress.query.filter_by(course_id=course.id).delete()

    db.session.delete(course)
    db.session.commit()

    flash("Course deleted successfully")
    return redirect(url_for("dashboard"))


@app.route("/course/<int:course_id>/enroll", methods=["POST"])
def enroll_course(course_id):
    if not login_required():
        return redirect(url_for("login"))

    if session.get("role") == "admin":
        flash("Admin does not need to enroll")
        return redirect(url_for("course_detail", course_id=course_id))

    existing_enrollment = Enrollment.query.filter_by(
        user_id=session["user_id"],
        course_id=course_id
    ).first()

    if existing_enrollment:
        flash("You are already enrolled in this course")
        return redirect(url_for("course_detail", course_id=course_id))

    enrollment = Enrollment(
        user_id=session["user_id"],
        course_id=course_id
    )

    db.session.add(enrollment)
    db.session.commit()

    flash("You enrolled in the course successfully")
    return redirect(url_for("dashboard"))


@app.route("/course/<int:course_id>")
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    lessons = Lesson.query.filter_by(course_id=course.id).all()
    quizzes = Quiz.query.filter_by(course_id=course.id).all()

    is_enrolled = False
    completed_lessons = []
    total_lessons = len(lessons)
    completed_count = 0
    progress_percent = 0

    if login_required() and session.get("role") == "student":
        enrollment = Enrollment.query.filter_by(
            user_id=session["user_id"],
            course_id=course.id
        ).first()

        if enrollment:
            is_enrolled = True

        completed = LessonProgress.query.filter_by(
            user_id=session["user_id"],
            course_id=course.id
        ).all()

        completed_lessons = [item.lesson_id for item in completed]
        completed_count = len(completed_lessons)

        if total_lessons > 0:
            progress_percent = int((completed_count / total_lessons) * 100)

    return render_template(
        "course_detail.html",
        course=course,
        lessons=lessons,
        quizzes=quizzes,
        is_enrolled=is_enrolled,
        completed_lessons=completed_lessons,
        progress_percent=progress_percent,
        completed_count=completed_count,
        total_lessons=total_lessons
    )


@app.route("/course/<int:course_id>/add-lesson", methods=["GET", "POST"])
def add_lesson(course_id):
    if not login_required():
        return redirect(url_for("login"))

    if not admin_required():
        flash("Only admin can add lessons")
        return redirect(url_for("dashboard"))

    course = Course.query.get_or_404(course_id)

    if request.method == "POST":
        title = request.form["title"]
        video_url = request.form.get("video_url")

        pdf = request.files.get("pdf_file")
        pdf_filename = None

        if pdf and pdf.filename != "":
            pdf_filename = secure_filename(pdf.filename)
            pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], pdf_filename)
            pdf.save(pdf_path)

        lesson = Lesson(
            course_id=course.id,
            title=title,
            video_url=video_url,
            pdf_file=pdf_filename
        )

        db.session.add(lesson)
        db.session.commit()

        flash("Lesson added successfully")
        return redirect(url_for("course_detail", course_id=course.id))

    return render_template("add_lesson.html", course=course)


@app.route("/course/<int:course_id>/add-quiz", methods=["GET", "POST"])
def add_quiz(course_id):
    if not login_required():
        return redirect(url_for("login"))

    if not admin_required():
        flash("Only admin can add quizzes")
        return redirect(url_for("dashboard"))

    course = Course.query.get_or_404(course_id)

    if request.method == "POST":
        quiz = Quiz(
            course_id=course.id,
            question=request.form["question"],
            option_a=request.form["option_a"],
            option_b=request.form["option_b"],
            option_c=request.form["option_c"],
            option_d=request.form["option_d"],
            correct_answer=request.form["correct_answer"]
        )

        db.session.add(quiz)
        db.session.commit()

        flash("Quiz question added successfully")
        return redirect(url_for("course_detail", course_id=course.id))

    return render_template("add_quiz.html", course=course)


@app.route("/lesson/<int:lesson_id>/complete", methods=["POST"])
def complete_lesson(lesson_id):
    if not login_required():
        return redirect(url_for("login"))

    if session.get("role") != "student":
        flash("Only students can complete lessons")
        return redirect(url_for("dashboard"))

    lesson = Lesson.query.get_or_404(lesson_id)

    enrollment = Enrollment.query.filter_by(
        user_id=session["user_id"],
        course_id=lesson.course_id
    ).first()

    if not enrollment:
        flash("You must enroll before completing lessons")
        return redirect(url_for("course_detail", course_id=lesson.course_id))

    existing_progress = LessonProgress.query.filter_by(
        user_id=session["user_id"],
        lesson_id=lesson.id
    ).first()

    if not existing_progress:
        progress = LessonProgress(
            user_id=session["user_id"],
            lesson_id=lesson.id,
            course_id=lesson.course_id
        )
        db.session.add(progress)
        db.session.commit()
        flash("Lesson marked as completed")

    return redirect(url_for("course_detail", course_id=lesson.course_id))


@app.route("/course/<int:course_id>/quiz", methods=["GET", "POST"])
def take_quiz(course_id):
    if not login_required():
        return redirect(url_for("login"))

    if session.get("role") == "student":
        enrollment = Enrollment.query.filter_by(
            user_id=session["user_id"],
            course_id=course_id
        ).first()

        if not enrollment:
            flash("Please enroll in this course before taking the quiz")
            return redirect(url_for("course_detail", course_id=course_id))

    course = Course.query.get_or_404(course_id)
    quizzes = Quiz.query.filter_by(course_id=course.id).all()

    if request.method == "POST":
        score = 0

        for quiz in quizzes:
            selected_answer = request.form.get(str(quiz.id))

            if selected_answer == quiz.correct_answer:
                score += 1

        result = Result(
            user_id=session["user_id"],
            course_id=course.id,
            score=score
        )

        db.session.add(result)
        db.session.commit()

        return render_template(
            "result.html",
            course=course,
            score=score,
            total=len(quizzes)
        )

    return render_template("quiz.html", course=course, quizzes=quizzes)


if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    with app.app_context():
        db.create_all()

        admin = User.query.filter_by(email="admin@example.com").first()

        if not admin:
            admin_user = User(
                name="Admin",
                email="admin@example.com",
                password=generate_password_hash("admin123"),
                role="admin"
            )

            db.session.add(admin_user)
            db.session.commit()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
