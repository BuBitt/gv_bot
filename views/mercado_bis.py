import hashlib
import time
import traceback
from models.account import Account

import settings

import discord
from discord import utils
from datetime import datetime

from models.vendas_bis import SellInfoBis
from models.mercado_bis import MarketOfferBis

from errors.errors import IsGreatherThanMaxError, IsNegativeError


logger = settings.logging.getLogger(__name__)


class QuantityModal(discord.ui.Modal, title="Quantos você deseja comprar?"):
    def __init__(self, max_quantity, message, offer, vendor, embed_offer) -> None:
        self.offer = offer
        self.vendor = vendor
        self.message = message
        self.embed_offer = embed_offer
        self.max_quantity = max_quantity
        super().__init__(timeout=None)

    quantity = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Quantidade",
        required=True,
        placeholder=f"digite a quantidade",
    )

    async def on_submit(self, interaction: discord.Interaction):
        quantity_to_buy = self.quantity.value
        max_quantity = self.max_quantity
        vendor = utils.get(interaction.guild.members, id=self.offer.vendor_id)

        try:
            quantity_to_buy = int(quantity_to_buy)

            if quantity_to_buy < 1:
                raise IsNegativeError

            elif quantity_to_buy > max_quantity:
                raise IsGreatherThanMaxError

            else:
                # feedback
                await interaction.response.send_message(
                    f"` Sua intenção de compra foi enviada para `{vendor.mention}",
                    ephemeral=True,
                )

                # adiciona quantidade a comprar
                self.embed_offer.add_field(
                    name="", value=f"```Qte: {quantity_to_buy}```"
                )

                # envia a oferta ao canal do mercado
                await vendor.send(
                    content=f"{interaction.user.mention}` está interessado na sua oferta `{self.offer.jump_url}",
                    embed=self.embed_offer,
                    view=MarketOfferInterestVendorConfirmationBis(
                        buyer=interaction.user,
                        message=self.message,
                        quantity_to_buy=quantity_to_buy,
                        offer=self.offer,
                    ),
                )

        except IsNegativeError:
            return await interaction.response.send_message(
                f"O número precisa ser maior que 1.", ephemeral=True
            )

        except IsGreatherThanMaxError:
            return await interaction.response.send_message(
                f"A quantidade não pode ser maior que ` {max_quantity} `.",
                ephemeral=True,
            )

        except ValueError:
            return await interaction.response.send_message(
                f"` {quantity_to_buy} ` não é um número.", ephemeral=True
            )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        traceback.print_tb(error.__traceback__)


class MarketOfferInterestVendorConfirmationBis(discord.ui.View):
    def __init__(self, buyer, message, offer, quantity_to_buy) -> None:
        self.buyer = buyer
        self.offer = offer

        self.message = message
        self.quantity_to_buy = quantity_to_buy
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Vender",
        style=discord.ButtonStyle.success,
        custom_id="vendor_confirmation_button_bis",
    )
    async def vendor_confirmation_button_bis(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        # verifica se a ordem ainda está ativa
        offer = MarketOfferBis.fetch_by_jump_url(self.offer.jump_url)
        if not offer.is_active:
            await interaction.message.delete()
            return await interaction.response.send_message(
                content=f"`Não foi possível vender para`{self.buyer.mention}` Todos os itens já foram vendidos. `",
                ephemeral=True,
            )

        # verifica se há intens suficientes para aceitar a oferta
        if offer.quantity < self.quantity_to_buy:
            await interaction.message.delete()
            return await interaction.response.send_message(
                content=f"`Não foi possível vender para`{self.buyer.mention}` {offer.quantity} disponíveis para uma ordem de {self.quantity_to_buy} itens. `",
                ephemeral=True,
            )

        # timestamp
        timestamp = datetime.fromtimestamp(int(time.time()))

        # gera hash da venda
        data = f"{interaction.user.id}{self.buyer.id}{timestamp}"
        sha256_hash = hashlib.sha256(data.encode()).hexdigest()

        # embed de confirmação
        embed_offer = discord.Embed(
            title=f"**RECIBO BIS**",
            color=discord.Color.purple(),
            timestamp=timestamp,
        )
        embed_offer.add_field(
            name="",
            value=f"```Item: {self.offer.item_tier_name} / {self.offer.item_name}```",
            inline=False,
        )
        embed_offer.insert_field_at(
            name="", value=f"```Oferta N°: {self.offer.id}```", index=1
        )
        embed_offer.insert_field_at(
            name="", value=f"```Qte entregue: {self.quantity_to_buy}```", index=2
        )
        embed_offer.add_field(
            name="COMPROVANTE", value=f"```{sha256_hash}```", inline=False
        )

        # grava venda no db
        sell_dict = {}
        sell_dict["vendor_id"] = interaction.user.id
        sell_dict["vendor_name"] = interaction.user.name
        sell_dict["buyer_id"] = self.buyer.id
        sell_dict["buyer_name"] = self.buyer.name
        sell_dict["offer_id"] = self.offer.id
        sell_dict["item_tier_name"] = self.offer.item_tier_name
        sell_dict["item_name"] = self.offer.item_name
        sell_dict["quantity"] = self.quantity_to_buy
        sell_dict["timestamp"] = datetime.fromtimestamp(int(time.time()))
        sell_dict["hash_proof"] = sha256_hash
        SellInfoBis.new(sell_dict)

        # envia feedback
        await interaction.message.edit(
            content=f"`✪ Venda concluída. {self.quantity_to_buy} {self.offer.item_tier_name} para `{self.buyer.mention}",
            embed=embed_offer,
            view=None,
        )
        await self.buyer.send(
            content=f"`✪ Compra concluída. Você comprou {self.quantity_to_buy} {self.offer.item_tier_name} de `{interaction.user.mention}",
            embed=embed_offer,
        )

        # calcula a quantidade de itens restante
        remain = self.offer.quantity - self.quantity_to_buy
        self.offer.quantity = remain

        # sistema para setar o equipamento true ou false no account
        buyer_account = Account.fetch(self.buyer)
        item_type = self.offer.item_type.lower()

        attribute_name = f"got_{item_type}"
        if hasattr(buyer_account, attribute_name):
            setattr(buyer_account, attribute_name, True)

        # sistema de checkagem dos 4 itens e reset dos pontos
        if all(
            getattr(buyer_account, f"got_{item}")
            for item in ["boots", "helmet", "armor", "legs"]
        ):
            buyer_account.points = 0
            buyer_account.got_helmet = False
            buyer_account.got_armor = False
            buyer_account.got_boots = False
            buyer_account.got_legs = False

        buyer_account.save()

        # deleta mensagem de confirmação de venda
        if remain == 0:
            # muda o status da oferta no db e deleta oferta no canal ofertas
            self.offer.is_active = False
            await self.message.delete()

        else:
            # encontra o ultimo ID da tabela para definir o número da oferta
            offer = self.offer

            embed_offer = discord.Embed(
                title=f"",
                color=discord.Color.dark_purple(),
                timestamp=datetime.fromtimestamp(int(self.offer.timestamp)),
            )

            embed_offer.set_footer(
                text=f"Oferta N° {offer.id} • {offer.item_name.title()}"
            )
            embed_offer.add_field(
                name="", value=f"**```{offer.item_tier_name.title()}```**", inline=False
            )
            embed_offer.add_field(
                name="",
                value=f"```Atributos: {offer.atributes.upper()}```",
            )
            embed_offer.add_field(name="", value=f"```{offer.quantity} Disponíveis```")
            embed_offer.set_author(
                name=f"{offer.vendor_name} craftou esse item BIS",
                icon_url=interaction.user.display_avatar,
            )
            embed_offer.set_image(url=offer.image)

            await self.message.edit(embed=embed_offer, view=MarketOfferInterestBis())

        self.offer.save()

        # log da operação
        log_message_terminal = f"Oferta N° {self.offer.id}: O Crafter {interaction.user.name} finalizou uma entrega de item: {self.offer.item_tier_name}. Comprador: {self.buyer.name}"
        logger.info(log_message_terminal)

        timestamp = str(time.time()).split(".")[0]
        log_message_ch = f"<t:{timestamp}:F>` - Oferta N° {self.offer.id} teve um item entregue. - `{self.buyer.mention}` recebeu o item: {self.offer.item_tier_name} do Crafter:`{interaction.user.mention}"

        log_channel = utils.get(
            self.message.guild.text_channels, id=settings.ADMIN_LOGS_CHANNEL
        )
        log_mkt_channel = utils.get(
            self.message.guild.text_channels, id=settings.MARKET_LOG_BIS
        )

        # envia msg aos canais de log
        await log_channel.send(log_message_ch)
        await log_mkt_channel.send(log_message_ch)


class MarketOfferInterestBis(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Tenho Interesse",
        style=discord.ButtonStyle.blurple,
        emoji="🛒",
        custom_id="interest_in_offer_button_bis",
    )
    async def interest_in_offer_button_bis(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        # conta do usuário
        account = Account.fetch(interaction.user)

        # encontra a oferta
        offer = MarketOfferBis.fetch(interaction.message.id)
        vendor = utils.get(interaction.guild.members, id=offer.vendor_id)

        if account.points < offer.min_points_req:
            no_points_embed = discord.Embed(
                title=f"Pontos insuficientes. Você possui ` {account.points}/{offer.min_points_req} `",
                color=discord.Color.dark_red(),
            )
            return await interaction.response.send_message(
                embed=no_points_embed,
                ephemeral=True,
            )

        # inviabiliza compra de tipo do item se ja houver comprado. válido até até o proximo reset
        item_type_messages = {
            "HELMET": "Você já pegou um Helmet, pegue o restante do set para ter acesso a novos Helmets",
            "ARMOR": "Você já pegou um Armor, pegue o restante do set para ter acesso a novos Armors",
            "LEGS": "Você já pegou uma Legs, pegue o restante do set para ter acesso a novas Legs.",
            "BOOTS": "Você já pegou uma Bota, pegue o restante do set para ter acesso a novas botas.",
        }

        if offer.item_type in item_type_messages and getattr(
            account, f"got_{offer.item_type.lower()}"
        ):
            embed = discord.Embed(
                title=f"**! {item_type_messages[offer.item_type]} !**",
                color=discord.Color.yellow(),
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # TODO HABILITAR CHECKER autor tentou comprar a propria oferta
        # checa se o autor da oferta tentou comprá-la
        # if interaction.user.id == vendor.id:
        #     return await interaction.response.send_message(
        #         "Você não pode comprar seu prório item!", ephemeral=True
        #     )

        # informações superficiais da oferta de interesse
        vendor_name = getattr(interaction.user, "nick", interaction.user.name)

        embed_offer = discord.Embed(
            title="**NOVA ORDEM DE COMPRA BIS**",
            description="Caso deseje conversar sobre a venda, envie uma dm clicanco na menção.",
            color=discord.Color.yellow(),
        )
        embed_offer.add_field(
            name="",
            value=f"```Item: {offer.item_tier_name} / {offer.item_name}```",
            inline=False,
        )

        # inserir quantidade de compra desejada
        if offer.quantity > 1:
            quantity_to_buy = await interaction.response.send_modal(
                QuantityModal(
                    embed_offer=embed_offer,
                    max_quantity=offer.quantity,
                    offer=offer,
                    vendor=vendor,
                    message=interaction.message,
                )
            )
        else:
            quantity_to_buy = 1

            # feedback

            await interaction.response.send_message(
                f"` Sua intenção de compra foi enviada para `{vendor.mention}",
                ephemeral=True,
            )

            # envia a oferta ao canal do mercado
            await vendor.send(
                content=f"{interaction.user.mention} está interessado nessa oferta {offer.jump_url}",
                embed=embed_offer,
                view=MarketOfferInterestVendorConfirmationBis(
                    buyer=interaction.user,
                    message=interaction.message,
                    quantity_to_buy=quantity_to_buy,
                    offer=offer,
                ),
            )
