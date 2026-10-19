# Backend image — FastAPI served by uvicorn.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# Install deps first so this layer is cached when only code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# On container start: create tables, seed base data + demo tickets, then serve.
# (Seeding is safe to run every boot here because it's a demo; in production
#  you would run migrations/seeds as a separate one-off job.)
EXPOSE 8000
CMD ["sh", "-c", "python -m app.seed && python -m app.seed_demo && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
