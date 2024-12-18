import discord

from discord.ext import commands

class Help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.delete_msg_seconds = None      # None: never delete


    @commands.Cog.listener()
    async def on_ready(self):
        print("Help_cog ready")


    # Helper function to send embedded messages
    async def send_embed_msg(self, ctx, msg_title, msg_description, msg_color=discord.Color.blue()):
        # If auto-delete is on
        if self.delete_msg_seconds:
            msg_description += f"\n\nThis message will be deleted in {self.delete_msg_seconds} seconds."
        # Format the message
        msg_embed = discord.Embed(title=msg_title, description=msg_description, color=msg_color)
        msg_embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar)
        await ctx.send(embed=msg_embed, delete_after=self.delete_msg_seconds)


    # Main function for ping command
    @commands.command(name="ping", help="- Show the latency of the bot")
    async def ping(self, ctx):
        await self.send_embed_msg(ctx, f"{self.bot.user.name}'s Latency (ms): ", f"{round(self.bot.latency * 1000)} ms")


    # Main function for set_auto_delete command
    @commands.command(name="set_auto_delete", aliases=["setAutoDelete", "SetAutoDelete"], help="- Set auto-delete seconds for bot messages")
    async def set_auto_delete(self, ctx, *args):
        # Check number of arguments
        if len(args) > 1:
            await self.send_embed_msg(ctx, "ERROR", "Too many argumants! Only one argument is allowed.", msg_color=discord.Color.red())
            return
        if len(args) == 0:
            await self.send_embed_msg(ctx, "ERROR", "Too few argumants! Require one argument for seconds.", msg_color=discord.Color.red())
            return
        # Check valid argument
        query = " ".join(args)
        try:
            seconds = int(query)
        except Exception as e:
            await self.send_embed_msg(ctx, "ERROR", "Invalid argument! It must be an integer.", msg_color=discord.Color.red())
            return
        if seconds <= 0:
            await self.send_embed_msg(ctx, "ERROR", "Invalid argument! It must be an positive non-zero integer.", msg_color=discord.Color.red())
            return
        # Seconds larger than 1 hour becomes switching off auto-delete
        if seconds > 3600:
            self.delete_msg_seconds = None
            await self.send_embed_msg(ctx, "Auto-Delete Off", "Message auto-delete is now off.")
            return
        # Set number of seconds
        self.delete_msg_seconds = seconds
        await self.send_embed_msg(ctx, "Auto-Delete On", f"Message auto-delete is now set to {self.delete_msg_seconds} seconds.")



async def setup(bot):
    await bot.add_cog(Help_cog(bot))