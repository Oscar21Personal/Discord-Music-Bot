import os
import discord
import re
import random
import shutil

from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands


# Load ADMINISTRATOR_ID from .env file
load_dotenv()
ADMINISTRATOR_ID = os.getenv("ADMINISTRATOR_ID")


class Album_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_msg = bot.embed_msg
        self.music_cog = None
        self.current_album = "Default"
        

    @commands.Cog.listener()
    async def on_ready(self):
        self.initialise_album_dir()
        # Obtain an instance of Music_cog
        self.music_cog = self.bot.get_cog("Music_cog")
        if not self.music_cog:
            print("Error: Music_cog not found when linking to Album_cog")
        else:
            print("Album_cog ready!")
        

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
        parent_dir = os.path.dirname(album_dir)
        current_dir = os.path.join(parent_dir, self.current_album)
        # Ensure the album folder exists
        if not os.path.exists(current_dir):
            os.makedirs(current_dir)
        return current_dir
    

    def format_album_title(self, title):
        pattern = r'[^0-9a-zA-Z\u4e00-\u9fff\u3040-\u30ff\u31f0-\u31ff\u3400-\u4DBF\u4E00-\u9FFF]'
        modified_title = re.sub(pattern, '', title)
        return modified_title.lower().capitalize()


    # Main function for album_create command
    @app_commands.command(name="album_create", description="Create a new album")
    async def album_create(self, interaction: discord.Interaction, album_name: str):
        album_name = self.format_album_title(album_name)
        current_dir = self.get_current_album_dir()
        parent_dir = os.path.dirname(current_dir)
        new_dir = os.path.join(parent_dir, album_name)
        if os.path.isdir(new_dir):
            # Reject request if directory already exists
            await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", f"Album **{album_name}** already exists!", msg_color=discord.Color.red())
            return
        else:
            os.makedirs(new_dir)
            await self.embed_msg.send_embed_msg_inter(interaction, "Album Created!", f"Album **{album_name}** created successfully. Current Album is switched to **{album_name}**")
        self.current_album = album_name


    # Main function for album_tracks command
    @app_commands.command(name="album_tracks", description="List all tracks in the current album")
    async def album_tracks(self, interaction: discord.Interaction):
        # Get current album folder
        album_dir = self.get_current_album_dir()
        # Extract all mp3 file titles in current album
        formatted_description = ""
        max_length = 50
        i = 0
        for file_name in os.listdir(album_dir):
            # Prevent showing a really long message
            if i >= max_length:
                formatted_description += "More songs following...\n"
                break
            file_path = os.path.join(album_dir, file_name)
            if os.path.isfile(file_path) and file_name.lower().endswith(".mp3"):
                title = file_name.removesuffix(".mp3")
                formatted_description += f" - {title}\n"
                i += 1
        formatted_description = formatted_description[:-1]      # Removes the last character '\n'
        await self.embed_msg.send_embed_msg_inter(interaction, "Current Album Tracks:", formatted_description)

    
    # Main function for album_list command
    @app_commands.command(name="album_list", description="List all albums")
    async def album_list(self, interaction: discord.Interaction):
        album_dir = self.get_current_album_dir()
        parent_dir = os.path.dirname(album_dir)
        # Extract all album titles
        formatted_description = f"**Current album**\n \u2794 {self.current_album}\n\n**Other Album**\n"
        for folder_name in os.listdir(parent_dir):
            folder_path = os.path.join(parent_dir, folder_name)
            if os.path.isdir(folder_path):
                if folder_name == self.current_album:
                    continue
                formatted_description += f" - {folder_name}\n"
        formatted_description = formatted_description[:-1]      # Removes the last character '\n'
        await self.embed_msg.send_embed_msg_inter(interaction, "Album List:", formatted_description)


    # Album autocomplete callback function
    async def album_autocomplete(self, interaction: discord.Interaction, current: str):
        # List directories in albums folder
        albums_root = os.path.dirname(self.get_current_album_dir())
        all_albums = [f for f in os.listdir(albums_root) if os.path.isdir(os.path.join(albums_root, f))]
        # Filter by what the user typed
        choices = [
            app_commands.Choice(name=album, value=album)
            for album in all_albums if current.lower() in album.lower()
        ][:25]  # Max 25 choices
        return choices

    
    # Main function for album_switch command
    @app_commands.command(name="album_switch", description="Switch to another album")
    @app_commands.autocomplete(album_name=album_autocomplete)
    async def album_switch(self, interaction: discord.Interaction, album_name: str):
        album_name = self.format_album_title(album_name)
        current_dir = self.get_current_album_dir()
        parent_dir = os.path.dirname(current_dir)
        switch_dir = os.path.join(parent_dir, album_name)
        if not os.path.isdir(switch_dir):
            await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", f"Album **{album_name}** does not exist!", msg_color=discord.Color.red())
            return
        self.current_album = album_name
        await self.embed_msg.send_embed_msg_inter(interaction, "Album Switched!", f"Current album is now switched to **{album_name}**")


    # Main function for album_play command
    @app_commands.command(name="album_play", description="Add the current album to the queue")
    @app_commands.describe(number_of_songs="Number of songs in the album being added to the queue", is_random="Randomise the album order or not")
    async def album_play(self, interaction: discord.Interaction, number_of_songs: int = 99999, is_random: bool = True):
        # Join user's channel
        user_voice_channel = await self.music_cog.join_channel(interaction)
        if user_voice_channel is None:
            await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", "You need to be in a voice channel for me to join!", msg_color=discord.Color.red())
            return
        # Check if the number of songs is valid
        if number_of_songs <= 0:
            await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", "Invalid argument! It must be an positive non-zero integer.", msg_color=discord.Color.red())
            return
        # Get current album folder
        album_dir = self.get_current_album_dir()
        # Extract all mp3 files
        mp3_files = []
        for file_name in os.listdir(album_dir):
            file_path = os.path.join(album_dir, file_name)
            if os.path.isfile(file_path) and file_name.lower().endswith(".mp3"):
                mp3_files.append((file_path, file_name.removesuffix(".mp3")))
        # If no arguments, number_of_songs=99999, load 100 music
        # Limit the maximum number of songs to 100
        number_of_songs = min(number_of_songs, len(mp3_files), 100)
        # Select the specified number of files
        if is_random:
            selected_mp3_files = random.sample(mp3_files, number_of_songs)
        else:
            selected_mp3_files = mp3_files[:number_of_songs]    # Take the first `number_of_songs` in order
        # Add the selected music to the queue
        formatted_description = "Music added to the queue:\n"
        for file_path, title in selected_mp3_files:
            formatted_description += f" - {title}\n"
            self.music_cog.music_queue.append((file_path, title))
        formatted_description = formatted_description[:-1]      # Removes the last character '\n'
        await self.embed_msg.send_embed_msg_inter(interaction, "Music Loaded!", formatted_description)
        # Start playing the audio
        if not self.music_cog.is_playing:
            self.music_cog.play_next(interaction)
            self.music_cog.is_playing = True


    # Main function for album_rename command
    @app_commands.command(name="album_rename", description="Rename current album")
    async def album_rename(self, interaction: discord.Interaction, new_album_name: str):
        new_album_name = self.format_album_title(new_album_name)
        # Reject request if renaming "Default"
        if self.current_album == "Default":
            await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", f"Album **Default** cannot be renamed!", msg_color=discord.Color.red())
            return
        current_dir = self.get_current_album_dir()
        parent_dir = os.path.dirname(current_dir)
        new_dir = os.path.join(parent_dir, new_album_name)
        # Reject request if directory already exists
        if os.path.isdir(new_dir):
            await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", f"Album **{new_album_name}** already exists!", msg_color=discord.Color.red())
            return
        os.rename(current_dir, new_dir)
        self.current_album = new_album_name
        await self.embed_msg.send_embed_msg_inter(interaction, "Album Renamed!", f"Current album is now renamed to **{new_album_name}**")


    # Main function for album_delete command
    @app_commands.command(name="album_delete", description="Delete an album")
    @app_commands.autocomplete(album_name=album_autocomplete)
    async def album_delete(self, interaction: discord.Interaction, album_name: str):
        album_name = self.format_album_title(album_name)
        # Only administrator can delete albums
        if str(interaction.user.id) != ADMINISTRATOR_ID:
            await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", "You do not have permission to use this command.", msg_color=discord.Color.red())
            return
        # Reject request if deleting "Default"
        if album_name == "Default":
            await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", f"Album **Default** cannot be deleted!", msg_color=discord.Color.red())
            return
        # Reject request if deleting current album
        if self.current_album == album_name:
            await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", f"You are currently at album **{self.current_album}**! You need to switch to another album first!", msg_color=discord.Color.red())
            return
        # Reject request if directory does not exsist
        current_dir = self.get_current_album_dir()
        parent_dir = os.path.dirname(current_dir)
        delete_dir = os.path.join(parent_dir, album_name)
        if not os.path.isdir(delete_dir):
            await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", f"Album **{album_name}** does not exist!", msg_color=discord.Color.red())
            return
        # Deletes the directory and all its contents
        shutil.rmtree(delete_dir)
        await self.embed_msg.send_embed_msg_inter(interaction, "Album Deleted!", f"Album **{album_name}** and its tracks deleted successfully!")
        

async def setup(bot):
    await bot.add_cog(Album_cog(bot))