import os
import discord

from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands


# Load ADMINISTRATOR_ID from .env file
load_dotenv()
ADMINISTRATOR_ID = os.getenv("ADMINISTRATOR_ID")

class Help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_msg = bot.embed_msg


    @commands.Cog.listener()
    async def on_ready(self):
        print("Help_cog ready!")


    # Main function for help command
    @app_commands.command(name="help", description="List all avaliable commands")
    async def help(self, interaction: discord.Interaction):
        formatted_description = """
**Music Cog**
```
/music_play(p)  - Download and play music from YouTube
/music_clear(c) - Clear all music from the queue
/music_list(l)  - List all music in the queue
/music_skip(s)  - Skip the current music
/music_pause    - Pause the currently playing music
/music_resume   - Resume the paused music
/music_repeat   - Toggle repeat mode for queue
/music_remove   - Remove music from the queue
/music_add      - Add music to current album
/music_delete   - Delete music from current album
```
**Album Cog**
```
/album_create   - Create a new album
/album_tracks   - List all tracks in the current album
/album_list     - List all albums
/album_switch   - Switch to another album
/album_play     - Add the current album to the queue
/album_rename   - Rename an album
/album_delete   - Delete an album
```
**Help Cog**
```
/help           - List all commands available
/ping           - Show the latency of the bot
/auto_delete    - Set auto-delete seconds for messages
```
        """
        await self.embed_msg.send_embed_msg_inter(interaction, "Command List", formatted_description)

    
    # Main function for ping command
    @app_commands.command(name="ping", description="Show the latency of the bot")
    async def ping(self, interaction: discord.Interaction):
        await self.embed_msg.send_embed_msg_inter(interaction, f"{self.bot.user.name}'s Latency (ms): ", f"{round(self.bot.latency * 1000)} ms")


    # Main function for set_auto_delete command
    @app_commands.command(name="auto_delete", description="Set auto-delete seconds for messages")
    @app_commands.describe(seconds="Number of seconds before auto-delete")
    async def auto_delete(self, interaction: discord.Interaction, seconds: int):
        # Check valid argument
        if seconds <= 0:
            await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", "Invalid argument! It must be an positive non-zero integer.", msg_color=discord.Color.red())
            return
        # Seconds larger than 1 hour becomes switching off auto-delete
        if seconds > 3600:
            self.embed_msg.delete_msg_seconds = None
            await self.embed_msg.send_embed_msg_inter(interaction, "Auto-Delete Off", "Message auto-delete is now off.")
            return
        # Set number of seconds
        self.embed_msg.delete_msg_seconds = seconds
        await self.embed_msg.send_embed_msg_inter(interaction, "Auto-Delete On", f"Message auto-delete is now set to {self.embed_msg.delete_msg_seconds} seconds.")


    # Main function for sync command
    @commands.command(name="sync", help="- Sync all slash commands")
    async def sync(self, ctx: commands.Context):
        if str(ctx.author.id) != ADMINISTRATOR_ID:
            await self.embed_msg.send_embed_msg_ctx(ctx, "ERROR", "You do not have permission to use this command.", msg_color=discord.Color.red())
            return
        try:
            synced_commands = await self.bot.tree.sync()
            print(f"Synced {len(synced_commands)} commands")
            await self.embed_msg.send_embed_msg_ctx(ctx, "Sync Successful!", f"Synced {len(synced_commands)} commands.")
        except Exception as e:
            print(f"An error with syncing application commands has occurred: {e}")
            await self.embed_msg.send_embed_msg_ctx(ctx, "ERROR", f"An error with syncing application commands has occurred: {e}", msg_color=discord.Color.red())


async def setup(bot):
    await bot.add_cog(Help_cog(bot))