# Bazarche - Telegram Shop Bot

A Telegram shop bot built with Python and aiogram 3. Customers browse products, add them to a cart and place orders; the shop owner manages products and orders from inside the bot.

> Work in progress.

## Planned features

- Product catalog with categories, photos and prices
- Cart and checkout (name, phone, address)
- Order status tracking with automatic customer notifications
- Admin panel inside the bot: products, orders, broadcast messages
- Sales report with charts
- English and Persian interface

## Tech stack

Python 3.13, aiogram 3, PostgreSQL 16, SQLAlchemy 2 (async), Alembic, Docker Compose

## Run locally

1. Copy `.env.example` to `.env` and fill in the values: the bot token from @BotFather, your Telegram user id in `ADMIN_IDS` (comma-separated for several admins), and the same database password in both `POSTGRES_PASSWORD` and `DATABASE_URL`.
2. Start the database: `docker compose up -d --wait`
3. Install dependencies: `python -m venv .venv && .venv/bin/pip install -r requirements.txt`
4. Create the tables: `.venv/bin/alembic upgrade head`
5. Load sample products (optional): `.venv/bin/python -m scripts.seed_sample_data`
6. Start the bot: `.venv/bin/python -m bot`

## License

MIT
