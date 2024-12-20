import os
import discord
import re
import random

from discord.ext import commands
from yt_dlp import YoutubeDL

class Music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music_queue = []
        self.is_playing = False
        self.repeat_mode = False
        self.current_music = ("", "")
        self.help_cog = None
        

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Music_cog ready. Bot connected as {self.bot.user}')
        # Obtain an instance of Help_cog
        self.help_cog = self.bot.get_cog("Help_cog")
        while not self.help_cog:
            print("Error: Help_cog is not connected.")
            self.help_cog = self.bot.get_cog("Help_cog")
        

    # Helper function to join user's channel
    async def join_channel(self, ctx): 
        # If user is not in a voice channel
        if ctx.author.voice is None:
            return None
        # Get the voice channel the author is in
        user_voice_channel = ctx.author.voice.channel
        # Check if the bot is already in a voice channel
        bot_voice_channel = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if bot_voice_channel is None:
            # If bot is not in any channel, join the author's channel
            await user_voice_channel.connect()
        elif bot_voice_channel.channel != user_voice_channel:
            # If bot is in a different channel, move to the author's channel
            await bot_voice_channel.move_to(user_voice_channel)
        return user_voice_channel


    # Helper function to initialise the "music" folder
    def initialise_music_dir(self):
        # Ensure the "music" folder exists
        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(base_dir, "../.."))     # Go back to project root directory
        music_dir = os.path.join(project_root, "music")
        if not os.path.exists(music_dir):
            os.makedirs(music_dir)
        return music_dir
    

    # Helper function to format music title
    def format_title(self, title):
        pattern = r'[^0-9a-zA-Z\u4e00-\u9fff\u3040-\u30ff\u31f0-\u31ff\u3400-\u4DBF\u4E00-\u9FFF]'
        modified_title = re.sub(pattern, '', title)
        return modified_title


    # Helper function to download and store audio
    def download_audio(self, query):
        # Initialise "music" folder
        music_dir = self.initialise_music_dir()
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
            file_path = os.path.join(music_dir, f"{modified_title}.mp3")
            # Check if the file already exists in the "music" folder
            if os.path.exists(file_path):
                print(f"Audio file already exists: {file_path}")
                return file_path, modified_title
        # Options for yt-dlp downloads
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{music_dir}/{modified_title}.%(ext)s',
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
    def play_next(self, ctx):
        if len(self.music_queue) > 0:
            # Remove the music from list
            file_path, title = self.music_queue.pop(0)
            self.current_music = (file_path, title)
            print(f"Playing {title}")
            # If repeat mode is on, add the song back to queue
            if self.repeat_mode:
                self.music_queue.append((file_path, title))
            # Play the music
            voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if voice_client.is_connected():
                voice_client.play(discord.FFmpegPCMAudio(source=file_path), after=lambda e: self.play_next(ctx))
        else:
            self.is_playing = False
            self.current_music = ("", "")


    # Main function for play command
    @commands.command(name="play", aliases=["p","Play"], help="- Plays a selected music from youtube link")
    async def play(self, ctx, *args):
        # Check if a link is given
        query = " ".join(args)
        if query == "":
            await self.help_cog.send_embed_msg(ctx, "ERROR", "Music link cannot be empty.", msg_color=discord.Color.red())
            return
        # Join user's channel
        user_voice_channel = await self.join_channel(ctx)
        if user_voice_channel is None:
            await self.help_cog.send_embed_msg(ctx, "ERROR", "You need to be in a voice channel for me to join!", msg_color=discord.Color.red())
            return
        # Download the audio
        try:
            print(f"Downloading {query}")
            await self.help_cog.send_embed_msg(ctx, "Music Downloading...", f"Downloading {query}")
            file_path, title = self.download_audio(query)
        except Exception as e:
            await self.help_cog.send_embed_msg(ctx, "ERROR", "An error occurred while downloading the audio.", msg_color=discord.Color.red())
            return
        # Add audio to list
        self.music_queue.append((file_path, title))
        await self.help_cog.send_embed_msg(ctx, "Music Added Successfully!", f"Music {title} added to the queue.")
        # Start playing the audio
        if not self.is_playing:
            self.play_next(ctx)
            self.is_playing = True


    # Main function for stop command
    @commands.command(name="stop", aliases=["Stop"], help="- Stops the music and clears the queue")
    async def stop(self, ctx):
        # Check if the music has already stopped
        if not self.is_playing:
            await self.help_cog.send_embed_msg(ctx, "ERROR", "Music has already stopped.", msg_color=discord.Color.red())
            return
        # Stop the current song if it's playing
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice_client.is_playing():
            voice_client.stop()
        # Clear the music queue
        self.music_queue = []
        self.is_playing = False
        print("Stopped the current music and cleared the queue.")
        await self.help_cog.send_embed_msg(ctx, "Music Stopped!", "Stopped the current music and cleared the queue.")


    # Main function for list command
    @commands.command(name="list", aliases=["l","List"], help="- Lists all music in the queue")
    async def list(self, ctx):
        max_length = 80
        i = 0
        formatted_description = ""
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
        await self.help_cog.send_embed_msg(ctx, "Music Queue:", formatted_description)


    # Main function for skip command
    @commands.command(name="skip", aliases=["Skip"], help="- Skips the current music and plays the next music in the queue")
    async def skip(self, ctx):
        # Check if the bot is playing
        if not self.is_playing:
            await self.help_cog.send_embed_msg(ctx, "ERROR", "No Music to be skipped.", msg_color=discord.Color.red())
            return
        # Stop the current song if it's playing
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice_client.is_playing():
            # Stop the current music and start playing the next music automatically
            # Note: when .stop() is called, it executes the after function in .play(), which automatically calls play_next()
            voice_client.stop()
            if len(self.music_queue) == 0:
                await self.help_cog.send_embed_msg(ctx, "Music Skipped!", f"The queue is now empty.")
                return
            file_path, title = self.music_queue[0]
            await self.help_cog.send_embed_msg(ctx, "Music Skipped!", f"Skipped current music. Start playing {title}.")


    # Main function for random command
    @commands.command(name="random", aliases=["Random"], help="- Randomly adds songs from the download directory into the queue")
    async def random(self, ctx, *args):
        # Join user's channel
        user_voice_channel = await self.join_channel(ctx)
        if user_voice_channel is None:
            await self.help_cog.send_embed_msg(ctx, "ERROR", "You need to be in a voice channel for me to join!", msg_color=discord.Color.red())
            return
        # Check number of arguments
        if len(args) > 1:
            await self.help_cog.send_embed_msg(ctx, "ERROR", "Too many argumants! Only one argument is allowed.", msg_color=discord.Color.red())
            return
        # Check if the number of songs is valid
        number_of_songs = 0
        if len(args) == 1:
            query = " ".join(args)
            try:
                number_of_songs = int(query)
            except Exception as e:
                await self.help_cog.send_embed_msg(ctx, "ERROR", "Invalid argument! It must be an integer.", msg_color=discord.Color.red())
                return
            if number_of_songs <= 0:
                await self.help_cog.send_embed_msg(ctx, "ERROR", "Invalid argument! It must be an positive non-zero integer.", msg_color=discord.Color.red())
                return
        # Initialise "music" folder
        music_dir = self.initialise_music_dir()
        # Extract all mp3 files
        mp3_files = []
        for file_name in os.listdir(music_dir):
            file_path = os.path.join(music_dir, file_name)
            if os.path.isfile(file_path) and file_name.lower().endswith(".mp3"):
                mp3_files.append((file_path, file_name.removesuffix(".mp3")))
        # If no arguments, load all music
        if len(args) == 0:
            number_of_songs = len(mp3_files)
        # Limit the maximum number of songs
        if number_of_songs > len(mp3_files):
            number_of_songs = len(mp3_files)
        # Randomly select the specified number of files
        selected_mp3_files = random.sample(mp3_files, number_of_songs)
        # Add the selected music to the queue
        formatted_description = "Music added to the queue:\n"
        for file_path, title in selected_mp3_files:
            formatted_description += f" - {title}\n"
            self.music_queue.append((file_path, title))
        formatted_description = formatted_description[:-1]      # Removes the last character '\n'
        await self.help_cog.send_embed_msg(ctx, "Music Loaded!", formatted_description)
        # Start playing the audio
        if not self.is_playing:
            self.play_next(ctx)
            self.is_playing = True


    # Main function for repeat command
    @commands.command(name="repeat", aliases=["Repeat"], help="- Repeatly plays music in the queue")
    async def repeat(self, ctx, *args):
        # Check number of arguments
        if len(args) > 1:
            await self.help_cog.send_embed_msg(ctx, "ERROR", "Too many argumants! Only one argument is allowed.", msg_color=discord.Color.red())
            return
        # If input on/off, switch to that mode
        if len(args) == 1:
            query = " ".join(args)
            # Validiate input
            if query.lower() != "on" and query.lower() != "off":
                await self.help_cog.send_embed_msg(ctx, "ERROR", "Invalid argument! It must be 'on', 'off', or left empty.", msg_color=discord.Color.red())
                return
            # If argument does not switch mode
            if (self.repeat_mode == True and query.lower() == "on") or (self.repeat_mode == False and query.lower() == "off"):
                await self.help_cog.send_embed_msg(ctx, "Mode Status", f"Repeat mode is already {query.lower()}.")
                return
        # If no argument or input on/off, switch the mode
        self.repeat_mode = not self.repeat_mode
        mode_str = "on" if self.repeat_mode else "off"
        await self.help_cog.send_embed_msg(ctx, "Mode Switched!", f"Repeat mode is now {mode_str}.")
        # If repeat mode on and current song is not in the list
        if self.repeat_mode and (not self.current_music in self.music_queue):
            self.music_queue.append(self.current_music)


    # Main function for remove command
    @commands.command(name="remove", aliases=["Remove"], help="- Removes specific music in the queue")
    async def remove(self, ctx, *args):
        # Check if music title is empty
        if len(args) == 0:
            await self.help_cog.send_embed_msg(ctx, "ERROR", "Music title cannot be empty.", msg_color=discord.Color.red())
            return
        # Remove all inputted music title
        for title in args:
            modified_title = self.format_title(title)
            index = 0
            is_removed = False
            for tup in self.music_queue:
                if modified_title in tup:           # tup: (file_name, title)
                    self.music_queue.pop(index)
                    await self.help_cog.send_embed_msg(ctx, "Music Removed!", f"Music {tup[1]} removed from the queue.")
                    is_removed = True
                    break
                index += 1
            # If nothing is removed, then title does not exist
            if not is_removed:
                await self.help_cog.send_embed_msg(ctx, "ERROR", f"Music title '{modified_title}' not found.", msg_color=discord.Color.red())


    # Main function for pause command
    @commands.command(name="pause", aliases=["Pause"], help="- Pauses the currently playing music")
    async def pause(self, ctx):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice_client and voice_client.is_playing():
            voice_client.pause()
            await self.help_cog.send_embed_msg(ctx, "Music Paused!", f"Music {self.current_music[1]} is currently paused.")
        else:
            await self.help_cog.send_embed_msg(ctx, "ERROR", "No music is playing right now.", msg_color=discord.Color.red())


    # Main function for resume command
    @commands.command(name="resume", aliases=["Resume"], help="- Resumes the paused music")
    async def resume(self, ctx):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice_client and voice_client.is_paused():
            voice_client.resume()
            await self.help_cog.send_embed_msg(ctx, "Music Resumed!", f"Music {self.current_music[1]} is currently resumed.")
        else:
            await self.help_cog.send_embed_msg(ctx, "ERROR", "No music is paused right now.", msg_color=discord.Color.red())



async def setup(bot):
    await bot.add_cog(Music_cog(bot))