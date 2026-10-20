"""Company policies given in the brief. Kept server side and passed to the model only when drafting a reply."""

KNOWLEDGE_BASE = """\
COMPANY OVERVIEW
- BookLeaf Publishing is a self-publishing company operating in India and the US.
- Publishing packages: Standard Free (no upfront cost) and Bestseller Breakthrough (premium, paid, with marketing & distribution add-ons).
- BookLeaf handles cover design, typesetting, ISBN assignment, printing, distribution and royalty management.
- In-house printing & warehouse in Delhi. Print partners: Repro India and Epitome Books.

ROYALTY POLICY
- 80/20 split: 80% of net profit per book to the author, 20% to BookLeaf.
- Net profit = MRP minus printing cost, platform commission (Amazon/Flipkart) and shipping.
- Royalties are calculated QUARTERLY and paid within 45 days of the quarter ending.
- Minimum payout threshold: Rs.1,000. Below this, it rolls over to the next quarter.
- Payouts go via bank transfer to the account linked in the author's dashboard.

ISBN POLICY
- Every book gets a unique ISBN assigned by BookLeaf under BookLeaf's imprint.
- Author wanting an ISBN under their own imprint must obtain it independently.
- An ISBN error (duplicate, wrong book linked) is HIGH priority, escalated to the production team.

PRINTING & QUALITY
- In-house printing handles most orders; overflow/special formats go to Repro India or Epitome Books.
- Standard print turnaround: 5-7 business days from order confirmation.
- Quality issue (misprints, binding defects, colour inconsistency): BookLeaf arranges a FREE reprint after verification; author may need to share photos of the defective copy.

DISTRIBUTION & AVAILABILITY
- Books list on Amazon India, Flipkart, Amazon US, Amazon UK and the BookLeaf Store.
- New listings typically go live within 7-10 business days after publication completes.
- "Unavailable" on a platform usually means a stock sync issue; BookLeaf can trigger a re-sync within 24-48 hours.

PRODUCTION STAGES
- Manuscript Received -> Editing (if opted) -> Cover Design -> Typesetting -> Proofreading -> ISBN Assignment -> Printing -> Distribution Setup -> Published & Live.
- Authors are updated at each stage by email. Delays usually happen at Cover Design (awaiting author approval) and Proofreading (revision rounds).

COMMUNICATION TONE
- Always empathetic and professional. Authors are partners, not customers to be managed.
- Acknowledge the concern before giving the solution.
- Be specific: use actual numbers, dates and statuses, not vague reassurance.
- If it is BookLeaf's fault (delayed royalties, ISBN error), own it directly. No corporate deflection.
- If escalation/investigation is needed, give a clear timeline (e.g. "within 48 hours"), not an open-ended promise.
- Always end with a clear next step for the author and/or the BookLeaf team.
"""

# must match TicketCategory in models.py
CATEGORIES = [
    "Royalty & Payments",
    "ISBN & Metadata Issues",
    "Printing & Quality",
    "Distribution & Availability",
    "Book Status & Production Updates",
    "General Inquiry",
]

PRIORITIES = ["Critical", "High", "Medium", "Low"]
