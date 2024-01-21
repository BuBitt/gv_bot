import datetime
import time
import discord
from errors.errors import IsNegativeError, NoChangeError
from models.guild import Guild
from models.mercado_bis import MarketOfferBis
import settings
import traceback
from discord import utils
import views.interface as wi
from models.items import Items
from models.account import Account
from views.mercado_bis import MarketOfferInterestBis


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

        channel = utils.get(
            interaction.guild.text_channels, id=settings.ADMIN_LOGS_CHANNEL
        )
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

        channel = utils.get(
            interaction.guild.text_channels, id=settings.ADMIN_LOGS_CHANNEL
        )
        await channel.send(log_message_ch)


class EditTierMinimalRequeirementsAdmin(
    discord.ui.Modal, title="É possível editar quantos tier quiser"
):
    t2 = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="T2",
        required=False,
        placeholder="A pontuação mínima desejada para o Tier 2",
        default=None,
    )

    t3 = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="T3",
        required=False,
        placeholder="A pontuação mínima desejada para o Tier 3",
        default=None,
    )
    t4 = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="T4",
        required=False,
        placeholder="A pontuação mínima desejada para o Tier 4",
        default=None,
    )
    t5 = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="T5",
        required=False,
        placeholder="A pontuação mínima desejada para o Tier 5",
        default=None,
    )
    t6 = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="T6",
        required=False,
        placeholder="A pontuação mínima desejada para o Tier 6",
        default=None,
    )

    async def on_submit(self, interaction: discord.Interaction):
        guilda = Guild.fetch(interaction.guild)
        response_tiers = {
            "t2": self.t2.value,
            "t3": self.t3.value,
            "t4": self.t4.value,
            "t5": self.t5.value,
            "t6": self.t6.value,
        }

        guilda_tiers = {
            "t2": guilda.t2_requirement,
            "t3": guilda.t3_requirement,
            "t4": guilda.t4_requirement,
            "t5": guilda.t5_requirement,
            "t6": guilda.t6_requirement,
        }

        non_empty_tiers = {
            key: value for key, value in response_tiers.items() if value != ""
        }

        try:
            if non_empty_tiers == {}:
                raise NoChangeError

            # converte os valores pra int
            int_dict = {key: int(value) for key, value in non_empty_tiers.items()}

            # Checa se todos os valores são positivos
            are_all_positive = all(value >= 0 for value in int_dict.values())

            if not are_all_positive:
                raise IsNegativeError

            # se nenhum erro correr executará:
            for key in int_dict:
                if key in guilda_tiers:
                    guilda_tiers[key] = int_dict[key]

            # edita os valores no banco de dados
            guilda.t2_requirement = guilda_tiers.get("t2")
            guilda.t3_requirement = guilda_tiers.get("t3")
            guilda.t4_requirement = guilda_tiers.get("t4")
            guilda.t5_requirement = guilda_tiers.get("t5")
            guilda.t6_requirement = guilda_tiers.get("t6")
            guilda.save()

            # envia feedback de sucesso
            await interaction.response.send_message(
                f"Alterações: ` {int_dict} `",
                ephemeral=True,
            )

            # atualiza ofertas existentes
            donation_channel_messages = utils.get(
                interaction.guild.text_channels, id=settings.MARKET_OFFER_CHANNEL_BIS
            )
            donation_channel_messages_history = donation_channel_messages.history(
                limit=None
            )

            async for message in donation_channel_messages_history:
                # enconta o ultimo id para definir o N° da oferta
                offer = MarketOfferBis.fetch(message.id)

                embed_offer = discord.Embed(
                    title=f"",
                    color=discord.Color.dark_purple(),
                    timestamp=datetime.datetime.fromtimestamp(int(offer.timestamp)),
                )
                embed_offer.add_field(
                    name="", value=f"**```{offer.item_tier_name.title()}```**"
                )
                embed_offer.add_field(
                    name="",
                    value=f"```Atributos: {offer.atributes.upper()}```",
                    inline=False,
                )
                embed_offer.set_footer(
                    text=f"Oferta N° {offer.id}  •  {offer.item_name.title()}"
                )

                # get the right tier
                tier_name = f"{offer.item_tier_name[0:2].lower()}_requirement"
                tier = getattr(Guild, tier_name)
                tier_points = Guild.select(tier).first()
                value = getattr(tier_points, tier_name)

                offer.min_points_req = value
                offer.save()

                vendor = utils.get(interaction.guild.members, id=offer.vendor_id)

                embed_offer.add_field(name="", value=f"```{value} Pontos Mínimos```")
                embed_offer.add_field(
                    name="", value=f"```{offer.quantity} Disponíveis```"
                )
                embed_offer.set_author(
                    name=f"{offer.vendor_name} craftou esse item BIS",
                    icon_url=vendor.display_avatar,
                )
                embed_offer.set_image(url=offer.image)

                # mensasgem publicada no canal mercado
                await message.edit(embed=embed_offer, view=MarketOfferInterestBis())

            # Log da operação (terminal)
            log_message_terminal = f"{interaction.user.name}(ID: {interaction.user.id} editou as pontuações de tier: {int_dict}"
            logger.info(log_message_terminal)

            timestamp = str(time.time()).split(".")[0]
            log_message_ch = f"<t:{timestamp}:F>` - `{interaction.user.mention}` editou as pontuações de tier: {int_dict} `"

            channel = utils.get(
                interaction.guild.text_channels, id=settings.ADMIN_LOGS_CHANNEL
            )
            await channel.send(log_message_ch)

        except NoChangeError:
            await interaction.response.send_message(
                "Nenhum número foi passado.", ephemeral=True
            )
        except TypeError:
            await interaction.response.send_message(
                f"Você não digitou números, output: {guilda}", ephemeral=True
            )
        except IsNegativeError:
            await interaction.response.send_message(
                f"Número negativos entre as respostas, output: {guilda}", ephemeral=True
            )
