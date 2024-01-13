import time
import discord
import settings
from discord import utils
from models.mercado import MarketOffer


logger = settings.logging.getLogger(__name__)


class MarketOfferInterestVendorConfirmation(discord.ui.View):
    def __init__(self, buyer, message, offer, vendor) -> None:
        self.buyer = buyer
        self.offer = offer
        self.vendor = vendor
        self.message = message
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Vender",
        style=discord.ButtonStyle.success,
        custom_id="vendor_confirmation_button",
    )
    async def vendor_confirmation_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        # edita a mensagem na loja
        await self.message.delete()

        # embed de confirmação
        embed_offer = discord.Embed(
            title=f"Item: {self.offer.item}. Preço: {self.offer.price}. Oferta: {self.offer.id}",
            color=discord.Color.brand_green(),
        )

        # deleta mensagem de confirmação de venda
        await interaction.message.delete()

        # envia feedback
        await interaction.response.send_message(
            content=f"Vendido para {self.buyer.mention}",
            embed=embed_offer,
            ephemeral=True,
        )

        # update offer status on db
        self.offer.is_active = False
        self.offer.buyer_id = self.buyer.id
        self.offer.save()

        # log da operação
        log_message_terminal = f"Oferta N° {self.offer.id}: O vendedor {self.vendor.name} finalizou a oferta do item {self.offer.item}. Comprador: {self.buyer.name}"
        logger.info(log_message_terminal)

        timestamp = str(time.time()).split(".")[0]
        log_message_ch = f"<t:{timestamp}:F>` - Oferta N° {self.offer.id} foi finalizada. Vendedor:`{self.vendor.mention}` - `{self.buyer.mention}` comprou o item: {self.offer.item} ao preço de {self.offer.price} `"

        log_channel = utils.get(self.message.guild.text_channels, name="logs")
        log_mkt_channel = utils.get(
            self.message.guild.text_channels, name="mercado-logs"
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

        # TODO habilitar check
        # checa se o autor da oferta tentou comprá-la
        if interaction.user.id == vendor.id:
            return await interaction.response.send_message("Você não pode comprar seu prório item!", ephemeral=True)

        # informações superficiais da oferta de interesse
        embed_offer = discord.Embed(title=f"Item: {offer.item}. Preço: {offer.price}")

        # feedback
        await interaction.response.send_message(
            f"Sua intenção de compra foi enviada para {vendor.mention}", ephemeral=True
        )

        # envia a oferta ao canal do mercado
        await vendor.send(
            content=f"{interaction.user.mention} está interessado na sua oferta {offer.jump_url}",
            embed=embed_offer,
            view=MarketOfferInterestVendorConfirmation(
                buyer=interaction.user,
                message=interaction.message,
                offer=offer,
                vendor=vendor,
            ),
        )
