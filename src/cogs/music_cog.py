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


    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Music_cog ready. Bot connected as {self.bot.user}')

    
    # Helper function to send embedded messages
    async def send_embed_msg(self, ctx, msg_title, msg_description, msg_color=discord.Color.blue()):
        msg_embed = discord.Embed(title=msg_title, description=msg_description, color=msg_color)
        msg_embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar)
        await ctx.send(embed=msg_embed)


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
            pattern = r'[^a-zA-Z\u4e00-\u9fff\u3040-\u30ff\u31f0-\u31ff\u3400-\u4DBF\u4E00-\u9FFF\u3000]'
            modified_title = re.sub(pattern, '', title)
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
            print(f"Playing {title}")
            # Play the music
            voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if voice_client.is_connected():
                voice_client.play(discord.FFmpegPCMAudio(source=file_path), after=lambda e: self.play_next(ctx))
        else:
            self.is_playing = False


    # Main function for play command
    @commands.command(name="play", aliases=["p","Play"], help="- Plays a selected song from youtube")
    async def play(self, ctx, *args):
        # Check if a link is given
        query = " ".join(args)
        if query == "":
            await self.send_embed_msg(ctx, "ERROR", "Music link cannot be empty.", msg_color=discord.Color.red())
            return
        # Join user's channel
        user_voice_channel = await self.join_channel(ctx)
        if user_voice_channel is None:
            await self.send_embed_msg(ctx, "ERROR", "You need to be in a voice channel for me to join!", msg_color=discord.Color.red())
            return
        # Download the audio
        try:
            print(f"Downloading {query}")
            await self.send_embed_msg(ctx, "Music Downloading...", f"Downloading {query}")
            file_path, title = self.download_audio(query)
        except Exception as e:
            await self.send_embed_msg(ctx, "ERROR", "An error occurred while downloading the audio.", msg_color=discord.Color.red())
            return
        # Add audio to list
        self.music_queue.append((file_path, title))
        await self.send_embed_msg(ctx, "Music Added Successfully!", f"Music {title} added to the queue.")
        # Start playing the audio
        if not self.is_playing:
            self.play_next(ctx)
            self.is_playing = True


    # Main function for stop command
    @commands.command(name="stop", aliases=["s","Stop"], help="- Stops the music and clears the queue")
    async def stop(self, ctx):
        # Check if the music has already stopped
        if not self.is_playing:
            await self.send_embed_msg(ctx, "ERROR", "Music has already stopped.", msg_color=discord.Color.red())
            return
        # Stop the current song if it's playing
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice_client.is_playing():
            voice_client.stop()
        # Clear the music queue
        self.music_queue = []
        self.is_playing = False
        print("Stopped the current music and cleared the queue.")
        await self.send_embed_msg(ctx, "Music Stopped!", "Stopped the current music and cleared the queue.")


    # Main function for list command
    @commands.command(name="list", aliases=["l","List"], help="- Lists all music in the queue")
    async def list(self, ctx):
        # Format the message
        formatted_description = ""
        for file_path, title in self.music_queue:
            formatted_description += f" - {title}\n"  
        # Send the message
        await self.send_embed_msg(ctx, "Music Queue:", formatted_description)


    # Main function for skip command
    @commands.command(name="skip", aliases=["Skip"], help="- Skips the current music and plays the next music in the queue")
    async def skip(self, ctx):
        # Check if the bot is playing
        if not self.is_playing:
            await self.send_embed_msg(ctx, "ERROR", "No Music to be skipped.", msg_color=discord.Color.red())
            return
        # Stop the current song if it's playing
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice_client.is_playing():
            # Stop the current music and start playing the next music automatically
            # Note: when .stop() is called, it executes the after function in .play(), which automatically calls play_next()
            voice_client.stop()
            if len(self.music_queue) == 0:
                await self.send_embed_msg(ctx, "Music Skipped!", f"The queue is now empty.")
                return
            file_path, title = self.music_queue[0]
            await self.send_embed_msg(ctx, "Music Skipped!", f"Skipped current music. Start playing {title}.")


    # Main function for load command
    @commands.command(name="load", aliases=["Load"], help="- Load random songs in the download directory into the queue")
    async def load(self, ctx, *args):
        # Join user's channel
        user_voice_channel = await self.join_channel(ctx)
        if user_voice_channel is None:
            await self.send_embed_msg(ctx, "ERROR", "You need to be in a voice channel for me to join!", msg_color=discord.Color.red())
            return
        # Check number of arguments
        if len(args) > 1:
            await self.send_embed_msg(ctx, "ERROR", "Too many argumants! Only one argument is allowed.", msg_color=discord.Color.red())
            return
        # Check if the number of songs is valid
        number_of_songs = 0
        if len(args) == 1:
            query = " ".join(args)
            try:
                number_of_songs = int(query)
            except Exception as e:
                await self.send_embed_msg(ctx, "ERROR", "Invalid argument! It must be an integer.", msg_color=discord.Color.red())
                return
            if number_of_songs <= 0:
                await self.send_embed_msg(ctx, "ERROR", "Invalid argument! It must be an positive non-zero integer.", msg_color=discord.Color.red())
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
        # Load the selected music to the queue
        formatted_description = "Music added to the queue:\n"
        for file_path, title in selected_mp3_files:
            formatted_description += f" - {title}\n"
            self.music_queue.append((file_path, title))
        await self.send_embed_msg(ctx, "Music Loaded!", formatted_description)
        # Start playing the audio
        if not self.is_playing:
            self.play_next(ctx)
            self.is_playing = True




async def setup(bot):
    await bot.add_cog(Music_cog(bot))