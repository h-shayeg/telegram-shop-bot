FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Run as a normal user, not root
RUN useradd --create-home --uid 10001 shopbot
USER shopbot

# Create or update the database tables, then start the bot
CMD ["sh", "-c", "alembic upgrade head && exec python -m bot"]
