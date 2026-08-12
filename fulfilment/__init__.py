import os

from flask import Flask

from .db import init_app, init_db


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE_PATH=os.environ.get("DATABASE_PATH", "fulfilment.db"),
        JSON_SORT_KEYS=False,
    )

    if test_config:
        app.config.update(test_config)

    init_app(app)

    from .orders import api

    app.register_blueprint(api)

    with app.app_context():
        init_db()

    return app
