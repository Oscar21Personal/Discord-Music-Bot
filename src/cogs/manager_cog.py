import os
import discord
import re
import asyncio

from discord.ext import commands
from discord import app_commands

class Manager_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.current_album = "Default"

        self.delete_msg_seconds = None      # None: never delete


    @commands.Cog.listener()
    async def on_ready(self):
        print("Manager_cog ready")


    # Helper function to initialise the default album folder
    def initialise_album_dir(self):
        # Ensure the "album" folder exists
        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(base_dir, "../.."))     # Go back to project root directory
        albums_dir = os.path.join(project_root, "album")
        if not os.path.exists(albums_dir):
            os.makedirs(albums_dir)
        # Ensure the "Default" album folder exists
        album_dir = os.path.join(albums_dir, "Default")
        if not os.path.exists(album_dir):
            os.makedirs(album_dir)
        return album_dir
    

    # Helper function to get current album directory
    def get_current_album_dir(self):
        album_dir = self.initialise_album_dir()
        head, _ = os.path.split(album_dir)
        current_dir = os.path.join(head, self.current_album)
        return current_dir


    # Helper function to send embedded messages from ctx
    async def send_embed_msg_ctx(self, ctx, msg_title, msg_description, msg_color=discord.Color.blue()):
        # If auto-delete is on
        if self.delete_msg_seconds:
            msg_description += f"\n\nThis message will be deleted in {self.delete_msg_seconds} seconds."
        # Format the message
        msg_embed = discord.Embed(title=msg_title, description=msg_description, color=msg_color)
        msg_embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar)
        await ctx.send(embed=msg_embed, delete_after=self.delete_msg_seconds)


    # Helper function to send embedded messages from interaction
    async def send_embed_msg_inter(self, interaction, msg_title, msg_description, msg_color=discord.Color.blue(), follow_up=False):
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


async def setup(bot):
    await bot.add_cog(Manager_cog(bot))