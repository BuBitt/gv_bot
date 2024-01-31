import asyncio
import datetime
import time
import discord
from models.guild import Guild
from models.mercado_bis import MarketOfferBis
import settings
from discord import utils
from discord import app_commands
from models.account import Account
from cogs.doar import IsNegativeError
from errors.errors import IsYourselfError, NotEnoughtPointsError


logger = settings.logging.getLogger(__name__)


class AdminCommands(app_commands.Group):
    @app_commands.command(
        name="adicionar-pontos", description="Adiciona pontos a um player"
    )
    @app_commands.describe(
        player="O player que receberá pontos",
        pontos="A quantidade de pontos a ser adicionada",
    )
    @app_commands.checks.has_any_role(
        settings.VICE_LIDER_ROLE, settings.LEADER_ROLE, settings.BOT_MANAGER_ROLE
    )
    async def admin_add_points(
        self, interaction: discord.Interaction, player: discord.Member, pontos: str
    ):
        try:
            pontos = int(pontos)
            if pontos < 1:
                raise IsNegativeError

            if interaction.user.id == player.id:
                raise IsYourselfError
        except IsYourselfError:
            return await interaction.response.send_message(
                f"`✪ {pontos} ` Você não pode dar pontos a sí mesmo.", ephemeral=True
            )
        except ValueError:
            return await interaction.response.send_message(
                f"`✪ {pontos} ` não é um número válido.", ephemeral=True
            )

        except IsNegativeError:
            return await interaction.response.send_message(
                f"`✪ {pontos} ` não é maior que zero.", ephemeral=True
            )

        interactor_name = (
            interaction.user.name
            if interaction.user.nick == None
            else interaction.user.nick
        )
        user_name = player.name if player.nick == None else player.nick

        account = Account.fetch(player)
        account.points += pontos
        account.save()

        # envia mensagem de feedback
        await interaction.response.send_message(
            f"`✪ {pontos} ` pontos foram concedidos a {player.mention}",
            ephemeral=True,
        )

        # logs também enviados ao player que recebeu pontos
        log_message_terminal = f"{interactor_name}(ID: {interaction.user.id}) adicinou {pontos} pontos ao player {user_name}"
        logger.info(log_message_terminal)

        timestamp = str(time.time()).split(".")[0]
        log_message_ch = f"<t:{timestamp}:F>` - `{interaction.user.mention}` adicionou {pontos} pontos ao player `{player.mention}"

        channel = utils.get(
            interaction.guild.text_channels, id=settings.ADMIN_LOGS_CHANNEL
        )
        await channel.send(log_message_ch)

        # Envia PM do log ao player afetado
        await player.send(log_message_ch)

    @app_commands.command(
        name="remover-pontos", description="Remove pontos a um player"
    )
    @app_commands.describe(
        player="O player que perderá pontos",
        pontos="A quantidade de pontos a ser removida",
    )
    @app_commands.checks.has_any_role(
        settings.VICE_LIDER_ROLE, settings.LEADER_ROLE, settings.BOT_MANAGER_ROLE
    )
    async def admin_remove_points(
        self, interaction: discord.Interaction, player: discord.Member, pontos: str
    ):
        account = Account.fetch(player)

        try:
            pontos = int(pontos)
            if pontos < 1:
                raise IsNegativeError

            elif pontos > account.points:
                raise NotEnoughtPointsError

        except ValueError:
            return await interaction.response.send_message(
                f"`✪ {pontos} ` não é um número válido", ephemeral=True
            )

        except NotEnoughtPointsError:
            return await interaction.response.send_message(
                f"{player.mention} possui apenas ` {account.points} ` pontos, portanto é impossível remover ` {pontos} ` pontos",
                ephemeral=True,
            )

        interactor_name = (
            interaction.user.name
            if interaction.user.nick == None
            else interaction.user.nick
        )
        user_name = player.name if player.nick == None else player.nick

        account.points -= pontos
        account.save()

        # envia mensagem de confirmação
        await interaction.response.send_message(
            f"`✪ {pontos} ` pontos foram removidos do player {player.mention}",
            ephemeral=True,
        )

        # logs também enviados ao player que recebeu pontos
        log_message_terminal = f"{interactor_name}(ID: {interaction.user.id}) removeu {pontos} pontos do player {user_name}"
        logger.info(log_message_terminal)

        timestamp = str(time.time()).split(".")[0]
        log_message_ch = f"<t:{timestamp}:F>` - `{interaction.user.mention}` removeu {pontos} pontos do player `{player.mention}"

        channel = utils.get(
            interaction.guild.text_channels, id=settings.ADMIN_LOGS_CHANNEL
        )
        await channel.send(log_message_ch)

        # Envia PM do log ao player afetado
        await player.send(log_message_ch)

    @app_commands.command(
        name="aviso",
        description="manda um embed de aviso",
    )
    @app_commands.checks.has_any_role(
        settings.VICE_LIDER_ROLE, settings.LEADER_ROLE, settings.BOT_MANAGER_ROLE
    )
    async def send_warning_gc_orders(
        self, interaction: discord.Interaction, titulo: str, aviso: str
    ):
        embed = discord.Embed(
            title=titulo, description=aviso, color=discord.Color.yellow()
        )
        chat_da_guilda = discord.utils.get(
            interaction.guild.text_channels, id=settings.GUILD_CHAT
        )
        aviso = await chat_da_guilda.send(embed=embed)
        await interaction.response.send_message(
            f"Aviso Publicado: {aviso.jump_url}", ephemeral=True
        )

    @app_commands.command(
        name="zerar",
        description="manda um embed de aviso",
    )
    @app_commands.checks.has_any_role(
        settings.VICE_LIDER_ROLE,
        settings.LEADER_ROLE,
        settings.BOT_MANAGER_ROLE,
        settings.CRAFTER_ROLE,
    )
    async def reset_player_points(
        self, interaction: discord.Interaction, player: discord.User
    ):
        account = Account.fetch(player)
        account.points = 0
        account.got_helmet = False
        account.got_armor = False
        account.got_legs = False
        account.got_boots = False
        account.set_lock = "no"
        account.save()

        await interaction.response.send_message(
            f"os pontos de {player.mention} foram resetados e seu set_lock foi limpo.",
            ephemeral=True,
        )


async def setup(bot):
    bot.tree.add_command(
        AdminCommands(name="admin", description="Comandos de administrador")
    )
