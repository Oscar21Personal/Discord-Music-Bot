import os
import discord
import asyncio

from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands

# Load DISCORD_BOT_TOKEN from .env file
load_dotenv()  
ADMINISTRATOR_ID = os.getenv("ADMINISTRATOR_ID")

class Help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.delete_msg_seconds = None      # None: never delete


    @commands.Cog.listener()
    async def on_ready(self):
        print("Help_cog ready")


    # Helper function to send embedded messages
    async def send_embed_msg(self, interaction, msg_title, msg_description, msg_color=discord.Color.blue(), follow_up=False):
        # If auto-delete is on
        if self.delete_msg_seconds:
            msg_description += f"\n\nThis message will be deleted in {self.delete_msg_seconds} seconds."
        # Format the message
        msg_embed = discord.Embed(title=msg_title, description=msg_description, color=msg_color)
        msg_embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar)
        if not follow_up:
            await interaction.response.send_message(embed=msg_embed, delete_after=self.delete_msg_seconds)
        else:
            message = await interaction.followup.send(embed=msg_embed)
            # Manually delete message because .followup.send() does not support it
            if self.delete_msg_seconds:
                await asyncio.sleep(self.delete_msg_seconds)
                await message.delete()


    # Main function for help command
    @app_commands.command(name="help", description="List all avaliable commands")
    async def help(self, interaction: discord.Interaction):
        formatted_description = """
```
Music Cog
/play           - Plays music from a youtube link
/stop           - Stops the music and clears the queue
/list           - Lists all music in the queue
/skip           - Skips the current music
/random         - Randomly adds songs to the queue
/repeat         - Repeatly plays music in the queue
/remove         - Removes specific music in the queue
/pause          - Pauses the currently playing music
/resume         - Resumes the paused music

Help Cog
/help           - List all commands available
/ping           - Show the latency of the bot
/auto_delete    - Set auto-delete seconds for messages
```
        """
        await self.send_embed_msg(interaction, "Command List", formatted_description)


    # Main function for ping command
    @app_commands.command(name="ping", description="Show the latency of the bot")
    async def ping(self, interaction: discord.Interaction):
        await self.send_embed_msg(interaction, f"{self.bot.user.name}'s Latency (ms): ", f"{round(self.bot.latency * 1000)} ms")


    # Main function for set_auto_delete command
    @app_commands.command(name="auto_delete", description="Set auto-delete seconds for messages")
    @app_commands.describe(seconds="Number of seconds before auto-delete")
    async def auto_delete(self, interaction: discord.Interaction, seconds: int):
        # Check valid argument
        if seconds <= 0:
            await self.send_embed_msg(interaction, "ERROR", "Invalid argument! It must be an positive non-zero integer.", msg_color=discord.Color.red())
            return
        # Seconds larger than 1 hour becomes switching off auto-delete
        if seconds > 3600:
            self.delete_msg_seconds = None
            await self.send_embed_msg(interaction, "Auto-Delete Off", "Message auto-delete is now off.")
            return
        # Set number of seconds
        self.delete_msg_seconds = seconds
        await self.send_embed_msg(interaction, "Auto-Delete On", f"Message auto-delete is now set to {self.delete_msg_seconds} seconds.")


    # Main function for sync command
    @app_commands.command(name="sync", description="Sync all slash commands")
    async def sync(self, interaction: discord.Interaction):
        if str(interaction.user.id) != ADMINISTRATOR_ID:
            await self.send_embed_msg(interaction, "ERROR", "You do not have permission to use this command.", msg_color=discord.Color.red)
            return
        try:
            synced_commands = await self.bot.tree.sync()
            print(f"Synced {len(synced_commands)} commands")
            await self.send_embed_msg(interaction, "Sync Successful!", f"Synced {len(synced_commands)} commands.")
        except Exception as e:
            print(f"An error with syncing application commands has occurred: {e}")
            await self.send_embed_msg(interaction, "ERROR", f"An error with syncing application commands has occurred: {e}", msg_color=discord.Color.red)



async def setup(bot):
    await bot.add_cog(Help_cog(bot))