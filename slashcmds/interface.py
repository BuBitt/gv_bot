import discord
from discord import app_commands
from views.interface import (
    AdminLauncher,
    DonationLauncher,
    MarketBisCrafterLauncher,
    MarketLauncher,
    MarketLauncherBis,
)
import settings


class InterfaceLaunchers(app_commands.Group):
    @app_commands.command(
        name="criar-controles-de-administrador",
        description="Inicia os botões para controle do administrador",
    )
    @app_commands.checks.has_any_role(
        settings.VICE_LIDER_ROLE, settings.LEADER_ROLE, settings.BOT_MANAGER_ROLE
    )
    async def admin_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="**PAINEL DE GERENCIAMENTO DO ADMINISTADOR**",
            color=discord.Color.red(),
            description="""\
BOTÕES:
    ` Novo Item `                   - Abre o formulário para a adição de um novo item
    ` Editar item `                 - Abre o formulário para a edição de pontos de um item
    ` Recalcular Pontuação`         - Recalcula a pontuação de todos os players
    ` Zerar Pontuação de Todos `    - Zera os pontos de todas as pessoas na guilda
    ` Remover Oferta Comum `        - Deletar uma oferta do mercado comum pelo número
    ` Remover Oferta Bis `          - Deletar uma oferta do mercado BIS pelo número

COMANDOS:
- **Adiciona pontos ao Player**
    - ```/admin adicionar-pontos [@player] [quantidade]```
- **Remove pontos do Player**
    - ```/admin remover-pontos [@player] [quantidade]```
""",
        )
        await interaction.channel.send(embed=embed, view=AdminLauncher())
        await interaction.response.send_message(
            f"{interaction.user.mention} Botão criado.",
            ephemeral=True,
        )

    @app_commands.command(
        name="criar-controles-de-craft",
        description="Inicia os botões do sistema de craft",
    )
    @app_commands.checks.has_any_role(
        settings.VICE_LIDER_ROLE, settings.LEADER_ROLE, settings.BOT_MANAGER_ROLE
    )
    async def craft_panel_bis(self, interaction: discord.Interaction):
        market_offers_channel = discord.utils.get(
            interaction.guild.text_channels, id=settings.MARKET_IMAGES_DUMP_BIS
        )
        embed = discord.Embed(
            title="**PAINEL DE GERENCIAMENTO DO CRAFTER**",
            description=f"""\
**BOTÕES:**
    ` Minhas Ofertas   `-→ Mostra todas as suas ofertas abertas e seus números
    ` Verificar Compra `-→ Busca uma venda pelo comprovante
    ` Deletar Oferta   `-→ Deleta uma oferta sua pelo número 

**CRIAR OFERTA:**
- **Para criar um oferta use o comando:**
```/bis criar [item] [Atributos] [Quantidade] [print]```
`[Item]`→ `T4 Cloth Armor` ou `Celestial Armor`, aparecerão no autocomplete
`[Atributos]`→ Atributos abreviados. EX: ` INT WIZ VIT SP WP HASTE `
`[Quantidade]`→ Quantidade de itens a venda
`[print]`→ envie um print do item em {market_offers_channel.mention} copie e cole o link

- _Executar o comando no canal {market_offers_channel.mention} facilitará o processo._

""",
            color=discord.Color.yellow(),
        )
        await interaction.channel.send(embed=embed, view=MarketBisCrafterLauncher())
        await interaction.response.send_message(
            f"{interaction.user.mention} Botão criado.",
            ephemeral=True,
        )

    @app_commands.command(
        name="criar-controles-de-doação",
        description="Inicia os botões do sistema de cadastro",
    )
    @app_commands.checks.has_any_role(
        settings.VICE_LIDER_ROLE, settings.LEADER_ROLE, settings.BOT_MANAGER_ROLE
    )
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

    @app_commands.command(
        name="criar-painel-do-mercado",
        description="Inicia o painel e botões do sistema de mercado",
    )
    @app_commands.checks.has_any_role(
        settings.VICE_LIDER_ROLE, settings.LEADER_ROLE, settings.BOT_MANAGER_ROLE
    )
    async def market_panel(self, interaction: discord.Interaction):
        market_offers_channel = discord.utils.get(
            interaction.guild.text_channels, id=settings.MARKET_IMAGES_DUMP
        )
        embed = discord.Embed(
            title="**PAINEL DO MERCARDO**",
            color=discord.Color.dark_green(),
            description=f"""\
**BOTÕES:**
    ` Minhas Ofertas   `-→ Mostra todas as suas ofertas abertas e seus números
    ` Buscar Item      `-→ Procura por um item no mercado
    ` Buscar Player    `-→ Mostra todas as ofertas de um determinado player
    ` Verificar Compra `-→ Buscar uma venda pelo seu comprovante
    ` Deletar Oferta   `-→ Deleta uma oferta pelo seu número 

**CRIAR OFERTA:**
- **Para criar um oferta use o comando:**
```/mercado criar [item] [preço] [quantidade] [print]```
`[item]`→ Escreva um nome para o item. EX:` T4 Cloth Armor int `
`[preço]`→ Preço unitário
`[quantidade]`→ Quantidade de itens a venda
`[print]`→ envie umprint do item em {market_offers_channel.mention} copie e cole o link

- _Executar o comando no canal {market_offers_channel.mention} facilitará o processo._

""",
        )
        await interaction.channel.send(embed=embed, view=MarketLauncher())
        await interaction.response.send_message(
            f"{interaction.user.mention} Botão criado.",
            ephemeral=True,
        )

    @app_commands.command(
        name="criar-painel-do-mercado-bis",
        description="Inicia o painel e botões do sistema de mercado bis",
    )
    @app_commands.checks.has_any_role(
        settings.VICE_LIDER_ROLE, settings.LEADER_ROLE, settings.BOT_MANAGER_ROLE
    )
    async def market_panel_bis(self, interaction: discord.Interaction):
        market_offers_channel = discord.utils.get(
            interaction.guild.text_channels, id=settings.MARKET_IMAGES_DUMP
        )
        embed = discord.Embed(
            title="**PAINEL DO MERCARDO BIS**",
            color=discord.Color.dark_purple(),
            description=f"""\
**BOTÕES**
    ` Buscar Item      `-→ Procura por um item no mercado
    ` Buscar Player    `-→ Mostra todas as ofertas de um determinado player
    ` Verificar Compra `-→ Buscar uma venda pelo seu comprovante

**REGRAS**
- Ao completar as 4 peças de um set, seus pontos e rank serão resetados;
- Não é possível pegar uma mesma parte do set até o pŕoximo reset;\n
""",
        )
        await interaction.channel.send(embed=embed, view=MarketLauncherBis())
        await interaction.response.send_message(
            f"{interaction.user.mention} Botão criado.",
            ephemeral=True,
        )

    # @app_commands.command(name="close", description="Fecha um canal")
    # @app_commands.checks.has_any_role(settings.CRAFTER_ROLE)
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
