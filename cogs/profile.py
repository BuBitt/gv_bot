import settings
import discord
from discord.ext import commands


logger = settings.logging.getLogger(__name__)


class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(Profile(bot))
