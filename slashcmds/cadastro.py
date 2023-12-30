import discord
from discord import app_commands
from views.cadastro import TransactionLauncher, Confirm


class Cadastro(app_commands.Group):
    @app_commands.command(
        name="new_tchannel_button", description="Inicia o sistema de cadastro"
    )
    @app_commands.checks.has_role("Admin")
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

    @app_commands.command(name="close", description="Fecha o canal de cadastro")
    @app_commands.checks.has_role("Guild Banker")
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
    @app_commands.checks.has_role("Guild Banker")
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
    bot.tree.add_command(Cadastro(name="cadastro", description="Comandos do perfil"))