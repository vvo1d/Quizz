from flask import Flask, render_template_string, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from dataclasses import dataclass

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-change-me"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///quiz.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    questions = db.relationship("Question", backref="quiz", cascade="all, delete-orphan", lazy=True)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    answers = db.relationship("Answer", backref="question", cascade="all, delete-orphan", lazy=True)


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=False)
    text = db.Column(db.String(300), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)


BASE_HTML = """
<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title or 'Quiz App' }}</title>
  <style>
    body { font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; background: #f5f6f8; color: #1f2937; }
    header { background: #111827; color: white; padding: 18px 32px; display: flex; justify-content: space-between; align-items: center; }
    header a { color: white; text-decoration: none; margin-left: 16px; }
    main { max-width: 920px; margin: 32px auto; background: white; padding: 28px; border-radius: 18px; box-shadow: 0 10px 30px rgba(0,0,0,.08); }
    .card { border: 1px solid #e5e7eb; border-radius: 14px; padding: 18px; margin-bottom: 16px; }
    .muted { color: #6b7280; }
    input[type=text], textarea { width: 100%; box-sizing: border-box; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 10px; margin: 6px 0 14px; }
    textarea { min-height: 80px; }
    button, .button { display: inline-block; background: #2563eb; color: white; border: 0; padding: 10px 16px; border-radius: 10px; text-decoration: none; cursor: pointer; }
    .secondary { background: #374151; }
    .danger { background: #dc2626; }
    label { font-weight: 600; }
    .answer { display: block; font-weight: 400; margin: 8px 0; }
    .question-block { padding: 16px; border-left: 4px solid #2563eb; background: #f9fafb; border-radius: 10px; margin-bottom: 18px; }
  </style>
</head>
<body>
  <header>
    <strong><a href="{{ url_for('index') }}">Quiz App</a></strong>
    <nav>
      <a href="{{ url_for('index') }}">Квизы</a>
      <a href="{{ url_for('create_quiz') }}">Создать</a>
    </nav>
  </header>
  <main>
    {{ content|safe }}
  </main>
</body>
</html>
"""


def page(content: str, title: str = "Quiz App"):
    return render_template_string(BASE_HTML, content=content, title=title)


@app.route("/")
def index():
    quizzes = Quiz.query.order_by(Quiz.id.desc()).all()
    cards = "".join(
        f"""
        <div class='card'>
          <h2>{quiz.title}</h2>
          <p class='muted'>{quiz.description or 'Без описания'}</p>
          <p>Вопросов: {len(quiz.questions)}</p>
          <a class='button' href='{url_for('take_quiz', quiz_id=quiz.id)}'>Пройти</a>
        </div>
        """
        for quiz in quizzes
    )
    if not cards:
        cards = "<p class='muted'>Пока нет квизов. Создайте первый.</p>"
    return page(f"<h1>Квизы</h1>{cards}", "Квизы")


@app.route("/quizzes/new", methods=["GET", "POST"])
def create_quiz():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()

        if not title:
            return page("<h1>Ошибка</h1><p>Название квиза обязательно.</p><a href='/quizzes/new'>Назад</a>")

        quiz = Quiz(title=title, description=description)
        db.session.add(quiz)
        db.session.flush()

        question_texts = request.form.getlist("question_text")
        for q_index, q_text in enumerate(question_texts):
            q_text = q_text.strip()
            if not q_text:
                continue

            question = Question(quiz_id=quiz.id, text=q_text)
            db.session.add(question)
            db.session.flush()

            answer_texts = request.form.getlist(f"answer_text_{q_index}")
            correct_index = request.form.get(f"correct_answer_{q_index}")

            for a_index, a_text in enumerate(answer_texts):
                a_text = a_text.strip()
                if not a_text:
                    continue
                db.session.add(Answer(
                    question_id=question.id,
                    text=a_text,
                    is_correct=str(a_index) == str(correct_index)
                ))

        db.session.commit()
        return redirect(url_for("index"))

    content = """
    <h1>Создать квиз</h1>
    <form method="post">
      <label>Название</label>
      <input type="text" name="title" placeholder="Например: Основы Python" required>

      <label>Описание</label>
      <textarea name="description" placeholder="Коротко о квизе"></textarea>

      <div id="questions"></div>

      <button type="button" class="secondary" onclick="addQuestion()">Добавить вопрос</button>
      <button type="submit">Сохранить квиз</button>
    </form>

    <script>
      let questionIndex = 0;

      function addQuestion() {
        const wrap = document.getElementById('questions');
        const idx = questionIndex++;
        const block = document.createElement('div');
        block.className = 'question-block';
        block.innerHTML = `
          <h3>Вопрос ${idx + 1}</h3>
          <label>Текст вопроса</label>
          <input type="text" name="question_text" required>

          <label>Ответы</label>
          ${[0,1,2,3].map(i => `
            <div>
              <input type="radio" name="correct_answer_${idx}" value="${i}" ${i === 0 ? 'checked' : ''}>
              <input type="text" name="answer_text_${idx}" placeholder="Ответ ${i + 1}" required>
            </div>
          `).join('')}
        `;
        wrap.appendChild(block);
      }

      addQuestion();
    </script>
    """
    return page(content, "Создать квиз")


@app.route("/quizzes/<int:quiz_id>", methods=["GET", "POST"])
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

        return redirect(url_for("quiz_result", quiz_id=quiz.id, score=score, total=total))

    questions_html = "".join(
        f"""
        <div class='question-block'>
          <h3>{question.text}</h3>
          {''.join(f"<label class='answer'><input type='radio' name='question_{question.id}' value='{answer.id}' required> {answer.text}</label>" for answer in question.answers)}
        </div>
        """
        for question in quiz.questions
    )

    content = f"""
    <h1>{quiz.title}</h1>
    <p class='muted'>{quiz.description}</p>
    <form method='post'>
      {questions_html}
      <button type='submit'>Завершить</button>
    </form>
    """
    return page(content, quiz.title)


@app.route("/quizzes/<int:quiz_id>/result")
def quiz_result(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    score = int(request.args.get("score", 0))
    total = int(request.args.get("total", 0))
    percent = round((score / total) * 100) if total else 0
    content = f"""
    <h1>Результат</h1>
    <div class='card'>
      <h2>{quiz.title}</h2>
      <p>Правильных ответов: <strong>{score} из {total}</strong></p>
      <p>Итог: <strong>{percent}%</strong></p>
      <a class='button' href='{url_for('take_quiz', quiz_id=quiz.id)}'>Пройти ещё раз</a>
      <a class='button secondary' href='{url_for('index')}'>К списку квизов</a>
    </div>
    """
    return page(content, "Результат")


@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database initialized")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
