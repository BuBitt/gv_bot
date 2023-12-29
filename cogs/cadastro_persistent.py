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

            await channel.send(
                f"{interaction.user.mention} criou um canal de transação.", view=Main()
            )
            await interaction.response.send_message(
                f"Canal de transação criado para {channel.mention}.", ephemeral=True
            )


class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Confirm", style=discord.ButtonStyle.danger, custom_id="confirm"
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
        label="Close Ticket",
        style=discord.ButtonStyle.danger,
        custom_id="close",
    )
    async def close_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="Are you sure you want to close this ticket?",
            color=discord.Color.dark_red(),
        )
        await interaction.response.send_message(
            embed=embed, ephemeral=True, view=Confirm()
        )


class CogImport(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ticket", description="Launches teh ticket system")
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

    @app_commands.command(name="close", description="Closes the ticket")
    async def close_command(self, interaction: discord.Interaction):
        if "gb-transaction-" in interaction.channel.name:
            embed = discord.Embed(
                title=f"Are you sure you want to close this ticket?",
                color=discord.Color.red,
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
