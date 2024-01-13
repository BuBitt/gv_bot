import time
from typing import ValuesView
import discord
import settings
from discord import utils
from models.mercado import MarketOffer


logger = settings.logging.getLogger(__name__)


class MarketOfferInterestVendorConfirmation(discord.ui.View):
    def __init__(self, buyer, message, offer, vendor) -> None:
        self.buyer = buyer
        self.offer = offer
        self.message = message
        self.vendor = vendor
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Vender",
        style=discord.ButtonStyle.success,
        custom_id="vendor_confirmation_button",
    )
    async def vendor_confirmation_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        offer = self.offer
        offer_message = self.message
        print(self.message)

        complete_offer_embed = discord.Embed(
            title="Venda completada!", color=discord.Color.dark_green()
        )

        # edita a mensagem na loja
        await offer_message.edit(
            content=f"`A oferta de `{self.vendor.mention}`.`{self.buyer.mention}` comprou o item: {offer.item} ao preço de {offer.price}",
            view=None,
            embed=complete_offer_embed,
        )

        # embed de confirmação
        embed_offer = discord.Embed(
            title=f"Item: {offer.item}. Preço: {offer.price}",
            color=discord.Color.brand_green(),
        )

        await interaction.response.send_message(
            f"{interaction.user.mention} está interessado na sua oferta {offer.jump_url}",
            embed=embed_offer,
        )
        # log da operação
        log_message_terminal = f"{self.buyer.name} finalizou a oferta do item {offer.item} do player {self.vendor.name}"
        logger.info(log_message_terminal)

        log_message_ch = f"<t:{str(time.time()).split('.')[0]}:F>` - `A oferta de `{self.vendor.mention}`.`{self.buyer.mention}` comprou o item: {offer.item} ao preço de {offer.price}` foi finalizada por `{self.buyer.mention}"
        channel = utils.get(interaction.guild.text_channels, name="logs")

        await channel.send(log_message_ch)


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
        vendor = utils.get(interaction.guild.members, id=offer.member_id)

        # TODO habilitar check
        # checa se o autor da oferta tentou comprá-la
        # if interaction.user.id == vendor.id:
        #     return await interaction.response.send_message("Você não pode comprar seu prório item!", ephemeral=True)

        # informações superficiais da oferta de interesse
        embed_offer = discord.Embed(title=f"Item: {offer.item}. Preço: {offer.price}")

        # feedback
        await interaction.response.send_message(
            f"Sua intenção de compra foi enviada para {vendor.mention}", ephemeral=True
        )

        # envia a oferta ao canal do mercado
        await vendor.send(
            f"{interaction.user.mention} está interessado na sua oferta {offer.jump_url}",
            embed=embed_offer,
            view=MarketOfferInterestVendorConfirmation(
                buyer=interaction.user,
                message=interaction.message,
                offer=offer,
                vendor=vendor,
            ),
        )
