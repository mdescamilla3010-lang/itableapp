from app.core.config import Settings


def test_bare_postgres_scheme_gets_psycopg2_driver():
    settings = Settings(DATABASE_URL="postgres://user:pass@host:5432/db")
    assert settings.DATABASE_URL == "postgresql+psycopg2://user:pass@host:5432/db"


def test_bare_postgresql_scheme_gets_psycopg2_driver():
    settings = Settings(DATABASE_URL="postgresql://user:pass@host:5432/db")
    assert settings.DATABASE_URL == "postgresql+psycopg2://user:pass@host:5432/db"


def test_url_with_driver_already_set_is_left_unchanged():
    url = "postgresql+psycopg2://user:pass@host:5432/db"
    settings = Settings(DATABASE_URL=url)
    assert settings.DATABASE_URL == url
