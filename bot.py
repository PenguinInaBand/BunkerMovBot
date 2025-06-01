
from interactions import slash_command, SlashContext, SlashCommandOption, OptionType, Client, Intents
import os
from tinydb import TinyDB, Query
from dotenv import load_dotenv

load_dotenv()  # Load .env locally if available

db = TinyDB('ratings.json')

@slash_command(
    name="ratemovie",
    description="Rate a movie from 1-5 stars",
    options=[
        SlashCommandOption(
            name="title",
            description="The title of the movie to rate",
            type=OptionType.STRING,
            required=True
        ),
        SlashCommandOption(
            name="rating",
            description="Your rating (1-5 stars)",
            type=OptionType.INTEGER,
            required=True,
            min_value=1,
            max_value=5
        )
    ]
)
async def rate_movie(ctx: SlashContext, title: str, rating: int):
    await ctx.defer()

    try:
        title_key = title.lower().strip()
        user_id = str(ctx.author.id)

        Movie = Query()
        existing_entry = db.get((Movie.title == title_key))

        if existing_entry:
            ratings = existing_entry.get("ratings", {})
        else:
            ratings = {}

        ratings[user_id] = rating
        db.upsert({"title": title_key, "ratings": ratings}, Movie.title == title_key)

        total = sum(ratings.values())
        count = len(ratings)
        avg = total / count
        stars = "⭐" * rating
        avg_stars = "⭐" * round(avg)

        response = f"✅ **{title}** rated {stars} ({rating}/5)\n"
        response += f"📊 **Average:** {avg_stars} ({avg:.1f}/5) from {count} vote{'s' if count != 1 else ''}"
        await ctx.send(response)

    except Exception as e:
        await ctx.send(f"❌ Error rating movie: {str(e)}")


@slash_command(
    name="movieratings",
    description="View all ratings for a movie",
    options=[
        SlashCommandOption(
            name="title",
            description="The title of the movie",
            type=OptionType.STRING,
            required=True
        )
    ]
)
async def movie_ratings(ctx: SlashContext, title: str):
    await ctx.defer()

    try:
        title_key = title.lower().strip()
        Movie = Query()
        entry = db.get(Movie.title == title_key)

        if not entry:
            await ctx.send(f"❌ No ratings for **{title}** yet.")
            return

        ratings = entry["ratings"]
        total = sum(ratings.values())
        count = len(ratings)
        avg = total / count
        avg_stars = "⭐" * round(avg)

        breakdown = {i: 0 for i in range(1, 6)}
        for r in ratings.values():
            breakdown[r] += 1

        response = f"🎬 **{title}** Ratings\n"
        response += f"📊 **Average:** {avg_stars} ({avg:.1f}/5) from {count} votes\n\n"
        response += "**Rating Breakdown:**\n"

        for i in range(5, 0, -1):
            stars = "⭐" * i
            bar = "█" * breakdown[i]
            response += f"{stars}: {breakdown[i]} {bar}\n"

        await ctx.send(response)

    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")


print("Starting bot...")
bot = Client(token=os.environ["DISCORD_BOT_TOKEN"],
             intents=Intents.GUILDS | Intents.GUILD_MESSAGES)

bot.start()


# Add a web server to keep the bot "alive" for services like Render
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Discord bot is online"

def run_web():
    app.run(host='0.0.0.0', port=8080)

# Start Flask web server in a separate thread
Thread(target=run_web).start()
