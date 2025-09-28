import asyncio
import discord

class EmbedMsg():
    def __init__(self):
        self.delete_msg_seconds = None      # None: never delete


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