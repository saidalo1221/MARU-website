from app.database import Base, engine
from app import models  # noqa: F401  (registers models on Base.metadata)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    print("Tables created:", ", ".join(sorted(Base.metadata.tables.keys())))


if __name__ == "__main__":
    init_db()
