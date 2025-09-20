import os
import discord
import asyncio

from discord.ext import commands
from discord import app_commands


class Album_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.help_cog = None


    @commands.Cog.listener()
    async def on_ready(self):
        print("Album_cog ready")
        # Obtain an instance of Help_cog
        self.help_cog = self.bot.get_cog("Help_cog")
        while not self.help_cog:
            print("Error: Help_cog is not connected.")
            self.help_cog = self.bot.get_cog("Help_cog")


    # Main function for album_create command
    @app_commands.command(name="album_create", description="Creates a new album")
    async def album_create(self, interaction: discord.Interaction):
        await self.help_cog.send_embed_msg_inter(interaction, f"TODO", f"DO STH")


    # Main function for album_list command
    @app_commands.command(name="album_list", description="Lists all albums")
    async def album_list(self, interaction: discord.Interaction):
        await self.help_cog.send_embed_msg_inter(interaction, f"TODO", f"DO STH")

    
    # Main function for album_switch command
    @app_commands.command(name="album_switch", description="Switches to another album")
    async def album_switch(self, interaction: discord.Interaction):
        await self.help_cog.send_embed_msg_inter(interaction, f"TODO", f"DO STH")

    
    # Main function for album_play command
    @app_commands.command(name="album_play", description="Adds the current album to the queue")
    async def album_play(self, interaction: discord.Interaction):
        await self.help_cog.send_embed_msg_inter(interaction, f"TODO", f"DO STH")
        

async def setup(bot):
    await bot.add_cog(Album_cog(bot))