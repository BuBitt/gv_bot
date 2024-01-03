import discord
from discord import app_commands
from views.cadastro import TransactionLauncher, Confirm


class CadastroButtons(app_commands.Group):
    @app_commands.command(
        name="gb_controler", description="Inicia o sistema de cadastro"
    )
    @app_commands.checks.has_role("Admin")
    async def transactioning(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"Painel de gerenciamento do Guild Bank.",
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
        if interaction.user.name or interaction.user.nick in interaction.channel.name:
            embed = discord.Embed(
                title=f"Você tem certeza que deseja cancelar o cadastro?",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(
                embed=embed, view=Confirm(), ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"{interaction.user.mention} não é um canal de transação.",
                ephemeral=True,
            )


async def setup(bot):
    bot.tree.add_command(
        CadastroButtons(name="interface", description="Comandos do perfil")
    )
