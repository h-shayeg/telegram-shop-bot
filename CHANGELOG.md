# Changelog

All notable changes to this project are listed here.

## [1.0.0] - 2026-11-04

First complete version of the shop bot.

### For customers

- Product catalog with categories, photos, prices and stock status
- Cart with quantity buttons and stock checks
- Checkout with name, phone number (typed or shared with one tap) and address, then a summary to confirm
- Order history, cancelling orders while they are new, and a message on every status change
- Persian and English interface, with Persian digits and the Persian (Jalali) calendar

### For the shop owner

- Admin panel inside the bot for the users listed in `ADMIN_IDS`
- Add and edit products and categories, upload product photos, hide or show products
- Notification of every new order and management of order statuses
- Sales report for the last 7 or 30 days with best sellers and a daily sales chart

### Quality

- Orders are placed in one database transaction with row locking, so the last item can never be sold twice
- 57 tests, including tests against a real PostgreSQL database
- Linting, a migrations check and all tests run on GitHub Actions on every push

[1.0.0]: https://github.com/h-shayeg/telegram-shop-bot/releases/tag/v1.0.0
