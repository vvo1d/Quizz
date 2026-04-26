from flask import Flask

from app.extensions import db
from app.routes import main_bp


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY="dev-secret-change-me",
        SQLALCHEMY_DATABASE_URI="sqlite:///quiz.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(app)
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()

    return app