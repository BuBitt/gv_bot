import settings
import discord
from discord.ext import commands
from models.account import Account


logger = settings.logging.getLogger(__name__)


class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def perfil(seld, ctx):
        ...


async def setup(bot):
    await bot.add_cog(Profile(bot))
