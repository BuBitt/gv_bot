import discord
import discord.ui

import settings
from discord.ext import commands
from models.account import Account

logger = settings.logging.getLogger(__name__)


class GuildBankButton(discord.ui.View):
    # def test(self, interactions: discord.Interaction, test: int):

    @discord.ui.button(label="New", style=discord.ButtonStyle.success)
    async def create_new_entry(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_message(
            f"{interaction.user.mention} Test", ephemeral=True
        )
        await interaction.guild.create_text_channel(name="haha")

    @discord.ui.button(label="Edit", style=discord.ButtonStyle.grey)
    async def edit_entries(
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
