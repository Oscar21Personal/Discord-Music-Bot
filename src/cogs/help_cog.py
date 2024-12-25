import discord
import asyncio

from discord.ext import commands
from discord import app_commands

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
        # msg_embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar)
        if not follow_up:
            await interaction.response.send_message(embed=msg_embed, delete_after=self.delete_msg_seconds)
        else:
            message = await interaction.followup.send(embed=msg_embed)
            # Manually delete message because .followup.send() does not support it
            if self.delete_msg_seconds:
                await asyncio.sleep(self.delete_msg_seconds)
                await message.delete()


    # Main function for ping command
    @app_commands.command(name="ping", description="Show the latency of the bot")
    async def ping(self, interaction: discord.Interaction):
        await self.send_embed_msg(interaction, f"{self.bot.user.name}'s Latency (ms): ", f"{round(self.bot.latency * 1000)} ms")


    # Main function for set_auto_delete command
    @app_commands.command(name="set_auto_delete", description="Set auto-delete seconds for bot messages")
    @app_commands.describe(seconds="Number of seconds to auto-delete messages from the bot")
    async def set_auto_delete(self, interaction: discord.Interaction, seconds: int):
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



async def setup(bot):
    await bot.add_cog(Help_cog(bot))