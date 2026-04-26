from flask import Blueprint, render_template, request, redirect, url_for

from app.extensions import db
from app.models import Quiz, Question, Answer

main_bp = Blueprint("main", __name__)

MIN_ANSWERS = 2
MAX_ANSWERS = 10


@main_bp.route("/")
def index():
    quizzes = Quiz.query.order_by(Quiz.id.desc()).all()
    return render_template("index.html", quizzes=quizzes)


@main_bp.route("/quizzes/new", methods=["GET", "POST"])
def create_quiz():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()

        if not title:
            return render_template(
                "create_quiz.html",
                error="Название квиза обязательно.",
            )

        quiz = Quiz(title=title, description=description)
        db.session.add(quiz)
        db.session.flush()

        question_texts = request.form.getlist("question_text")

        for question_index, question_text in enumerate(question_texts):
            question_text = question_text.strip()
            if not question_text:
                continue

            question_type = request.form.get(
                f"question_type_{question_index}",
                Question.TYPE_SINGLE,
            )

            if question_type not in {Question.TYPE_SINGLE, Question.TYPE_MULTIPLE}:
                question_type = Question.TYPE_SINGLE

            answer_texts = [
                answer_text.strip()
                for answer_text in request.form.getlist(f"answer_text_{question_index}")
                if answer_text.strip()
            ]

            if len(answer_texts) < MIN_ANSWERS:
                db.session.rollback()
                return render_template(
                    "create_quiz.html",
                    error=f"У каждого вопроса должно быть минимум {MIN_ANSWERS} варианта ответа.",
                )

            if len(answer_texts) > MAX_ANSWERS:
                db.session.rollback()
                return render_template(
                    "create_quiz.html",
                    error=f"У вопроса не может быть больше {MAX_ANSWERS} вариантов ответа.",
                )

            correct_answer_indexes = set(
                request.form.getlist(f"correct_answers_{question_index}")
            )

            if not correct_answer_indexes:
                db.session.rollback()
                return render_template(
                    "create_quiz.html",
                    error="У каждого вопроса должен быть хотя бы один правильный ответ.",
                )

            if question_type == Question.TYPE_SINGLE and len(correct_answer_indexes) > 1:
                db.session.rollback()
                return render_template(
                    "create_quiz.html",
                    error="В вопросе с одним правильным ответом можно выбрать только один правильный вариант.",
                )

            question = Question(
                quiz_id=quiz.id,
                text=question_text,
                question_type=question_type,
            )
            db.session.add(question)
            db.session.flush()

            for answer_index, answer_text in enumerate(answer_texts):
                answer = Answer(
                    question_id=question.id,
                    text=answer_text,
                    is_correct=str(answer_index) in correct_answer_indexes,
                )
                db.session.add(answer)

        db.session.commit()
        return redirect(url_for("main.index"))

    return render_template("create_quiz.html")


@main_bp.route("/quizzes/<int:quiz_id>", methods=["GET", "POST"])
def take_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    if request.method == "POST":
        total = len(quiz.questions)
        score = 0

        for question in quiz.questions:
            correct_answer_ids = {
                str(answer.id)
                for answer in question.answers
                if answer.is_correct
            }

            selected_answer_ids = set(
                request.form.getlist(f"question_{question.id}")
            )

            if selected_answer_ids == correct_answer_ids:
                score += 1

        return redirect(
            url_for(
                "main.quiz_result",
                quiz_id=quiz.id,
                score=score,
                total=total,
            )
        )

    return render_template("take_quiz.html", quiz=quiz)


@main_bp.route("/quizzes/<int:quiz_id>/result")
def quiz_result(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    score = int(request.args.get("score", 0))
    total = int(request.args.get("total", 0))
    percent = round((score / total) * 100) if total else 0

    return render_template(
        "result.html",
        quiz=quiz,
        score=score,
        total=total,
        percent=percent,
    )