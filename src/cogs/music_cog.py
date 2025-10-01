import asyncio
import discord
import os
import re

from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands
from yt_dlp import YoutubeDL

from utils.select_menu import SelectMenu


# Load ADMINISTRATOR_ID from .env file
load_dotenv()
ADMINISTRATOR_ID = os.getenv("ADMINISTRATOR_ID")


class Music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_msg = bot.embed_msg
        self.album_cog = None
        self.music_queue = []
        self.is_playing = False
        self.repeat_mode = False
        self.current_music = ("", "")


    @commands.Cog.listener()
    async def on_ready(self):
        # Obtain an instance of Album_cog
        self.album_cog = self.bot.get_cog("Album_cog")
        if not self.album_cog:
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
        formatted_title = re.sub(pattern, '', title)
        return formatted_title


    # Helper function to search for valid audio to download
    async def validate_audio(self, query):
        ydl_opts_info = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
        }
        # Validate the audio asynchronously
        loop = asyncio.get_event_loop()
        try:
            def _extract(query):
                audio_results = []
                with YoutubeDL(ydl_opts_info) as ydl:
                    # Case 1: Direct YouTube URL
                    if query.startswith("http"):
                        # Extract video info
                        info_dict = ydl.extract_info(query, download=False)
                        audio_results.append({
                            "title": info_dict.get("title", "Unknown Title"),
                            "uploader": info_dict.get("uploader", "Unknown Uploader"),
                            "url": info_dict.get("webpage_url", query)
                        })
                    # Case 2: Search by title
                    else:
                        query = f"ytsearch3:{query}"
                        info_dict = ydl.extract_info(query, download=False)
                        entries = info_dict.get("entries", [])
                        for e in entries:
                            audio_results.append({
                                "title": e.get("title", "Unknown Title"),
                                "uploader": e.get("uploader", "Unknown Uploader"),
                                "url": e.get("webpage_url", "Unknown Url"),
                            })
                return audio_results
            return await loop.run_in_executor(None, lambda: _extract(query))
        except Exception as e:
            print(f"Error occurred at audio validation: {e}")
            return []


    # Helper function to check if music is already downloaded at current album
    def check_music_exist(self, choice):
        album_dir = self.album_cog.get_current_album_dir()
        title = choice["title"]
        formatted_title = self.format_title(title)
        file_path = os.path.join(album_dir, f"{formatted_title}.mp3")
        if os.path.exists(file_path):
            print(f"Audio file already exists: {file_path}")
            return True, file_path
        else:
            return False, file_path


    # Helper function to download and store audio
    async def download_audio(self, file_path, url):
        file_path_no_ext = file_path.removesuffix(".mp3")
        # Options for yt-dlp downloads
        ydl_opts = {
            'format': 'bestaudio[abr>256]/bestaudio/best',
            'outtmpl': f'{file_path_no_ext}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'retries': 10,
            'fragment_retries': 10,
            'continuedl': True,        # resume partial files
            'quiet': True,
            'no_warnings': True,
        }
        # Download the audio to the file_path asynchronously
        loop = asyncio.get_event_loop()
        try:
            def _download():
                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                    print(f"Audio downloaded at: {file_path}")
                return file_path
            return await loop.run_in_executor(None, _download)
        except Exception as e:
            print(f"Error occured at audio download: {e}")
            return None


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
    @app_commands.describe(query="Youtube link or title of the music to be played")
    async def p(self, interaction: discord.Interaction, query: str):
        await self.music_play_handler(interaction, query)


    # Function for music_play command
    @app_commands.command(name="music_play", description="Download and play music from YouTube")
    @app_commands.describe(query="Youtube link or title of the music to be played")
    async def music_play(self, interaction: discord.Interaction, query: str):
        await self.music_play_handler(interaction, query)


    # Main logic for music_play command
    async def music_play_handler(self, interaction, query): 
        # Join user's channel
        user_voice_channel = await self.join_channel(interaction)
        if user_voice_channel is None:
            await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", "You need to be in a voice channel for me to join!", msg_color=discord.Color.red())
            return
        
        # Search beforehand to make sure the audio is valid
        print(f"Validating query: {query}")
        await self.embed_msg.send_embed_msg_inter(interaction, "Validating Query...", f"Searching '{query}'", ephemeral=True)
        audio_results = await self.validate_audio(query)
        if not audio_results:
            await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", "The Youtube link or the search query is invalid.", msg_color=discord.Color.red(), follow_up=True)
            return
        
        # If search using query, allow users to choose which one to download
        if len(audio_results) > 1:
            view = SelectMenu(audio_results)
            await interaction.followup.send("Choose the music to be downloaded:", view=view, ephemeral=True)
            # Wait until user selects or timeout
            await view.wait()
            if view.result is None:
                await self.embed_msg.send_embed_msg_inter(interaction, "Aborting", "No selection made.", follow_up=True, ephemeral=True)
                return
            choice = audio_results[view.result]
        else:
            # If search using link, only gives 1 result
            choice = audio_results[0]

        # Check if music already exists in current album
        is_exist, file_path = self.check_music_exist(choice)
        formatted_title = self.format_title(choice["title"])
        
        # Download the audio
        if not is_exist:
            print(f"Downloading {formatted_title}")
            await self.embed_msg.send_embed_msg_inter(interaction, "Music Downloading...", f"Downloading '{formatted_title}'", follow_up=True, ephemeral=True)
            file_path = await self.download_audio(file_path, choice["url"])
            if not file_path:
                await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", "An error occurred while downloading the audio.", msg_color=discord.Color.red(), follow_up=True)
                return

        # Add audio to list
        self.music_queue.append((file_path, formatted_title))
        await self.embed_msg.send_embed_msg_inter(interaction, "Music Added Successfully!", f"Music *{formatted_title}* added to the queue.", follow_up=True)
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
            await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", "Music queue has already cleared.", msg_color=discord.Color.red())
            return
        # Stop the current song if it's playing
        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice_client.is_playing():
            voice_client.stop()
        # Clear the music queue
        self.music_queue = []
        self.is_playing = False
        print("Stopped the current music and cleared the queue.")
        await self.embed_msg.send_embed_msg_inter(interaction, "Music Queue Cleared!", "Stopped the current music and cleared the queue.")


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
            formatted_description = f"**Current playing**\n \u2794 {self.current_music[1]}\n\n**Following**\n"
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
        await self.embed_msg.send_embed_msg_inter(interaction, "Music Queue:", formatted_description)


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
            await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", "No Music to be skipped.", msg_color=discord.Color.red())
            return
        # Stop the current song if it's playing
        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice_client.is_playing():
            skipped_title = self.current_music[1]
            # Stop the current music and start playing the next music automatically
            # Note: when .stop() is called, it executes the after function in .play(), which automatically calls play_next()
            voice_client.stop()
            if len(self.music_queue) == 0:
                await self.embed_msg.send_embed_msg_inter(interaction, "Music Skipped!", f"Skipped *{skipped_title}*.\nThe queue is now empty.")
                return
            _, next_title = self.music_queue[0]
            await self.embed_msg.send_embed_msg_inter(interaction, "Music Skipped!", f"Skipped *{skipped_title}*.\nStart playing *{next_title}*.")


    # Main function for music_pause command
    @app_commands.command(name="music_pause", description="Pause the currently playing music")
    async def music_pause(self, interaction: discord.Interaction):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await self.embed_msg.send_embed_msg_inter(interaction, "Music Paused!", f"Music *{self.current_music[1]}* is currently paused.")
        else:
            await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", "No music is playing right now.", msg_color=discord.Color.red())


    # Main function for music_resume command
    @app_commands.command(name="music_resume", description="Resume the paused music")
    async def music_resume(self, interaction: discord.Interaction):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await self.embed_msg.send_embed_msg_inter(interaction, "Music Resumed!", f"Music *{self.current_music[1]}* is currently resumed.")
        else:
            await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", "No music is paused right now.", msg_color=discord.Color.red())


    # Main function for music_repeat command
    @app_commands.command(name="music_repeat", description="Toggle repeat mode for queue")
    @app_commands.describe(state="Switch repeat mode on or off")
    async def music_repeat(self, interaction: discord.Interaction, state: bool = None):
        if state != None:
            # If argument does not switch mode
            if (self.repeat_mode == True and state == True) or (self.repeat_mode == False and state == False):
                mode_str = "ON" if self.repeat_mode else "OFF"
                await self.embed_msg.send_embed_msg_inter(interaction, "Mode Status", f"Repeat mode is already **{mode_str}**.")
                return
        # If no argument or input on/off, switch the mode
        self.repeat_mode = not self.repeat_mode
        mode_str = "ON" if self.repeat_mode else "OFF"
        await self.embed_msg.send_embed_msg_inter(interaction, "Mode Switched!", f"Repeat mode is now **{mode_str}**.")
        # If repeat mode on and current song is not in the list
        if self.repeat_mode and (not self.current_music in self.music_queue):
            self.music_queue.append(self.current_music)


    # Music in queue autocomplete callback function
    async def music_queue_autocomplete(self, interaction: discord.Interaction, current: str):
        # List all music in the queue
        all_titles = [title for _, title in self.music_queue]
        # Filter by what the user typed
        choices = [
            app_commands.Choice(name=title, value=title)
            for title in all_titles if current.lower() in title.lower()
        ][:25]  # Max 25 choices
        return choices


    # Main function for music_remove command
    @app_commands.command(name="music_remove", description="Remove a specific music from the queue")
    @app_commands.describe(music_title="Title of the music from 'music_list' command")
    @app_commands.autocomplete(music_title=music_queue_autocomplete)
    async def music_remove(self, interaction: discord.Interaction, music_title: str):
        # Remove inputted music title
        modified_title = self.format_title(music_title)
        index = 0
        is_removed = False
        for tup in self.music_queue:
            if modified_title in tup:
                self.music_queue.pop(index)
                await self.embed_msg.send_embed_msg_inter(interaction, "Music Removed!", f"Music *{tup[1]}* removed from the queue.")
                is_removed = True
                break
            index += 1
        # If nothing is removed, then title does not exist
        if not is_removed:
            await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", f"Music title *{modified_title}* not found.", msg_color=discord.Color.red())


    # Main function for music_add command
    @app_commands.command(name="music_add", description="Add music to current album")
    @app_commands.describe(query="Youtube link or title of the music to be added")
    async def music_add(self, interaction: discord.Interaction, query: str):
        # Search beforehand to make sure the audio is valid
        print(f"Validating query: {query}")
        await self.embed_msg.send_embed_msg_inter(interaction, "Validating Query...", f"Searching '{query}'", ephemeral=True)
        audio_results = await self.validate_audio(query)
        if not audio_results:
            await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", "The Youtube link or the search query is invalid.", msg_color=discord.Color.red(), follow_up=True)
            return
        
        # If search using query, allow users to choose which one to download
        if len(audio_results) > 1:
            view = SelectMenu(audio_results)
            await interaction.followup.send("Choose the music to be downloaded:", view=view, ephemeral=True)
            # Wait until user selects or timeout
            await view.wait()
            if view.result is None:
                await self.embed_msg.send_embed_msg_inter(interaction, "Aborting", "No selection made.", follow_up=True, ephemeral=True)
                return
            choice = audio_results[view.result]
        else:
            # If search using link, only gives 1 result
            choice = audio_results[0]

        # Check if music already exists in current album
        is_exist, file_path = self.check_music_exist(choice)
        formatted_title = self.format_title(choice["title"])
        
        # Download the audio
        if not is_exist:
            print(f"Downloading {formatted_title}")
            await self.embed_msg.send_embed_msg_inter(interaction, "Music Downloading...", f"Downloading '{formatted_title}'", follow_up=True, ephemeral=True)
            file_path = await self.download_audio(file_path, choice["url"])
            if not file_path:
                await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", "An error occurred while downloading the audio.", msg_color=discord.Color.red(), follow_up=True)
                return
        await self.embed_msg.send_embed_msg_inter(interaction, "Music Added Successfully!", f"Music *{formatted_title}* added to current album.", follow_up=True)


    # Music in album autocomplete callback function
    async def music_album_autocomplete(self, interaction: discord.Interaction, current: str):
        # List all music in the album
        album_dir = self.album_cog.get_current_album_dir()
        all_titles = [file_name.removesuffix(".mp3") for file_name in os.listdir(album_dir)]
        # Filter by what the user typed
        choices = [
            app_commands.Choice(name=title, value=title)
            for title in all_titles if current.lower() in title.lower()
        ][:25]  # Max 25 choices
        return choices


    # Main function for music_delete command
    @app_commands.command(name="music_delete", description="Remove music from current album")
    @app_commands.describe(music_title="Title of the music from 'music_list' command")
    @app_commands.autocomplete(music_title=music_album_autocomplete)
    async def music_delete(self, interaction: discord.Interaction, music_title: str):
        modified_title = self.format_title(music_title)
        # Only administrator can delete music
        if str(interaction.user.id) != ADMINISTRATOR_ID:
            await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", "You do not have permission to use this command.", msg_color=discord.Color.red())
            return
        # Reject request if music is in the queue or current playing
        if modified_title == self.current_music[1]:
            await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", f"Music *{modified_title}* is currently playing.", msg_color=discord.Color.red())
            return
        for tup in self.music_queue:
            if modified_title in tup:
                await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", f"Music *{modified_title}* is still in the music queue.", msg_color=discord.Color.red())
                return
        # Delete the music from current album
        album_dir = self.album_cog.get_current_album_dir()
        file_to_delete = f"{modified_title}.mp3"
        file_path = os.path.join(album_dir, file_to_delete)
        if os.path.exists(file_path):
            os.remove(file_path)
            await self.embed_msg.send_embed_msg_inter(interaction, "Music Deleted!", f"Music *{modified_title}* deleted from the current album.")
        else:
            await self.embed_msg.send_embed_msg_inter(interaction, "ERROR", f"Music *{modified_title}* does not exist in current album.", msg_color=discord.Color.red())


async def setup(bot):
    await bot.add_cog(Music_cog(bot))