import time
import discord
import settings
import traceback
from discord import utils
from models.items import Items
from views.admin import (
    AdminToZeroPointsConfirm,
    EditItemConfirm,
    EditTierMinimalRequeirementsAdmin,
    NewItemModalAdmin,
)


logger = settings.logging.getLogger(__name__)


class NewItemConfirm(discord.ui.View):
    def __init__(self, new_item, points, changer_id) -> None:
        self.new_item = new_item
        self.points = points
        self.changer_id = changer_id
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Confirmar",
        style=discord.ButtonStyle.success,
        custom_id="confirm_new_item_button",
    )
    async def confirm_new_item(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        item_instance = Items.create(
            item=self.new_item.lower(), add_by_id=self.changer_id, points=self.points
        )
        item_instance.save()

        embed_new_item = discord.Embed(
            title=f"**Um novo item adicionado**",
            color=discord.Color.green(),
            description=f"**Item: ` {self.new_item} `, Pontos:** `{self.points}` ",
        )

        await interaction.response.send_message(embed=embed_new_item, ephemeral=True)
        gb_name = (
            interaction.user.nick
            if interaction.user.nick is not None
            else interaction.user.name
        )

        # Log da operação (terminal)
        log_message_terminal = f"{gb_name}(ID: {interaction.user.id}) adicionou o item {self.new_item} a base de dados"
        logger.info(log_message_terminal)

        timestamp = str(time.time()).split(".")[0]
        log_message_ch = f"<t:{timestamp}:F>` - `{interaction.user.mention}` adicionou um novo item a base de dados: {self.new_item}, Pontos: {self.points}`"

        channel = utils.get(interaction.guild.text_channels, name="logs")
        await channel.send(log_message_ch)


class NewItemModalCrafter(discord.ui.Modal, title="Adicione um novo item"):
    new_item = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Item",
        required=True,
        placeholder="Digite o nome do item",
    )

    async def on_submit(self, interaction: discord.Interaction):
        new_item = self.new_item.value.title()
        points = 1
        changer_id = interaction.user.id

        # mensagem
        embed = discord.Embed(
            title=f"**Confirmação de novo Item:**",
            color=discord.Color.yellow(),
            description="Quando um crafter cria um item a pontuação é automaticamente setada como 1,\npeça a um Vice Lider ou administrados para mudar a pontuação caso necessário.",
        )
        embed.add_field(name=f"**Item:**", value=f"` {new_item} `")
        embed.add_field(name=f"**Pontuação:**", value=f"` {points} `")

        # verifica se new_item já existe na base de dados
        item_check = Items.is_in_db(new_item.lower())

        if not item_check:
            await interaction.response.send_message(
                embed=embed,
                view=NewItemConfirm(new_item, points, changer_id),
                ephemeral=True,
            )
        else:
            embed = discord.Embed(
                title=f"**O Item ` {new_item} ` já está cadastrado na base de dados**",
                color=discord.Color.dark_red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        traceback.print_tb(error.__traceback__)


class EditItemModal(discord.ui.Modal, title="Edite um item"):
    item = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Item",
        required=True,
        placeholder="Digite o nome do item",
    )

    points = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Nova Pontuação",
        required=True,
        placeholder="Digite a nova pontuação do item",
    )

    async def on_submit(self, interaction: discord.Interaction):
        item = self.item.value.title()
        points = self.points.value
        changer_id = interaction.user.id

        # tenta converter points para um número inteiro
        try:
            points = int(points)
            if points < 1:
                raise TypeError
        except:
            embed = discord.Embed(
                title=f"**` {points} ` não é um número válido**",
                color=discord.Color.dark_red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        # mensagem
        embed = discord.Embed(
            title=f"**Confirmação de edição Item:**",
            color=discord.Color.yellow(),
        )
        embed.add_field(name=f"Item:", value=f"` {item} `")
        embed.add_field(name=f"**Nova Pontuação:**", value=f"` {points} `")

        # verifica se new_item já existe na base de dados
        item_check = Items.is_in_db(item.lower())

        if item_check:
            await interaction.response.send_message(
                embed=embed,
                view=EditItemConfirm(item, points, changer_id),
                ephemeral=True,
            )
        else:
            embed = discord.Embed(
                title=f"**O Item ` {item} ` não está cadastrado na base de dados**",
                color=discord.Color.dark_red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        traceback.print_tb(error.__traceback__)


# Botões das interfaces
class DonationLauncher(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Abrir Canal de Doações",
        style=discord.ButtonStyle.success,
        custom_id="transaction_button",
    )
    async def transaction(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        global_thread_name = f"DOAÇÃO - {interaction.user.name if interaction.user.nick == None else interaction.user.nick}"
        transaction = utils.get(
            interaction.guild.threads,
            name=global_thread_name,
        )

        if transaction is not None:
            await interaction.response.send_message(
                f"Você já possui um canal de Doações aberto: {transaction.mention}",
                ephemeral=True,
            )
        else:
            channel = await interaction.channel.create_thread(
                name=global_thread_name,
                invitable=False,
                auto_archive_duration=60,
                reason=f"Canal de doação para {interaction.user}",
            )

            instructions_embed = discord.Embed(
                title=f"**Instruções de uso**",
                description="\
1 - Para iniciar um novo cadastro digite `!doar` no chat;\n\
2 - Na parte `Item` o nome deve ser escrito em inglês, sugestões serão dadas;\n\
3 - Para cancelar o cadastro a qualquer momento digite `!cancelar`\n\
4 - Na parte `Print` envie uma imagem pelo por um link externo.",
                color=discord.Color.yellow(),
            )
            await channel.send(
                f"{interaction.user.mention}",
                embed=instructions_embed,
                view=Main(),
            )
            await interaction.response.send_message(
                f"Canal de doação criado para {channel.mention}.", ephemeral=True
            )
            logger.info(
                f"Canal de doação {channel.name} criado para {interaction.user.nick}(ID: {interaction.user.id})."
            )


class CrafterLauncher(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Novo Item",
        style=discord.ButtonStyle.success,
        custom_id="crafter_new_item_button",
    )
    async def new_crafter_item(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(NewItemModalCrafter())


class AdminLauncher(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Novo Item",
        style=discord.ButtonStyle.success,
        custom_id="admin_new_item_button",
    )
    async def new_admin_item(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(NewItemModalAdmin())

    @discord.ui.button(
        label="Editar Item",
        style=discord.ButtonStyle.success,
        custom_id="admin_edit_item_button",
    )
    async def edit_admin_item(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(EditItemModal())

    @discord.ui.button(
        label="Transferir Silver",
        style=discord.ButtonStyle.danger,
        custom_id="admin_transfer_silver_button",
    )
    async def admin_transfer_silver(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="**Instruções de Transferencia de Silver**",
            description="Para registrar uma transferencia de silver da gulda para um player use o comando:\n\
Essa transferencia só é geita em casos e oversupply ou grande necessidade\n\
```/admin doar-silver [@player] [quantidade]```",
            color=discord.Color.yellow(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="Editar Valores de Tier",
        style=discord.ButtonStyle.danger,
        custom_id="admin_edit_value_tier_button",
    )
    async def admin_edit_value_tier(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(EditTierMinimalRequeirementsAdmin())

    @discord.ui.button(
        label="Zerar a Pontuação de Todos",
        style=discord.ButtonStyle.danger,
        custom_id="admin_to_zero_points_button",
        row=2,
    )
    async def zero_admin_item(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="**⚠️  ESSA AÇÃO É EXTREMAMENTE PERIGOSA!  ⚠️\n\nTODOS OS PONTOS DE TODOS OS USUÁRIOS DO DISCORD VOLTARÃO A 0!\n\nUSE APENAS EM CASOS EXTREMOS!**",
            color=discord.Color.brand_red(),
            description="VOCÊ TEM CERTEZA QUE DESEJA EXECUTAR ESSA AÇÃO?\nCASO NÃO APENAS NÃO, APERTE EM IGNORAR MENSAGEM\n\nEsse botão só é válido por 30 segundos.",
        )

        await interaction.response.send_message(
            embed=embed, view=AdminToZeroPointsConfirm(), ephemeral=True
        )


# Confirmação para deletas canais
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
        label="Fechar Canal",
        style=discord.ButtonStyle.danger,
        custom_id="close_cannel_button",
    )
    async def close_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="Você tem certeza que deseja fechar esse canal?",
            color=discord.Color.dark_red(),
        )
        await interaction.response.send_message(
            embed=embed, ephemeral=True, view=Confirm()
        )
