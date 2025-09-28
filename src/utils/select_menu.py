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
        # self.values can contain index of multiple selections, in this case we get only 1 selection
        index = int(self.values[0])  # convert str -> int
        self.view.result = index
        selected_label = self.options[index].label
        print(f"User selected option {selected_label}")
        # Acknowledge the interaction without sending a message
        await interaction.response.defer()
        # Stop listening for further input
        self.view.stop()