import settings
import discord
from discord import commands


logger = settings.logging.getLogger(__name__)


class Profile(commands.Cog):
    pass


async def setup(bot):
    await bot.add_cog(Profile(bot))
