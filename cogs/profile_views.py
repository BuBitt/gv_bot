import settings
import discord
from discord.ext import commands

logger = settings.logging.getLogger(__name__)


class ProfileViewsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(ProfileViewsCog(bot))
