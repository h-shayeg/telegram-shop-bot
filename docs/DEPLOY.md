# Deploy on a server

This guide runs the bot and its database on a Linux server with Docker, so the shop stays online around the clock. No programming is needed: every step is a command to copy and paste.

## What you need

- **A server (VPS)** with Ubuntu 24.04. One CPU, 1 to 2 GB of RAM and 20 GB of disk are enough. The server must be in a country where Telegram is reachable. A domain name is not needed.
- **A bot token.** In Telegram, open [@BotFather](https://t.me/BotFather), send `/newbot`, choose a name and a username, and copy the token it gives you.
- **Your Telegram user id**, so the bot knows you are the shop owner. Bots such as [@userinfobot](https://t.me/userinfobot) show it when you send them a message.

## 1. Connect to the server

Your server provider gives you an IP address and a password. On your computer, open a terminal and run:

```bash
ssh root@YOUR_SERVER_IP
```

## 2. Install Docker

```bash
curl -fsSL https://get.docker.com | sh
```

## 3. Download the bot

```bash
git clone https://github.com/h-shayeg/telegram-shop-bot.git
cd telegram-shop-bot
```

## 4. Fill in the settings

Create a password for the database:

```bash
openssl rand -hex 16
```

Copy the example settings file and open it:

```bash
cp .env.example .env
nano .env
```

Fill in these lines:

| Setting | What to write |
| --- | --- |
| `BOT_TOKEN` | The token from @BotFather |
| `POSTGRES_PASSWORD` | The password you just created (letters and digits only) |
| `ADMIN_IDS` | Your Telegram user id. For several admins, separate the ids with commas |
| `PROXY_URL` | Leave empty |
| `TIMEZONE` | Your time zone, for example `Asia/Tehran` or `Europe/Istanbul` |

Leave the other lines as they are: inside Docker, the bot finds its database by itself. Save with `Ctrl+O`, then `Enter`, and close the editor with `Ctrl+X`.

## 5. Start the bot

```bash
docker compose --profile bot up -d --build
```

The first start takes a few minutes. The bot creates its database tables by itself. To check that it is running:

```bash
docker compose logs -f bot
```

When you see `Start polling`, the bot is online. Press `Ctrl+C` to stop watching the logs (the bot keeps running). Now send `/start` to your bot in Telegram, and `/admin` to open the admin panel.

To load the sample products (optional):

```bash
docker compose --profile bot run --rm bot python -m scripts.seed_sample_data
```

The bot and the database start again by themselves after the server restarts.

## Everyday commands

Run these inside the `telegram-shop-bot` folder.

| Task | Command |
| --- | --- |
| See the logs | `docker compose logs -f bot` |
| Restart the bot | `docker compose --profile bot restart bot` |
| Stop the bot | `docker compose --profile bot stop` |
| Start it again | `docker compose --profile bot up -d` |
| Apply changed settings in `.env` | `docker compose --profile bot up -d` |
| Update to the latest version | `git pull && docker compose --profile bot up -d --build` |

## Backups

All products, orders and customers are in the database. To save a backup file:

```bash
docker compose exec -T db pg_dump -U shopbot shopbot > backup-$(date +%F).sql
```

Copy the backup files to another place from time to time, for example to your own computer with `scp`.

To restore a backup on a new server, follow steps 1 to 4, start only the database with `docker compose up -d --wait`, then run:

```bash
docker compose exec -T db psql -U shopbot shopbot < backup-2026-11-04.sql
```

and continue with step 5.

## Troubleshooting

- **The bot does not answer.** Look at the logs with `docker compose logs -f bot`.
- **`Unauthorized` in the logs.** The bot token is wrong. Fix `BOT_TOKEN` in `.env` and run `docker compose --profile bot up -d`.
- **`Conflict: terminated by other getUpdates request` in the logs.** The same bot is running somewhere else too, for example on your own computer. Stop the other copy: one bot token can be used by only one running bot.
- **Timeouts in the logs.** The server cannot reach Telegram. Choose a server in a country where Telegram is not blocked.
- **`/admin` does not work.** Check that your user id is in `ADMIN_IDS`, then run `docker compose --profile bot up -d`.
