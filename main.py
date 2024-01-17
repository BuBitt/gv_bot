import sys
import signal
import discord
import settings
import database
from models.items import Items
from discord import app_commands
from discord.ext import commands
from models.account import Account
from models.donation import Donation
from views.mercado import MarketOfferInterest
from views.mercado_bis import MarketOfferInterestBis
from views.perfil import PlayerGeneralIfo
from views.interface import (
    AdminLauncher,
    CrafterLauncher,
    DonationLauncher,
    Main,
    MarketBisCrafterLauncher,
    MarketLauncher,
    MarketLauncherBis,
)


logger = settings.logging.getLogger(__name__)


def run():
    # Cria tabela no banco de dados
    database.db.create_tables([Account, Donation, Items])

    # Regula as permissões do BOT no servidor
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    # Define o prefixo dos comandos
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        logger.info(f"Bot {bot.user.name} id:{bot.user.id} has Started")
        bot.added = False

        # persistent views
        if not bot.added:
            bot.add_view(MarketBisCrafterLauncher())
            bot.add_view(MarketOfferInterestBis())
            bot.add_view(MarketOfferInterest())
            bot.add_view(MarketLauncherBis())
            bot.add_view(DonationLauncher())
            bot.add_view(CrafterLauncher())
            bot.add_view(MarketLauncher())
            bot.add_view(AdminLauncher())
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
        @commands.has_any_role(settings.VICE_LIDER_ROLE, settings.LEADER_ROLE)
        async def load(ctx, cog: str):
            await bot.load_extension(f"cogs.{cog.lower()}")

        @bot.command()
        @commands.has_any_role(settings.VICE_LIDER_ROLE, settings.LEADER_ROLE)
        async def unload(ctx, cog: str):
            await bot.unload_extension(f"cogs.{cog.lower()}")

        @bot.command()
        @commands.has_any_role(settings.VICE_LIDER_ROLE, settings.LEADER_ROLE)
        async def reload(ctx, cog: str):
            await bot.reload_extension(f"cogs.{cog.lower()}")
            logger.info(f"cog {cog} reloaded.")
            await ctx.send(f"cog: {cog} reloaded")

    # # TODO Error Handling
    # # slashcommands errorhandling
    # async def on_tree_error(
    #     interaction: discord.Interaction, error: app_commands.AppCommandError
    # ):
    #     if isinstance(error, app_commands.CommandOnCooldown):
    #         logger.info(f"Erro de cooldown {error}")
    #         return await interaction.response.send_message(
    #             f"Esse comando está em cooldown! Use-o novamente em **{int(error.retry_after)}** segundos!",
    #             ephemeral=True,
    #         )

    #     elif isinstance(error, app_commands.MissingPermissions):
    #         logger.info(f"Erro de permissão {error}")
    #         return await interaction.response.send_message(
    #             f"Você não tem permissão para usar esse comando.", ephemeral=True
    #         )

    #     elif isinstance(error, app_commands.errors.MissingAnyRole):
    #         logger.info(f"Erro de permissão {error}")
    #         await interaction.response.send_message(
    #             "Você não tem permissão para executar esse comando", ephemeral=True
    #         )
    #     else:
    #         raise error

    # Interaction Menus
    @bot.tree.context_menu(name="Informações Gerais")
    @app_commands.checks.has_any_role(
        settings.CRAFTER_ROLE,
        settings.VICE_LIDER_ROLE,
        settings.LEADER_ROLE,
        settings.BOT_MANAGER_ROLE,
    )
    async def general_info(interaction: discord.Interaction, member: discord.Member):
        embed = discord.Embed(title=f"Informações do player: **{member.name}**")
        await interaction.response.send_message(
            embed=embed,
            view=PlayerGeneralIfo(ctx_menu_interaction=member),
            ephemeral=True,
        )

    # bot.tree.on_error = on_tree_error
    bot.run(settings.DISCORD_API_SECRET, root_logger=True)


def interrupt_handler(signum, frame):
    print("")
    logger.warning("Desligando Good Vibes Crafter's Bot…")
    logger.warning("Desligado")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, interrupt_handler)
    run()
