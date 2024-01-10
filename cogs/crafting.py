import discord
from discord import utils
from discord.ext import commands

import settings

logger = settings.logging.getLogger(__name__)


class CadastroCrafting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_role("Crafter")
    @commands.has_role("Guild Banker")
    async def craft(self, ctx: commands.context.Context):
        if ctx.channel.name.startswith("Craft"):
            await ctx.channel.send("test")


async def setup(bot):
    await bot.add_cog(CadastroCrafting(bot))
