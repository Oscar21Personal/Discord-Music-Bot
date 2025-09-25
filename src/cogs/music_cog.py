import os
import discord
import re

from discord.ext import commands
from discord import app_commands
from yt_dlp import YoutubeDL

class Music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.help_cog = None
        self.album_cog = None
        self.music_queue = []
        self.is_playing = False
        self.repeat_mode = False
        self.current_music = ("", "")


    @commands.Cog.listener()
    async def on_ready(self):
        # Obtain an instance of Help_cog and Album_cog
        self.help_cog = self.bot.get_cog("Help_cog")
        self.album_cog = self.bot.get_cog("Album_cog")
        if not self.help_cog:
            print("Error: Help_cog not found when linking to Music_cog")
        elif not self.album_cog:
            print("Error: Album_cog not found when linking to Music_cog")
        else:
            print("Music_cog ready!")
        

    # Helper function to join user's channel
    async def join_channel(self, interaction): 
        # If user is not in a voice channel
        if interaction.user.voice is None:
            return None
        # Get the voice channel the author is in
        user_voice_channel = interaction.user.voice.channel
        # Check if the bot is already in a voice channel
        bot_voice_channel = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if bot_voice_channel is None:
            # If bot is not in any channel, join the author's channel
            await user_voice_channel.connect()
        elif bot_voice_channel.channel != user_voice_channel:
            # If bot is in a different channel, move to the author's channel
            await bot_voice_channel.move_to(user_voice_channel)
        return user_voice_channel
    

    # Helper function to format music title
    def format_title(self, title):
        pattern = r'[^0-9a-zA-Z\u4e00-\u9fff\u3040-\u30ff\u31f0-\u31ff\u3400-\u4DBF\u4E00-\u9FFF]'
        modified_title = re.sub(pattern, '', title)
        return modified_title


    # Helper function to download and store audio
    def download_audio(self, query):
        # Initialise album directory
        album_dir = self.album_cog.get_current_album_dir()
        # Extract video info first
        ydl_opts_info = {
            'format': 'bestaudio/best',
            'quiet': True,
        }
        modified_title = ""
        file_path = ""
        with YoutubeDL(ydl_opts_info) as ydl:
            info_dict = ydl.extract_info(query, download=False)     # Don't download yet, just extract info
            # Format the title
            title = info_dict.get("title", "Unknown Title")
            modified_title = self.format_title(title)
            file_path = os.path.join(album_dir, f"{modified_title}.mp3")
            # Check if the file already exists in the "album" folder
            if os.path.exists(file_path):
                print(f"Audio file already exists: {file_path}")
                return file_path, modified_title
        # Options for yt-dlp downloads
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{album_dir}/{modified_title}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
        }
        # Download the audio to the file_path
        with YoutubeDL(ydl_opts) as ydl:
            # If the file does not exist, proceed to download the audio
            ydl.download([query])
            print(f"Audio downloaded at: {file_path}")
            return file_path, modified_title


    # Helper function to play the next song in the music queue
    def play_next(self, interaction):
        if len(self.music_queue) > 0:
            # Remove the music from list
            file_path, title = self.music_queue.pop(0)
            self.current_music = (file_path, title)
            print(f"Playing {title}")
            # If repeat mode is on, add the song back to queue
            if self.repeat_mode:
                self.music_queue.append((file_path, title))
            # Play the music
            voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            if voice_client.is_connected():
                voice_client.play(discord.FFmpegPCMAudio(source=file_path), after=lambda e: self.play_next(interaction))
        else:
            self.is_playing = False
            self.current_music = ("", "")


    # Aliase for music_play command
    @app_commands.command(name="p", description="Aliase for /music_play")
    @app_commands.describe(link="Youtube link to be played")
    async def p(self, interaction: discord.Interaction, link: str):
        await self.music_play_handler(interaction, link)


    # Function for music_play command
    @app_commands.command(name="music_play", description="Download and play music from YouTube")
    @app_commands.describe(link="Youtube link to be played")
    async def music_play(self, interaction: discord.Interaction, link: str):
        await self.music_play_handler(interaction, link)


    # Main logic for music_play command
    async def music_play_handler(self, interaction, link): 
        # Join user's channel
        user_voice_channel = await self.join_channel(interaction)
        if user_voice_channel is None:
            await self.help_cog.send_embed_msg_inter(interaction, "ERROR", "You need to be in a voice channel for me to join!", msg_color=discord.Color.red())
            return
        # Download the audio
        try:
            print(f"Downloading {link}")
            await self.help_cog.send_embed_msg_inter(interaction, "Music Downloading...", f"Downloading {link}")
            file_path, title = self.download_audio(link)
        except Exception as e:
            await self.help_cog.send_embed_msg_inter(interaction, "ERROR", "An error occurred while downloading the audio.", msg_color=discord.Color.red())
            return
        # Add audio to list
        self.music_queue.append((file_path, title))
        await self.help_cog.send_embed_msg_inter(interaction, "Music Added Successfully!", f"Music {title} added to the queue.", follow_up=True)
        # Start playing the audio
        if not self.is_playing:
            self.play_next(interaction)
            self.is_playing = True


    # Aliase for music_clear command
    @app_commands.command(name="c", description="Aliase for /music_clear")
    async def c(self, interaction: discord.Interaction):
        await self.music_clear_handler(interaction)


    # Function for music_clear command
    @app_commands.command(name="music_clear", description="Clear all music from the queue")
    async def music_clear(self, interaction: discord.Interaction):
        await self.music_clear_handler(interaction)


    # Main logic for music_clear command
    async def music_clear_handler(self, interaction):
        # Check if the music has already stopped
        if not self.is_playing:
            await self.help_cog.send_embed_msg_inter(interaction, "ERROR", "Music queue has already cleared.", msg_color=discord.Color.red())
            return
        # Stop the current song if it's playing
        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice_client.is_playing():
            voice_client.stop()
        # Clear the music queue
        self.music_queue = []
        self.is_playing = False
        print("Stopped the current music and cleared the queue.")
        await self.help_cog.send_embed_msg_inter(interaction, "Music Queue Cleared!", "Stopped the current music and cleared the queue.")


    # Aliase for music_list command
    @app_commands.command(name="l", description="Aliase for /music_list")
    async def l(self, interaction: discord.Interaction):
        await self.music_list_handler(interaction)


    # Function for music_list command
    @app_commands.command(name="music_list", description="List all music in the queue")
    async def music_list(self, interaction: discord.Interaction):
        await self.music_list_handler(interaction)


    # Main logic for music_list command
    async def music_list_handler(self, interaction):
        formatted_description = ""
        max_length = 50
        i = 0
        if self.is_playing:
            formatted_description = f"**Current playing**\n \u2794 {self.current_music[1]}\n\n"
        for file_path, title in self.music_queue:
            # Prevent showing a really long message
            if i >= max_length:
                formatted_description += "More songs following...\n"
                break
            # Format the message
            formatted_description += f" - {title}\n"
            i += 1
        formatted_description = formatted_description[:-1]  # Removes the last character '\n'
        # Send the message
        await self.help_cog.send_embed_msg_inter(interaction, "Music Queue:", formatted_description)


    # Aliase for music_skip command
    @app_commands.command(name="s", description="Aliase for /music_skip")
    async def s(self, interaction: discord.Interaction):
        await self.music_skip_handler(interaction)


    # Function for music_skip command
    @app_commands.command(name="music_skip", description="Skip the current music")
    async def music_skip(self, interaction: discord.Interaction):
        await self.music_skip_handler(interaction)


    # Main logic for music_skip command
    async def music_skip_handler(self, interaction):
        # Check if the bot is playing
        if not self.is_playing:
            await self.help_cog.send_embed_msg_inter(interaction, "ERROR", "No Music to be skipped.", msg_color=discord.Color.red())
            return
        # Stop the current song if it's playing
        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice_client.is_playing():
            # Stop the current music and start playing the next music automatically
            # Note: when .stop() is called, it executes the after function in .play(), which automatically calls play_next()
            voice_client.stop()
            if len(self.music_queue) == 0:
                await self.help_cog.send_embed_msg_inter(interaction, "Music Skipped!", f"The queue is now empty.")
                return
            file_path, title = self.music_queue[0]
            await self.help_cog.send_embed_msg_inter(interaction, "Music Skipped!", f"Skipped current music. Start playing {title}.")


    # Main function for music_pause command
    @app_commands.command(name="music_pause", description="Pause the currently playing music")
    async def music_pause(self, interaction: discord.Interaction):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await self.help_cog.send_embed_msg_inter(interaction, "Music Paused!", f"Music {self.current_music[1]} is currently paused.")
        else:
            await self.help_cog.send_embed_msg_inter(interaction, "ERROR", "No music is playing right now.", msg_color=discord.Color.red())


    # Main function for music_resume command
    @app_commands.command(name="music_resume", description="Resume the paused music")
    async def music_resume(self, interaction: discord.Interaction):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await self.help_cog.send_embed_msg_inter(interaction, "Music Resumed!", f"Music {self.current_music[1]} is currently resumed.")
        else:
            await self.help_cog.send_embed_msg_inter(interaction, "ERROR", "No music is paused right now.", msg_color=discord.Color.red())


    # Main function for music_repeat command
    @app_commands.command(name="music_repeat", description="Toggle repeat mode for queue")
    @app_commands.describe(state="Switch repeat mode on or off")
    async def music_repeat(self, interaction: discord.Interaction, state: bool = None):
        if state != None:
            # If argument does not switch mode
            if (self.repeat_mode == True and state == True) or (self.repeat_mode == False and state == False):
                mode_str = "ON" if self.repeat_mode else "OFF"
                await self.help_cog.send_embed_msg_inter(interaction, "Mode Status", f"Repeat mode is already **{mode_str}**.")
                return
        # If no argument or input on/off, switch the mode
        self.repeat_mode = not self.repeat_mode
        mode_str = "ON" if self.repeat_mode else "OFF"
        await self.help_cog.send_embed_msg_inter(interaction, "Mode Switched!", f"Repeat mode is now **{mode_str}**.")
        # If repeat mode on and current song is not in the list
        if self.repeat_mode and (not self.current_music in self.music_queue):
            self.music_queue.append(self.current_music)


    # Main function for music_remove command
    @app_commands.command(name="music_remove", description="Remove a specific music from the queue")
    @app_commands.describe(music_title="Title of the music from 'music_list' command")
    async def music_remove(self, interaction: discord.Interaction, music_title: str):
        # Remove inputted music title
        modified_title = self.format_title(music_title)
        index = 0
        is_removed = False
        for tup in self.music_queue:
            if modified_title in tup:           # tup: (file_name, title)
                self.music_queue.pop(index)
                await self.help_cog.send_embed_msg_inter(interaction, "Music Removed!", f"Music {tup[1]} removed from the queue.")
                is_removed = True
                break
            index += 1
        # If nothing is removed, then title does not exist
        if not is_removed:
            await self.help_cog.send_embed_msg_inter(interaction, "ERROR", f"Music title '{modified_title}' not found.", msg_color=discord.Color.red())


async def setup(bot):
    await bot.add_cog(Music_cog(bot))