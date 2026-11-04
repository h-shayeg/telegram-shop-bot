# Bazarche - Telegram Shop Bot

<p>
  <a href="https://github.com/h-shayeg/telegram-shop-bot/actions/workflows/tests.yml"><img src="https://github.com/h-shayeg/telegram-shop-bot/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <img src="https://img.shields.io/badge/python-3.13-blue" alt="Python 3.13">
  <img src="https://img.shields.io/badge/PostgreSQL-16-336791" alt="PostgreSQL 16">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT"></a>
</p>

A complete online shop inside Telegram, built with Python and aiogram 3. Customers browse products, fill a cart and place orders; the shop owner manages products, orders and sales from an admin panel inside the bot. The interface is available in Persian and English.

## Features

### For customers

- Product catalog with categories, photos, prices and stock status
- Cart with quantity buttons; a cart can never hold more than the stock
- Checkout in a few steps: name, phone number (typed or shared with one tap) and address, then a summary to confirm
- Order history with the status of each order; an order can be cancelled while it is still new
- A message whenever the shop updates the status of an order
- Persian or English interface, with Persian digits and the Persian (Jalali) calendar in Persian

### For the shop owner

- Admin panel inside the bot, available only to the Telegram users listed in `ADMIN_IDS`
- Add and edit products (name, description, price, stock, photo), hide or show them, and add categories
- Instant notification of every new order, with a button to open it
- List of open orders and status changes: new → confirmed → shipped → delivered, or cancelled
- Sales report for the last 7 or 30 days: number of orders, revenue, average order, cancelled orders, best sellers and a daily sales chart

<p align="center"><img src="docs/images/sales-chart.png" alt="Daily sales chart from the admin sales report" width="640"></p>

*The daily sales chart from the admin sales report (sample data, in thousand toman, dates in the Persian calendar).*

## How it works

- **No overselling.** An order is placed in one database transaction. The product rows are locked while stock is checked and reduced, so two customers can never buy the last item at the same time. A test runs exactly this race against PostgreSQL.
- **Order history stays correct.** Product names and prices are copied into each order, so editing a product later does not change old orders.
- **Stock follows cancellations.** Cancelling an order puts its items back in stock.
- **Clear order flow.** An order status can only move forward (new → confirmed → shipped → delivered). Customers can cancel only their own orders, and only while they are new.
- **Bilingual by design.** Every text lives in `bot/locales/en.json` and `bot/locales/fa.json`; each user picks a language, and all messages, buttons, numbers and dates follow it.
- **Works behind restrictions.** The bot can reach Telegram through an HTTP or SOCKS proxy (`PROXY_URL`).

## Tech stack

Python 3.13 · aiogram 3 · PostgreSQL 16 · SQLAlchemy 2 (async, asyncpg) · Alembic · Pillow · Docker Compose · pytest · Ruff · GitHub Actions

## Project structure

```text
bot/
  handlers/      Telegram handlers: catalog, cart, checkout, orders, admin panel, sales report
  services/      Shop logic and database queries, kept separate from Telegram code
  db/            Database models and session
  middlewares/   One database session per update, user registration, language
  locales/       Persian and English texts
  charts.py      Sales chart drawn with Pillow
alembic/         Database migrations
scripts/         Sample data loader and the README chart
tests/           Unit tests and PostgreSQL tests
```

## Run locally

Requirements: Python 3.13, Docker, and a bot token from [@BotFather](https://t.me/BotFather).

1. Copy `.env.example` to `.env` and fill in the values (see [Configuration](#configuration)).
2. Start the database: `docker compose up -d --wait`
3. Install dependencies: `python -m venv .venv && .venv/bin/pip install -r requirements.txt`
4. Create the tables: `.venv/bin/alembic upgrade head`
5. Load sample products (optional): `.venv/bin/python -m scripts.seed_sample_data`
6. Start the bot: `.venv/bin/python -m bot`

Send `/start` to the bot. Admins can also use `/admin`.

## Configuration

| Variable | Required | Description |
| --- | --- | --- |
| `BOT_TOKEN` | yes | Bot token from @BotFather |
| `DATABASE_URL` | yes | Database address, for example `postgresql+asyncpg://shopbot:PASSWORD@127.0.0.1:15433/shopbot` |
| `POSTGRES_PASSWORD` | yes | Password of the database container; use the same password in `DATABASE_URL` |
| `ADMIN_IDS` | no | Telegram user ids of the admins, comma-separated |
| `PROXY_URL` | no | Proxy for reaching Telegram, for example `http://127.0.0.1:10808` or `socks5://127.0.0.1:1080` |
| `TIMEZONE` | no | Time zone for dates and reports, default `Asia/Tehran` |
| `TEST_DATABASE_URL` | no | Separate database for the PostgreSQL tests (see below) |

## Tests

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/ruff check .
.venv/bin/python -m pytest
```

The PostgreSQL tests (placing orders, stock locking, cancellations, status rules and the sales report) run only when `TEST_DATABASE_URL` is set. They wipe that database before each test, so its name must end with `_test`. To create it in the Docker database: `docker compose exec db createdb -U shopbot shopbot_test`

On every push, GitHub Actions runs the linter, applies the migrations to a fresh PostgreSQL, checks that the models match the migrations, and runs all tests.

## Roadmap

- Run the bot around the clock on a server with Docker
- Broadcast messages from admins to all customers
- Online payment

## License

MIT, see [LICENSE](LICENSE).
