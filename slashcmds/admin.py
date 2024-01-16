import time
import discord
from models.guild import Guild
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
        name="doar-silver", description="Transfere Silver da guilda para um player"
    )
    @app_commands.describe(
        player="O player que receberá silver",
        quantidade="A quantidade de silver a ser transferida",
    )
    @app_commands.checks.has_any_role(
        settings.VICE_LIDER_ROLE, settings.LEADER_ROLE, settings.BOT_MANAGER_ROLE
    )
    async def admin_donate_silver(
        self, interaction: discord.Interaction, player: discord.Member, quantidade: int
    ):
        account = Account.fetch(player)
        guild = Guild.fetch(interaction.guild)

        try:
            if quantidade < 1:
                raise IsNegativeError

            elif guild.guild_silver < quantidade:
                raise NotEnoughtPointsError

        except ValueError:
            return await interaction.response.send_message(
                f"`✪ {quantidade} ` não é um número positivo", ephemeral=True
            )

        except NotEnoughtPointsError:
            return await interaction.response.send_message(
                f"A Guilda não possui silver suficiente ` {guild.guild_silver} ` para transferir ` {quantidade} `",
                ephemeral=True,
            )

        interactor_name = (
            interaction.user.name
            if interaction.user.nick == None
            else interaction.user.nick
        )
        user_name = player.name if player.nick == None else player.nick

        guild.guild_silver -= quantidade
        account.silver_quantity += quantidade
        guild.save()
        account.save()

        # envia mensagem de confirmação
        await interaction.response.send_message(
            f"`✪ {quantidade} ` Silver foi transferido para o player {player.mention}",
            ephemeral=True,
        )

        # logs também enviados ao player que recebeu pontos
        log_message_terminal = f"{interactor_name}(ID: {interaction.user.id}) transferiu {quantidade} silver da Guilda para o player {user_name}"
        logger.info(log_message_terminal)

        timestamp = str(time.time()).split(".")[0]
        log_message_ch = f"<t:{timestamp}:F>` - `{interaction.user.mention}` transferiu {quantidade} silver da Guilda para o player `{player.mention}"

        channel = utils.get(
            interaction.guild.text_channels, id=settings.ADMIN_LOGS_CHANNEL
        )
        await channel.send(log_message_ch)

        # Envia PM do log ao player afetado
        await player.send(log_message_ch)


async def setup(bot):
    bot.tree.add_command(
        AdminCommands(name="admin", description="Comandos de administrador")
    )
