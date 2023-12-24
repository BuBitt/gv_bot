import discord
from discord.ext import commands
import settings
import utils
import database
from models.account import Account

logger = settings.logging.getLogger(__name__)


def run():
    database.db.create_tables([Account])

    intents = discord.Intents.all()
    # intents.message_content = True
    # intents.members = True
    # intents.guild_messages = True
    # intents.guilds = True
    # intents.

    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        await utils.load_videocmds(bot)
        await bot.tree.sync()

        for cog_file in settings.COGS_DIR.glob("*.py"):
            if cog_file.name != "__init__.py":
                await bot.load_extension(f"cogs.{cog_file.name[:-3]}")

        @bot.command()
        async def load(ctx, cog: str):
            await bot.load_extension(f"cogs.{cog.lower()}")

        @bot.command()
        async def unload(ctx, cog: str):
            await bot.unload_extension(f"cogs.{cog.lower()}")

        @bot.command()
        async def reload(ctx, cog: str):
            await bot.reload_extension(f"cogs.{cog.lower()}")

    bot.run(settings.DISCORD_API_SECRET, root_logger=True)


if __name__ == "__main__":
    run()
