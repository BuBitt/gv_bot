import discord
from models.mercado import MarketOffer

import settings
from models.mercado_bis import MarketOfferBis


# MERCADO BIS
class MarketAdminDeleteOffersModalBis(discord.ui.Modal, title="Delete uma oferta"):
    offer_id = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Número da Oferta",
        required=True,
        placeholder="Digite o Número da Oferta",
    )

    async def on_submit(self, interaction: discord.Interaction):
        offer_id = self.offer_id.value.strip()

        try:
            offer_id = int(offer_id)
            offer = MarketOfferBis.fetch_by_id(offer_id)

            embed = discord.Embed(
                title="**Você realmente deseja DELETAR essa oferta?**",
                color=discord.Color.red(),
            )
            return await interaction.response.send_message(
                embed=embed,
                view=MarketAdminDeleteOffersViewBis(offer=offer),
                ephemeral=True,
            )
        except ValueError:
            return await interaction.response.send_message(
                f"` {offer_id} ` não é um número."
            )


class MarketAdminDeleteOffersViewBis(discord.ui.View):
    def __init__(self, offer):
        self.offer = offer
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Confirmar Deleção",
        style=discord.ButtonStyle.danger,
        custom_id="admin_delete_offer_market_bis",
    )
    async def admin_delete_offer_market_bis(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        offer = self.offer
        offer.is_active = False
        offer.save()

        message = await discord.utils.get(
            interaction.guild.text_channels, id=settings.MARKET_OFFER_CHANNEL_BIS
        ).fetch_message(offer.message_id)

        await message.delete()

        embed = discord.Embed(
            title="**Essa oferta foi deletada.**",
            color=discord.Color.yellow(),
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)


#   MERCADO COMUM
class MarketAdminDeleteOffersModal(discord.ui.Modal, title="Delete uma oferta"):
    offer_id = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Número da Oferta",
        required=True,
        placeholder="Digite o Número da Oferta",
    )

    async def on_submit(self, interaction: discord.Interaction):
        offer_id = self.offer_id.value.strip()

        try:
            offer_id = int(offer_id)
            offer = MarketOffer.fetch_by_id(offer_id)

            embed = discord.Embed(
                title="**Você realmente deseja DELETAR essa oferta?**",
                color=discord.Color.red(),
            )
            return await interaction.response.send_message(
                embed=embed,
                view=MarketAdminDeleteOffersView(offer=offer),
                ephemeral=True,
            )
        except ValueError:
            return await interaction.response.send_message(
                f"` {offer_id} ` não é um número."
            )
        except discord.errors.NotFound:
            return await interaction.response.send_message(
                f"Oferta ` {offer_id} ` não foi encontrada."
            )


class MarketAdminDeleteOffersView(discord.ui.View):
    def __init__(self, offer):
        self.offer = offer
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Confirmar Deleção",
        style=discord.ButtonStyle.danger,
        custom_id="admin_delete_offer_market",
    )
    async def admin_delete_offer_market(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        offer = self.offer
        offer.is_active = False
        offer.save()

        message = await discord.utils.get(
            interaction.guild.text_channels, id=settings.MARKET_OFFER_CHANNEL
        ).fetch_message(offer.message_id)

        await message.delete()

        embed = discord.Embed(
            title="**Essa oferta foi deletada.**",
            color=discord.Color.yellow(),
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)

