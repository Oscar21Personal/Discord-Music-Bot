import discord

from discord.ui import View, Select


class SelectMenu(View):
    def __init__(self, embed_msg, results, timeout=30):
        super().__init__(timeout=timeout)
        self.embed_msg = embed_msg
        self.result = None

        # Build select options
        options = [
            discord.SelectOption(
                label=f"{i+1}. {r.get('title', 'Unknown')[:90]}",  # truncate long titles
                description=f"by {r.get('uploader', 'Unknown')}",
                value=str(i)  # store index
            )
            for i, r in enumerate(results)
        ]

        self.add_item(MusicOptions(self.embed_msg, options))


class MusicOptions(Select):
    def __init__(self, embed_msg, options):
        super().__init__(options=options)
        self.embed_msg = embed_msg

    async def callback(self, interaction: discord.Interaction):
        index = int(self.values[0])  # convert str -> int
        self.view.result = index
        print(f"You selected option {index+1}")
        await self.embed_msg.send_embed_msg_inter(interaction, "TEST", f"You selected option {index+1}", ephemeral=True)
        self.view.stop()