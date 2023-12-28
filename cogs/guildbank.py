import discord
import discord.ui

import settings
from discord.ext import commands
from models.account import Account

logger = settings.logging.getLogger(__name__)


class GuildBankButton(discord.ui.View):
    # def test(self, interactions: discord.Interaction, test: int):

    @discord.ui.button(label="Novo", style=discord.ButtonStyle.success)
    async def create_entry(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_message(
            f"{interaction.user.mention} Test", ephemeral=True
        )
        await interaction.guild.create_text_channel(
            name="Thread Name",
        )

    @discord.ui.button(label="Edit")
    async def edit_entries(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_message("Edit")

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.red)
    async def cancel_entries(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_message("Edit")


class GuildBank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def gb(self, ctx):
        view = GuildBankButton()
        # button = discord.ui.Button(label="New")
        # view.add_item(button)
        await ctx.send(view=view)


async def setup(bot):
    await bot.add_cog(GuildBank(bot))
