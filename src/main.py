import os
import discord
import asyncio
import subprocess, sys, importlib

from dotenv import load_dotenv
from discord.ext import commands

# Load DISCORD_BOT_TOKEN from .env file
load_dotenv()  
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Make sure ytdlp is up-to-date
def ensure_latest_ytdlp():
    import yt_dlp
    try:
        import importlib.metadata
        current_version = importlib.metadata.version("yt-dlp")
    except Exception:
        current_version = "unknown"
    print(f"Current yt-dlp version: {current_version}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "yt-dlp"])
        importlib.reload(yt_dlp)  # reload updated module
    except Exception as e:
        print("Could not auto-update yt-dlp:", e)


# Create a bot object
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f"Bot Ready! Bot connected as {bot.user}")

async def load():
    # Get the absolute path of the cogs
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cogs_dir = os.path.join(base_dir, "cogs")
    # Load all cogs
    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")   

async def main():
    ensure_latest_ytdlp()
    async with bot:
        await load()
        await bot.start(TOKEN)      # Run the bot

asyncio.run(main())