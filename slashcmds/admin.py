import time
import discord
import settings
from discord import utils
from discord import app_commands
from models.account import Account
from cogs.doar import IsNegativeError
from errors.errors import NotEnoughtPoints


logger = settings.logging.getLogger(__name__)


# TODO adicionar has_any_roles para vice_lider e remover crafter
# TODO selfcheck para não dar pontos a si mesmo
class AdminCommands(app_commands.Group):
    @app_commands.command(name="add", description="Adiciona pontos a um player")
    @app_commands.describe(
        player="O player que receberá pontos",
        pontos="A quantidade de pontos a ser adicionada",
    )
    @app_commands.checks.has_any_role("Admin", "Vice Lider", "Crafter")
    async def admin_add_points(
        self, interaction: discord.Interaction, player: discord.Member, pontos: str
    ):
        try:
            pontos = int(pontos)
            if pontos < 1:
                raise IsNegativeError

        except ValueError:
            return await interaction.response.send_message(
                f"` {pontos} ` não é um número válido", ephemeral=True
            )

        except IsNegativeError:
            return await interaction.response.send_message(
                f"` {pontos} ` não é maior que zero", ephemeral=True
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

        # envia mensagem de confirmação
        await interaction.response.send_message(
            f"` {pontos} ` pontos foram concedidos a {player.mention}",
            ephemeral=True,
        )

        # logs também enviados ao player que recebeu pontos
        log_message_terminal = f"{interactor_name}(ID: {interaction.user.id}) adicinou {pontos} pontos ao player {user_name}"
        logger.info(log_message_terminal)

        timestamp = str(time.time()).split(".")[0]
        log_message_ch = f"<t:{timestamp}:F>` - `{interaction.user.mention}` adicionou {pontos} pontos ao player `{player.mention}"

        channel = utils.get(interaction.guild.text_channels, name="logs")
        await channel.send(log_message_ch)

        # Envia PM do log ao player afetado
        await player.send(log_message_ch)
    
    @app_commands.command(name="remover", description="Remove pontos a um player")
    @app_commands.describe(
        player="O player que perderá pontos",
        pontos="A quantidade de pontos a ser removida",
    )
    @app_commands.checks.has_any_role("Admin", "Vice Lider", "Crafter")
    async def admin_remove_points(
        self, interaction: discord.Interaction, player: discord.Member, pontos: str
    ):
        account = Account.fetch(player)

        try:
            pontos = int(pontos)
            if pontos < 1:
                raise IsNegativeError

            elif pontos > account.points:
                raise NotEnoughtPoints

        except ValueError:
            return await interaction.response.send_message(
                f"` {pontos} ` não é um número válido", ephemeral=True
            )

        except NotEnoughtPoints:
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
            f"` {pontos} ` pontos foram removidos do player {player.mention}",
            ephemeral=True,
        )

        # logs também enviados ao player que recebeu pontos
        log_message_terminal = f"{interactor_name}(ID: {interaction.user.id}) removeu {pontos} pontos do player {user_name}"
        logger.info(log_message_terminal)

        timestamp = str(time.time()).split(".")[0]
        log_message_ch = f"<t:{timestamp}:F>` - `{interaction.user.mention}` removeu {pontos} pontos do player `{player.mention}"

        channel = utils.get(interaction.guild.text_channels, name="logs")
        await channel.send(log_message_ch)

        # Envia PM do log ao player afetado
        await player.send(log_message_ch)


async def setup(bot):
    bot.tree.add_command(
        AdminCommands(
            name="pontos", description="Comandos para adição e remoção de pontos"
        )
    )
