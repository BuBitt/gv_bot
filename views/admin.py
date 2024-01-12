import time
import discord
import settings
import traceback
from database import db
from discord import utils
import views.interface as wi
from models.items import Items
from models.account import Account


logger = settings.logging.getLogger(__name__)


class AdminToZeroPointsConfirm(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=30)

    @discord.ui.button(
        label="Confirmar",
        style=discord.ButtonStyle.danger,
        custom_id="confirm_to_zero_points_button",
    )
    async def confirm_to_zero_points_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        query = Account.update(points=0)
        query.execute()

        embed = discord.Embed(
            title="**Todos os usuários agora possuem 0 pontos**",
            color=discord.Color.brand_red(),
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Log da operação (terminal)
        log_message_terminal = f"{interaction.user.name}(ID: {interaction.user.id}) Zerou a pontuação de todos os players da guilda"
        logger.info(log_message_terminal)

        timestamp = str(time.time()).split(".")[0]
        log_message_ch = f"<t:{timestamp}:F>` - `{interaction.user.mention}` Zerou a pontuação de todos os players da guilda `"

        channel = utils.get(interaction.guild.text_channels, name="logs")
        await channel.send(log_message_ch)


class NewItemModalAdmin(discord.ui.Modal, title="Adicione um novo item"):
    new_item = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Item",
        required=True,
        placeholder="Digite o nome do item",
    )

    points = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Pontuação",
        required=True,
        placeholder="Digite a pontuação do item",
    )

    async def on_submit(self, interaction: discord.Interaction):
        new_item = self.new_item.value.title()
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
            title=f"**Confirmação de novo Item:**",
            color=discord.Color.yellow(),
        )
        embed.add_field(name=f"**Item:**", value=f"` {new_item} `")
        embed.add_field(name=f"**Pontuação:**", value=f"` {points} `")

        # verifica se new_item já existe na base de dados
        item_check = Items.is_in_db(new_item.lower())

        if not item_check:
            await interaction.response.send_message(
                embed=embed,
                view=wi.NewItemConfirm(new_item, points, changer_id),
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


class EditItemConfirm(discord.ui.View):
    def __init__(self, item, points, changer_id) -> None:
        self.item = item
        self.points = points
        self.changer_id = changer_id
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Confirmar",
        style=discord.ButtonStyle.success,
        custom_id="confirm_new_item_button",
    )
    async def confirm_edit_item(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        item_instance = Items.fetch(item=self.item.lower())

        item_instance.points = self.points
        item_instance.add_by_id = self.changer_id

        item_instance.save()

        embed_new_item = discord.Embed(
            title=f"Item: **` {self.item} ` **",
            color=discord.Color.green(),
            description=f"**Nova Pontuação:** `{self.points}` ",
        )

        await interaction.response.send_message(embed=embed_new_item, ephemeral=True)
        gb_name = (
            interaction.user.nick
            if interaction.user.nick is not None
            else interaction.user.name
        )

        # Log da operação (terminal)
        log_message_terminal = f"{gb_name}(ID: {interaction.user.id} editou a pontuação do item {item_instance.item} para: {self.points} pontos"
        logger.info(log_message_terminal)

        timestamp = str(time.time()).split(".")[0]
        log_message_ch = f"<t:{timestamp}:F>` - `{interaction.user.mention}` editou a pontuação do item: {item_instance.item} para: {self.points} pontos `"

        channel = utils.get(interaction.guild.text_channels, name="logs")
        await channel.send(log_message_ch)
