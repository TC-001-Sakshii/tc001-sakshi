import pytest

from fulfilment import create_app


@pytest.fixture()
def app(tmp_path):
    database_path = tmp_path / "test.db"
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(database_path),
        }
    )
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()
