from app.extensions import db


class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")

    questions = db.relationship(
        "Question",
        backref="quiz",
        cascade="all, delete-orphan",
        lazy=True,
    )


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)

    answers = db.relationship(
        "Answer",
        backref="question",
        cascade="all, delete-orphan",
        lazy=True,
    )


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=False)
    text = db.Column(db.String(300), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)