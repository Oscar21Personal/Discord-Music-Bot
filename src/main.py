import os
import discord
import asyncio

from dotenv import load_dotenv
from discord.ext import commands

# Load DISCORD_BOT_TOKEN from .env file
load_dotenv()  
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Create a bot object
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

async def load():
    # Get the absolute path of the cogs
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cogs_dir = os.path.join(base_dir, "cogs")
    # Load all cogs
    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")   

async def main():
    async with bot:
        await load()
        await bot.start(TOKEN)      # Run the bot

asyncio.run(main())