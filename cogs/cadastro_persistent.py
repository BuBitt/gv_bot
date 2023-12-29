from dis import disco
import discord
import settings
from discord import utils, app_commands
from discord.ext import commands


logger = settings.logging.getLogger(__name__)


class TransactionLauncher(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Criar Transação",
        style=discord.ButtonStyle.success,
        custom_id="transaction_button",
    )
    async def transaction(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        transaction = utils.get(
            interaction.guild.text_channels,
            name=f"gb-transaction-{interaction.user.nick}",
        )
        if transaction is not None:
            await interaction.response.send_message(
                f"Você já possui um canal de transação aberto {transaction.mention}",
                ephemeral=True,
            )
        else:
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(
                    view_channel=False
                ),
                interaction.user: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    attach_files=True,
                    embed_links=True,
                ),
                interaction.guild.me: discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_message_history=True
                ),
            }

            channel = await interaction.guild.create_text_channel(
                name=f"gb-transaction-{interaction.user.nick}",
                overwrites=overwrites,
                reason=f"Canal de transação para {interaction.user}",
            )

            instructions_embed = discord.Embed(
                title=f"**Instruções de uso para {interaction.user.nick}.**",
                description="1 - Para iniciar um novo cadastro digite `!cadastro` no chat;\n \
                    2 - Na parte `Item` o nome deve ser escrito em inglês;",
                color=discord.Color.yellow(),
            )
            await channel.send(
                f"{interaction.user.mention} criou um canal de transação.",
                embed=instructions_embed,
                view=Main(),
            )
            await interaction.response.send_message(
                f"Canal de transação criado para {channel.mention}.", ephemeral=True
            )
            logger.info(
                f"Canal de transação {channel.name} criado para {interaction.user.nick}(ID: {interaction.user.id})."
            )


class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Confirmar", style=discord.ButtonStyle.red, custom_id="confirm"
    )
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        try:
            await interaction.channel.delete()
        except:
            await interaction.response.send_message(
                f"Channel delete failed! make sure I have `manage_channels` persmission.",
                ephemeral=True,
            )


class Main(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Fechar Transação",
        style=discord.ButtonStyle.danger,
        custom_id="close",
    )
    async def close_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="Você tem certeza que deseja cancelar o cadastro?",
            color=discord.Color.dark_red(),
        )
        await interaction.response.send_message(
            embed=embed, ephemeral=True, view=Confirm()
        )


class CogImport(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="transaction_button", description="Inicia o sistema de cadastro"
    )
    async def transactioning(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"Para criar um novo canal de transação pressione o botão abaixo.",
            color=discord.Color.blue(),
        )
        await interaction.channel.send(embed=embed, view=TransactionLauncher())
        await interaction.response.send_message(
            f"{interaction.user.mention} Botão criado.",
            ephemeral=True,
        )

    @app_commands.command(name="close", description="Closes the cadastro")
    async def close_command(self, interaction: discord.Interaction):
        if "gb-transaction-" in interaction.channel.name:
            embed = discord.Embed(
                title=f"Você tem certeza que deseja cancelar o cadastro?",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(
                embed=embed, view=Confirm(), ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"{interaction.user.mention} isn't a Ticket.",
                ephemeral=True,
            )

    @app_commands.command(name="add", description="Adds a user to the ticket.")
    @app_commands.describe(user="The user you want to add to the ticket")
    async def add_command(self, interaction: discord.Interaction, user: discord.Member):
        if "gb-transaction-" in interaction.channel.name:
            await interaction.channel.set_permissions(
                user,
                view_channel=True,
                send_messages=True,
                attach_files=True,
                embed_links=True,
            )
            await interaction.response.send_message(
                f"{user.mention} has been added to ticket {interaction.user.mention}"
            )
        else:
            await interaction.response.send_message(
                f"This isn't a ticket.", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(CogImport(bot))
