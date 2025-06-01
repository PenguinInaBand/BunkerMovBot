
from interactions import slash_command, SlashContext, SlashCommandOption, OptionType, Client, Intents
import os
from tinydb import TinyDB, Query
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
import requests
import urllib3


load_dotenv()
db = TinyDB('ratings.json')
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# Flask app for Render health check
app = Flask(__name__)
@app.route('/')
def home():
    return "Discord bot is online"

def run_web():
    app.run(host='0.0.0.0', port=10000)

Thread(target=run_web).start()

@slash_command(
    name="ratemovie",
    description="Rate a movie from 1-5 stars",
    options=[
        SlashCommandOption(name="title", description="Movie title", type=OptionType.STRING, required=True),
        SlashCommandOption(name="rating", description="Your rating (1-5)", type=OptionType.INTEGER, required=True, min_value=1, max_value=5)
    ]
)
async def rate_movie(ctx: SlashContext, title: str, rating: int):
    await ctx.defer()
    title_key = title.lower().strip()
    user_id = str(ctx.author.id)
    Movie = Query()
    entry = db.get(Movie.title == title_key)
    ratings = entry.get("ratings", {}) if entry else {}
    ratings[user_id] = rating
    db.upsert({"title": title_key, "ratings": ratings}, Movie.title == title_key)
    total, count = sum(ratings.values()), len(ratings)
    avg = total / count
    stars = "⭐" * rating
    avg_stars = "⭐" * round(avg)
    msg = f"✅ **{title}** rated {stars} ({rating}/5)\n📊 **Average:** {avg_stars} ({avg:.1f}/5) from {count} votes"
    await ctx.send(msg)

@slash_command(
    name="movieratings",
    description="View all ratings for a movie",
    options=[SlashCommandOption(name="title", description="Movie title", type=OptionType.STRING, required=True)]
)
async def movie_ratings(ctx: SlashContext, title: str):
    await ctx.defer()
    Movie = Query()
    entry = db.get(Movie.title == title.lower().strip())
    if not entry:
        await ctx.send(f"❌ No ratings for **{title}** yet.")
        return
    ratings = entry["ratings"]
    total, count = sum(ratings.values()), len(ratings)
    avg = total / count
    avg_stars = "⭐" * round(avg)
    breakdown = {i: 0 for i in range(1, 6)}
    for r in ratings.values():
        breakdown[r] += 1
    response = f"🎬 **{title}** Ratings\n📊 **Average:** {avg_stars} ({avg:.1f}/5) from {count} votes\n\n**Breakdown:**\n"
    for i in range(5, 0, -1):
        bar = "█" * breakdown[i]
        response += f"{'⭐'*i}: {breakdown[i]} {bar}\n"
    await ctx.send(response)

@slash_command(
    name="moviedetails",
    description="Get details about a movie or TV show",
    options=[SlashCommandOption(name="title", description="Title of the movie/show", type=OptionType.STRING, required=True)]
)
async def movie_details(ctx: SlashContext, title: str):
    await ctx.defer()
    try:
        res = requests.get(f"https://www.omdbapi.com/?apikey={OMDB_API_KEY}&t={title}")
        data = res.json()
        if data.get("Response") == "False":
            await ctx.send(f"❌ Could not find details for **{title}**.")
            return
        embed = {
            "title": f"{data.get('Title')} ({data.get('Year')})",
            "description": data.get("Plot"),
            "fields": [
                {"name": "Genre", "value": data.get("Genre", "N/A"), "inline": True},
                {"name": "Director", "value": data.get("Director", "N/A"), "inline": True},
                {"name": "IMDB Rating", "value": data.get("imdbRating", "N/A"), "inline": True},
            ],
            "image": {"url": data["Poster"]} if data.get("Poster") and data["Poster"] != "N/A" else {}
        }
        await ctx.send(embeds=[embed])
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@slash_command(
    name="leaderboard",
    description="Show the top 10 highest rated movies based on average ratings"
)
async def leaderboard(ctx: SlashContext):
    await ctx.defer()

    all_entries = db.all()
    leaderboard_data = []

    for entry in all_entries:
        title = entry["title"]
        ratings = entry.get("ratings", {})
        if ratings:
            avg = sum(ratings.values()) / len(ratings)
            leaderboard_data.append((title, avg, len(ratings)))

    if not leaderboard_data:
        await ctx.send("❌ No movie ratings found yet.")
        return

    # Sort by average rating (descending), then by number of ratings (descending)
    leaderboard_data.sort(key=lambda x: (-x[1], -x[2]))
    top_10 = leaderboard_data[:10]

    response = "**🏆 Top 10 Rated Movies:**\n"
    for i, (title, avg, count) in enumerate(top_10, 1):
        stars = "⭐" * round(avg)
        response += f"{i}. **{title.title()}** — {stars} ({avg:.2f}/5 from {count} vote{'s' if count != 1 else ''})\n"

    await ctx.send(response)

print("Starting bot...")
bot = Client(token=os.environ["DISCORD_BOT_TOKEN"], intents=Intents.GUILDS | Intents.GUILD_MESSAGES)
bot.start()
