import settings as st
from discord.ext import commands, tasks

import discord
from discord.ext import commands, tasks
import settings

logger = settings.logging.getLogger(__name__)


class BackgroundTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fetch_crafters_by_role.add_exception_type(Exception)
        self.fetch_crafters_by_role.start()

    def cog_unload(self) -> None:
        self.fetch_crafters_by_role.stop()

    @tasks.loop(seconds=5)  # Run the task every 60 seconds
    async def fetch_crafters_by_role(self):
        # Your background task logic goes here
        # test = discord.utils.get(
        #     self.bot.guilds[0].roles, id=settings.ADMIN_LOGS_CHANNEL
        # )
        test = self.bot.guilds[0].name
        logger.info(test)

    @commands.command()
    async def start(self, ctx):
        self.fetch_crafters_by_role.start()

    @commands.command()
    async def cancel(self, ctx):
        self.fetch_crafters_by_role.cancel()

    @commands.command()
    async def change(self, ctx, seconds: int):
        self.fetch_crafters_by_role.change_interval(seconds=seconds)

    @fetch_crafters_by_role.before_loop
    async def before_check_users(self):
        logger.warn("Before starting loop")

    @fetch_crafters_by_role.after_loop
    async def after_check_users(self):
        logger.warn("After stopping loop")


async def setup(bot):
    await bot.add_cog(BackgroundTasks(bot))
