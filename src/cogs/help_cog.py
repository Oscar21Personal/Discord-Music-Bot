import discord

from discord.ext import commands

class Help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):
        print("Help_cog ready")


    # Ping command to show the latency
    @commands.command(name="ping", help="- Show the latency of the bot")
    async def ping(self, ctx):
        ping_embed = discord.Embed(title="Ping", description="Latency in ms", color=discord.Color.blue())
        ping_embed.add_field(name=f"{self.bot.user.name}'s Latency (ms): ", value=f"{round(self.bot.latency * 1000)} ms", inline=False)
        ping_embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar)
        await ctx.send(embed=ping_embed)



async def setup(bot):
    await bot.add_cog(Help_cog(bot))