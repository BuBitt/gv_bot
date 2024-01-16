import hashlib
import secrets
import string
import time
import discord
from models.vendas import SellInfo
import settings
import traceback
from discord import utils
from datetime import datetime
from models.mercado import MarketOffer
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

                # adiciona quantidade a comprar e total de silver
                self.embed_offer.add_field(
                    name="", value=f"```Qte: {quantity_to_buy}```"
                )
                self.embed_offer.add_field(
                    name="",
                    value=f"```Total: {quantity_to_buy * self.offer.price} Silver```",
                )

                # envia a oferta ao canal do mercado
                await vendor.send(
                    content=f"{interaction.user.mention}` está interessado na sua oferta `{self.offer.jump_url}",
                    embed=self.embed_offer,
                    view=MarketOfferInterestVendorConfirmation(
                        buyer=interaction.user,
                        message=self.message,
                        quantity_to_buy=quantity_to_buy,
                        offer=self.offer,
                        vendor=vendor,
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


class MarketOfferInterestVendorConfirmation(discord.ui.View):
    def __init__(self, buyer, message, offer, vendor, quantity_to_buy) -> None:
        self.buyer = buyer
        self.offer = offer
        self.vendor = vendor
        self.message = message
        self.quantity_to_buy = quantity_to_buy
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Vender",
        style=discord.ButtonStyle.success,
        custom_id="vendor_confirmation_button",
    )
    async def vendor_confirmation_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        # verifica se a ordem ainda está ativa
        offer = MarketOffer.fetch_by_jump_url(self.offer.jump_url)
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
            title=f"**RECIBO**", color=discord.Color.brand_green(), timestamp=timestamp
        )
        embed_offer.add_field(
            name="", value=f"```Item: {self.offer.item}```", inline=False
        )
        embed_offer.insert_field_at(
            name="", value=f"```Oferta N°: {self.offer.id}```", index=1
        )
        embed_offer.insert_field_at(
            name="", value=f"```Preço: {self.offer.price}```", index=1
        )
        embed_offer.insert_field_at(
            name="", value=f"```Qte vendida: {self.quantity_to_buy}```", index=2
        )
        embed_offer.insert_field_at(
            name="",
            value=f"```Total: {self.quantity_to_buy * self.offer.price}```",
            index=2,
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
        sell_dict["item"] = self.offer.item
        sell_dict["price"] = self.offer.price
        sell_dict["quantity"] = self.quantity_to_buy
        sell_dict["timestamp"] = datetime.fromtimestamp(int(time.time()))
        sell_dict["hash_proof"] = sha256_hash
        SellInfo.new(sell_dict)

        # envia feedback
        await interaction.message.edit(
            content=f"`✪ Venda concluída. {self.quantity_to_buy} {self.offer.item} para `{self.buyer.mention}",
            embed=embed_offer,
            view=None,
        )
        await self.buyer.send(
            content=f"`✪ Compra concluída. Você comprou {self.quantity_to_buy} {self.offer.item} de `{self.vendor.mention}",
            embed=embed_offer,
        )

        # update offer no db
        self.offer.buyer_id = interaction.user.id

        # calcula a quantidade de itens restante
        remain = self.offer.quantity - self.quantity_to_buy
        self.offer.quantity = remain

        # deleta mensagem de confirmação de venda
        if remain == 0:
            # muda o status da oferta no db e deleta oferta no canal ofertas
            self.offer.is_active = False
            await self.message.delete()

        else:
            offer = self.offer
            embed_offer = discord.Embed(
                title=f"",
                color=discord.Color.dark_green(),
                timestamp=datetime.fromtimestamp(int(self.offer.timestamp)),
            )
            embed_offer.add_field(
                name="", value=f"```{offer.item.title()}```", inline=False
            )
            embed_offer.set_footer(text=f"**```OFERTA N° {offer.id}```**")
            embed_offer.add_field(name="", value=f"```{offer.price} Silver```")
            embed_offer.add_field(name="", value=f"```{offer.quantity} Disponíveis```")
            embed_offer.set_author(
                name=f"{offer.vendor_name} criou essa oferta",
                icon_url=interaction.user.display_avatar,
            )
            embed_offer.set_image(url=offer.image)

            await self.message.edit(embed=embed_offer, view=MarketOfferInterest())

        self.offer.save()

        # log da operação
        log_message_terminal = f"Oferta N° {self.offer.id}: O vendedor {self.vendor.name} finalizou a oferta do item {self.offer.item}. Comprador: {self.buyer.name}"
        logger.info(log_message_terminal)

        timestamp = str(time.time()).split(".")[0]
        log_message_ch = f"<t:{timestamp}:F>` - Oferta N° {self.offer.id} teve uma compra. - `{self.buyer.mention}` comprou o item: {self.offer.item} ao preço de {self.offer.price} do vendedor:`{self.vendor.mention}"

        log_channel = utils.get(
            self.message.guild.text_channels, id=settings.ADMIN_LOGS_CHANNEL
        )
        log_mkt_channel = utils.get(
            self.message.guild.text_channels, id=settings.MARKET_LOGS
        )

        # envia msg aos canais de log
        await log_channel.send(log_message_ch)
        await log_mkt_channel.send(log_message_ch)


class MarketOfferInterest(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Tenho Interesse",
        style=discord.ButtonStyle.success,
        custom_id="interest_in_offer_button",
    )
    async def interest_in_offer_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        # encontra a oferta
        offer = MarketOffer.fetch(interaction.message.id)
        vendor = utils.get(interaction.guild.members, id=offer.vendor_id)

        # TODO HABILITAR CHECKER autor tentou comprar a propria oferta
        # checa se o autor da oferta tentou comprá-la
        # if interaction.user.id == vendor.id:
        #     return await interaction.response.send_message(
        #         "Você não pode comprar seu prório item!", ephemeral=True
        #     )

        # informações superficiais da oferta de interesse
        embed_offer = discord.Embed(
            title="**NOVA ORDEM DE COMPRA**",
            description="Caso deseje conversar sobre a venda, envie uma dm clicanco na menção.",
            color=discord.Color.yellow(),
        )
        embed_offer.add_field(name="", value=f"```Item: {offer.item}```")
        embed_offer.add_field(name="", value=f"```Item: {offer.price}```")

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
            embed_offer.add_field(name="", value=f"```Qte: {quantity_to_buy}```")
            embed_offer.add_field(
                name="",
                value=f"```Total Silver: {quantity_to_buy * offer.price}```",
            )

            # envia a oferta ao canal do mercado
            await vendor.send(
                content=f"{interaction.user.mention} está interessado nessa oferta {offer.jump_url}",
                embed=embed_offer,
                view=MarketOfferInterestVendorConfirmation(
                    buyer=interaction.user,
                    message=interaction.message,
                    quantity_to_buy=quantity_to_buy,
                    offer=offer,
                    vendor=vendor,
                ),
            )
