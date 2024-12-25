import os
import discord
import asyncio

from dotenv import load_dotenv
from discord.ext import commands

# Load DISCORD_BOT_TOKEN from .env file
load_dotenv()  
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Sync commands only if true, set to true if new commands are added
SYNC_MODE = False

# Create a bot object
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f"Bot Ready! Bot connected as {bot.user}")
    if SYNC_MODE:
        try:
            synced_commands = await bot.tree.sync()
            print(f"Synced {len(synced_commands)} commands")
        except Exception as e:
            print(f"An error with syncing application commands has occurred: {e}")

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