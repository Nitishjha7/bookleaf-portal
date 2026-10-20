"""Loads seed_data.json (10 authors, 18 books) and creates one admin.

    python -m app.seed

Drops and recreates all tables first. Logins: admin@bookleaf.com / admin123,
authors use their own email with author123.
"""
import json
import os

from .database import Base, engine, SessionLocal
from .models import Author, Book, Admin
from .auth import hash_password

SEED_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "seed_data.json")
AUTHOR_PASSWORD = "author123"
ADMIN_PASSWORD = "admin123"


def run():
    # wipes everything, so only run on a fresh or demo db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with open(SEED_FILE) as f:
        data = json.load(f)

    db = SessionLocal()
    try:
        for a in data["authors"]:
            author = Author(
                author_code=a["author_id"],
                name=a["name"],
                email=a["email"].lower(),
                phone=a.get("phone"),
                city=a.get("city"),
                joined_date=a.get("joined_date"),
                hashed_password=hash_password(AUTHOR_PASSWORD),
            )
            db.add(author)
            db.flush()  # need author.id for the books

            for b in a.get("books", []):
                db.add(Book(
                    book_code=b["book_id"],
                    author_id=author.id,
                    title=b["title"],
                    isbn=b.get("isbn"),
                    genre=b.get("genre"),
                    publication_date=b.get("publication_date"),
                    status=b.get("status"),
                    mrp=b.get("mrp"),
                    author_royalty_per_copy=b.get("author_royalty_per_copy"),
                    total_copies_sold=b.get("total_copies_sold") or 0,
                    total_royalty_earned=b.get("total_royalty_earned") or 0,
                    royalty_paid=b.get("royalty_paid") or 0,
                    royalty_pending=b.get("royalty_pending") or 0,
                    last_royalty_payout_date=b.get("last_royalty_payout_date"),
                    print_partner=b.get("print_partner"),
                    available_on=b.get("available_on") or [],
                ))

        db.add(Admin(
            name="BookLeaf Ops",
            email="admin@bookleaf.com",
            hashed_password=hash_password(ADMIN_PASSWORD),
        ))
        db.commit()

        n_authors = db.query(Author).count()
        n_books = db.query(Book).count()
        print(f"Seeded {n_authors} authors and {n_books} books.")
        print("\nDemo logins")
        print("-----------")
        print("Admin : admin@bookleaf.com / admin123")
        for author in db.query(Author).all():
            print(f"Author: {author.email} / author123   ({author.name})")
    finally:
        db.close()


if __name__ == "__main__":
    run()
