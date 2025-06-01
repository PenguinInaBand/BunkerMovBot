
# Discord Movie Rating Bot

A slash-command Discord bot to rate and view movie ratings using TinyDB. Deployable on Render.com.

## Commands

- `/ratemovie title:<movie name> rating:<1-5>` – Submit or update a rating.
- `/movieratings title:<movie name>` – View all ratings and breakdown.

## Setup

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file:
   ```env
   DISCORD_BOT_TOKEN=your_token_here
   ```

3. Run locally:
   ```bash
   python bot.py
   ```

## Deploy to Render

- Push to GitHub
- Create a "Background Worker" service on Render
- Set env var `DISCORD_BOT_TOKEN`
- Build Command: `pip install -r requirements.txt`
- Start Command: `python bot.py`
