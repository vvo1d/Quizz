from flask import Blueprint, render_template, request, redirect, url_for

from app.extensions import db
from app.models import Quiz, Question, Answer

main_bp = Blueprint("main", __name__)

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

            question = Question(quiz_id=quiz.id, text=question_text)
            db.session.add(question)
            db.session.flush()

            answer_texts = request.form.getlist(f"answer_text_{question_index}")
            correct_answer_index = request.form.get(f"correct_answer_{question_index}")

            for answer_index, answer_text in enumerate(answer_texts):
                answer_text = answer_text.strip()
                if not answer_text:
                    continue

                answer = Answer(
                    question_id=question.id,
                    text=answer_text,
                    is_correct=str(answer_index) == str(correct_answer_index),
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
            selected_answer_id = request.form.get(f"question_{question.id}")
            if not selected_answer_id:
                continue

            answer = Answer.query.get(int(selected_answer_id))
            if answer and answer.question_id == question.id and answer.is_correct:
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