import discord

from discord.ui import View, Select


class SelectMenu(View):
    def __init__(self, results, timeout=30):
        super().__init__(timeout=timeout)
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

        self.add_item(MusicOptions(options))


class MusicOptions(Select):
    def __init__(self, options):
        super().__init__(options=options)

    async def callback(self, interaction: discord.Interaction):
        index = int(self.values[0])  # convert str -> int
        self.view.result = index
        print(f"You selected option {index+1}")
        await interaction.response.send_message(
            f"You selected option {index+1}", ephemeral=True
        )
        self.view.stop()