"""Adds a few sample tickets so the admin queue isn't empty. Run after app.seed.

They are triaged with the keyword rules, not Gemini, so a fresh deploy costs no API quota.
"""
from .database import SessionLocal
from .models import Author, Book, Ticket, TicketResponse, TicketStatus, Admin
from .ai.service import classify_ticket

# author email, book title (or None), subject, description
DEMO = [
    ("priya.sharma@email.com", "Whispers of the Ganges",
     "Haven't received royalty in 6 months",
     "I published my book over 6 months ago and still haven't received any royalty payment. "
     "My dashboard shows pending royalty but nothing has hit my bank account. What's going on?"),
    ("rohit.kapoor@email.com", "Code & Karma",
     "Wrong ISBN showing on Amazon",
     "The ISBN on my Amazon listing is different from the one printed inside my physical copy. "
     "This looks like a serious data issue — buyers are confused. Please fix urgently."),
    ("ananya.reddy@email.com", "Between Two Temples",
     "Print quality is poor on author copies",
     "I received my author copies and the print quality is terrible — the images are blurry and "
     "a few pages are misaligned. I'm not comfortable sharing these with reviewers."),
    ("vikram.joshi@email.com", "Debugging Life",
     "Book showing 'Currently Unavailable' on Amazon",
     "My book is published but Amazon India shows it as Currently Unavailable since yesterday. "
     "Is this a stock issue? Can you help get it back up?"),
    ("meera.nair@email.com", None,
     "Can I update my author bio?",
     "Quick question — can I update the author bio and book description on my dashboard after the "
     "book is already live? How long do changes take to reflect?"),
    ("sneha.kulkarni@email.com", "Midnight in Mysore",
     "When will my book move out of Cover Design?",
     "It's been 3 weeks and 'Midnight in Mysore' is still in Cover Design. When will it move forward?"),
]


def run():
    db = SessionLocal()
    try:
        admin = db.query(Admin).first()
        made = 0
        for email, book_title, subject, desc in DEMO:
            author = db.query(Author).filter(Author.email == email).first()
            if not author:
                continue
            book = None
            if book_title:
                book = db.query(Book).filter(
                    Book.author_id == author.id, Book.title == book_title
                ).first()
            # keyword rules here so seeding never spends Gemini quota
            triage = classify_ticket(subject, desc, use_ai=False)
            ticket = Ticket(
                author_id=author.id,
                book_id=book.id if book else None,
                subject=subject,
                description=desc,
                status=TicketStatus.OPEN,
                ai_category=triage["category"], ai_priority=triage["priority"],
                category=triage["category"], priority=triage["priority"],
                ai_classification_note=triage["note"],
            )
            db.add(ticket)
            db.flush()
            # reply to the first one so there is a thread to look at
            if made == 0 and admin:
                ticket.status = TicketStatus.IN_PROGRESS
                ticket.responses.append(TicketResponse(
                    admin_id=admin.id, was_ai_drafted=1,
                    body=("Hi Priya, thank you for reaching out, and I'm sorry for the worry here. "
                          "Royalties are calculated quarterly and paid within 45 days of the quarter "
                          "ending, with a minimum payout threshold of Rs.1,000. I can see a pending "
                          "amount on your account, so I'm escalating this to our payments team and will "
                          "get back to you with the exact payout date within 48 hours. Could you confirm "
                          "your bank details on the dashboard are current in the meantime?"),
                ))
            made += 1
        db.commit()
        print(f"Added {made} demo tickets.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
