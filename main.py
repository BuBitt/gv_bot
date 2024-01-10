import sys
import signal
import discord
import settings
import database
from models.items import Items
from discord import app_commands
from discord.ext import commands
from models.account import Account
from views.profile import PlayerGeneralIfo
from models.transactions import Transaction
from views.cadastro import TransactionLauncher, Main


logger = settings.logging.getLogger(__name__)


def run():
    # Cria tabela no banco de dados
    database.db.create_tables([Account, Transaction, Items])

    # Regula as permissões do BOT no servidor
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    # Define o prefixo dos comandos
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        logger.info(f"Good Vibes Crafter's Bot Started")
        # persistent views
        bot.added = False

        if not bot.added:
            bot.add_view(TransactionLauncher())
            bot.add_view(Main())
            bot.added = True

        # carrega todos os cogs automaticamente
        for cog_file in settings.COGS_DIR.glob("*.py"):
            if cog_file.name != "__init__.py":
                await bot.load_extension(f"cogs.{cog_file.name[:-3]}")
                logger.info(f"cog {cog_file.name[:-3]} loaded.")

        # carrega todos os slashcommands no bot automaticamente
        for slash_cmd in settings.SCMDS_DIR.glob("*.py"):
            if slash_cmd.name != "__init__.py":
                await bot.load_extension(f"slashcmds.{slash_cmd.name[:-3]}")
                logger.info(f"slash commands {slash_cmd.name[:-3]} loaded.")

        # carrega slash_commands na guilda
        bot.tree.copy_global_to(guild=settings.GUILDS_ID)
        await bot.tree.sync(guild=settings.GUILDS_ID)

        # comandos de load
        @bot.command()
        @commands.has_role("Admin")
        async def load(ctx, cog: str):
            await bot.load_extension(f"cogs.{cog.lower()}")

        @bot.command()
        @commands.has_role("Admin")
        async def unload(ctx, cog: str):
            await bot.unload_extension(f"cogs.{cog.lower()}")

        @bot.command()
        @commands.has_role("Admin")
        async def reload(ctx, cog: str):
            await bot.reload_extension(f"cogs.{cog.lower()}")
            logger.info(f"cog {cog} reloaded.")
            await ctx.send(f"cog: {cog} reloaded")

    # slashcommands errorhandling
    async def on_tree_error(
        interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandOnCooldown):
            return await interaction.response.send_message(
                f"Esse comando está em cooldown! Use-o novamente em **{int(error.retry_after)}** segundos!",
                ephemeral=True,
            )
        elif isinstance(error, app_commands.MissingPermissions):
            return await interaction.response.send_message(
                f"Você não tem permissão para usar esse comando.", ephemeral=True
            )
        else:
            raise error

    @bot.tree.context_menu(name="Informações Gerais")
    @app_commands.checks.has_role("Guild Banker")
    async def general_info(interaction: discord.Interaction, member: discord.Member):
        embed = discord.Embed(title=f"Informações do player: **{member.name}**")
        await interaction.response.send_message(
            embed=embed,
            view=PlayerGeneralIfo(ctx_menu_interaction=member),
            ephemeral=True,
        )

    bot.tree.on_error = on_tree_error

    bot.run(settings.DISCORD_API_SECRET, root_logger=True)


def interrupt_handler(signum, frame):
    print("")
    logger.warning("Desligando Good Vibes Crafter's Bot…")
    logger.warning("Desligado")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, interrupt_handler)
    run()
