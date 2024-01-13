import discord
from discord import app_commands
from views.interface import AdminLauncher, CrafterLauncher, DonationLauncher


# TODO adicionar has_any_roles para vice_lider
class InterfaceLaunchers(app_commands.Group):
    @app_commands.command(
        name="criar_controles_de_administrador",
        description="Inicia os botões para controle do administrador",
    )
    @app_commands.checks.has_any_role("Admin", "Vice Lider")
    async def admin_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="**PAINEL DE GERENCIAMENTO DO ADMINISTADOR**",
            color=discord.Color.red(),
            description="""\
BOTÕES:
    ` Novo Item `               - Abre o formulário para a adição de um novo item
    ` Editar item `             - Abre o formulário para a edição de pontos de um item
    ` Zerar Pontuação de Todos` - Zera os pontos de todas as pessoas na guilda

COMANDOS:
    `/pontos add @usuário quantidade`     - Adiciona pontos ao Player
    `/pontos remover @usuário quantidade` - Remove pontos do Player
""",
        )
        await interaction.channel.send(embed=embed, view=AdminLauncher())
        await interaction.response.send_message(
            f"{interaction.user.mention} Botão criado.",
            ephemeral=True,
        )

    @app_commands.command(
        name="criar_controles_de_craft",
        description="Inicia os botões do sistema de craft",
    )
    @app_commands.checks.has_any_role("Admin", "Vice Lider")
    async def craft_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="**PAINEL DE GERENCIAMENTO DO CRAFT**",
            color=discord.Color.blue(),
        )
        await interaction.channel.send(embed=embed, view=CrafterLauncher())
        await interaction.response.send_message(
            f"{interaction.user.mention} Botão criado.",
            ephemeral=True,
        )

    @app_commands.command(
        name="criar_controles_de_doação",
        description="Inicia os botões do sistema de cadastro",
    )
    @app_commands.checks.has_any_role("Admin", "Vice Lider")
    async def donation_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"**Para doar clique no botão abaixo**",
            description="Após isso vá até a nova sala marcada e siga as instruções.",
            color=discord.Color.blue(),
        )
        await interaction.channel.send(embed=embed, view=DonationLauncher())
        await interaction.response.send_message(
            f"{interaction.user.mention} Botão criado.",
            ephemeral=True,
        )

    # @app_commands.command(name="close", description="Fecha um canal")
    # @app_commands.checks.has_any_role("Crafter")
    # async def close_command(self, interaction: discord.Interaction):
    #     if (
    #         interaction.user.name in interaction.channel.name
    #         or interaction.user.nick in interaction.channel.name
    #     ):
    #         embed = discord.Embed(
    #             title=f"Você tem certeza que deseja deletar o canal?",
    #             color=discord.Color.dark_red(),
    #         )
    #         await interaction.response.send_message(
    #             embed=embed, view=Confirm(), ephemeral=True
    #         )
    #     else:
    #         await interaction.response.send_message(
    #             f"{interaction.channel.mention} não é um canal de doação.",
    #             ephemeral=True,
    #         )


async def setup(bot):
    bot.tree.add_command(
        InterfaceLaunchers(name="interface", description="Comandos do perfil")
    )
