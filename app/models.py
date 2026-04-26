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
    TYPE_SINGLE = "single"
    TYPE_MULTIPLE = "multiple"

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False, default=TYPE_SINGLE)

    answers = db.relationship(
        "Answer",
        backref="question",
        cascade="all, delete-orphan",
        lazy=True,
    )

    @property
    def is_multiple(self):
        return self.question_type == self.TYPE_MULTIPLE


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=False)
    text = db.Column(db.String(300), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)