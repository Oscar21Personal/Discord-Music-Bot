import os
import discord
import asyncio
import random

from discord.ext import commands
from discord import app_commands


class Album_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        

    @commands.Cog.listener()
    async def on_ready(self):
        # await self.bot.wait_until_ready()
        # self.initialise_album_dir()
        # # Obtain an instance of Help_cog and Music_cog
        # self.help_cog = self.bot.get_cog("Help_cog")
        # self.music_cog = self.bot.get_cog("Music_cog")
        # if not self.help_cog:
        #     print("Error: Help_cog not found")
        # elif not self.music_cog:
        #     print("Error: Music_cog not found")
        # else:
        #     print("Album_cog ready and linked with Help_cog and Music_cog")
        print("Album_cog ready")
        

    


#     # Main function for album_create command
#     @app_commands.command(name="album_create", description="Create a new album")
#     async def album_create(self, interaction: discord.Interaction):
#         await self.help_cog.send_embed_msg_inter(interaction, f"TODO", f"DO STH")


#     # Main function for album_tracks command
#     @app_commands.command(name="album_tracks", description="List all tracks in the current album")
#     async def album_tracks(self, interaction: discord.Interaction):
#         await self.help_cog.send_embed_msg_inter(interaction, f"TODO", f"DO STH")

    
#     # Main function for album_list command
#     @app_commands.command(name="album_list", description="List all albums")
#     async def album_list(self, interaction: discord.Interaction):
#         await self.help_cog.send_embed_msg_inter(interaction, f"TODO", f"DO STH")

    
#     # Main function for album_switch command
#     @app_commands.command(name="album_switch", description="Switch to another album")
#     async def album_switch(self, interaction: discord.Interaction):
#         await self.help_cog.send_embed_msg_inter(interaction, f"TODO", f"DO STH")

    
#     # Main function for album_add command
#     @app_commands.command(name="album_add", description="Add a track to the current album")
#     async def album_add(self, interaction: discord.Interaction):
#         await self.help_cog.send_embed_msg_inter(interaction, f"TODO", f"DO STH")


#     # Main function for album_remove command
#     @app_commands.command(name="album_remove", description="Remove a track from the current album")
#     async def album_remove(self, interaction: discord.Interaction):
#         await self.help_cog.send_embed_msg_inter(interaction, f"TODO", f"DO STH")


#     # Main function for album_play command
#     @app_commands.command(name="album_play", description="Add the current album to the queue")
#     @app_commands.describe(number_of_songs="Number of songs in the album being added to the queue", is_random="Randomise the album order or not")
#     async def album_play(self, interaction: discord.Interaction, number_of_songs: int = 99999, is_random: bool = True):
#         # Join user's channel
#         user_voice_channel = await self.join_channel(interaction)
#         if user_voice_channel is None:
#             await self.help_cog.send_embed_msg_inter(interaction, "ERROR", "You need to be in a voice channel for me to join!", msg_color=discord.Color.red())
#             return
#         # Check if the number of songs is valid
#         if number_of_songs <= 0:
#             await self.help_cog.send_embed_msg_inter(interaction, "ERROR", "Invalid argument! It must be an positive non-zero integer.", msg_color=discord.Color.red())
#             return
#         # Get current album folder
#         album_dir = self.get_current_album_dir()
#         # Extract all mp3 files
#         mp3_files = []
#         for file_name in os.listdir(album_dir):
#             file_path = os.path.join(album_dir, file_name)
#             if os.path.isfile(file_path) and file_name.lower().endswith(".mp3"):
#                 mp3_files.append((file_path, file_name.removesuffix(".mp3")))
#         # If no arguments, number_of_songs=99999, load 100 music
#         # Limit the maximum number of songs to 100
#         number_of_songs = min(number_of_songs, len(mp3_files), 100)
#         # Select the specified number of files
#         if is_random:
#             selected_mp3_files = random.sample(mp3_files, number_of_songs)
#         else:
#             selected_mp3_files = mp3_files[:number_of_songs]    # Take the first `number_of_songs` in order
#         # Add the selected music to the queue
#         formatted_description = "Music added to the queue:\n"
#         for file_path, title in selected_mp3_files:
#             formatted_description += f" - {title}\n"
#             self.music_cog.music_queue.append((file_path, title))
#         formatted_description = formatted_description[:-1]      # Removes the last character '\n'
#         await self.help_cog.send_embed_msg_inter(interaction, "Music Loaded!", formatted_description)
#         # Start playing the audio
#         if not self.music_cog.is_playing:
#             self.music_cog.play_next(interaction)
#             self.music_cog.is_playing = True


#     # Main function for album_rename command
#     @app_commands.command(name="album_rename", description="Rename an album")
#     async def album_rename(self, interaction: discord.Interaction):
#         await self.help_cog.send_embed_msg_inter(interaction, f"TODO", f"DO STH")


#     # Main function for album_delete command
#     @app_commands.command(name="album_delete", description="Delete an album")
#     async def album_delete(self, interaction: discord.Interaction):
#         await self.help_cog.send_embed_msg_inter(interaction, f"TODO", f"DO STH")
        

async def setup(bot):
    await bot.add_cog(Album_cog(bot))