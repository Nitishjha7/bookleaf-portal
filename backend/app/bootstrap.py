"""Container start-up: create tables and load the data only if the db is empty.

app.seed drops every table, so it can't run on each boot against a real database.
"""
from .database import Base, engine, SessionLocal
from .models import Author
from . import seed, seed_demo


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        empty = db.query(Author).count() == 0
    finally:
        db.close()
    if empty:
        seed.run()
        seed_demo.run()
    else:
        print("db already has data, skipping seed")


if __name__ == "__main__":
    run()
