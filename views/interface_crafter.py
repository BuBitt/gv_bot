import discord

import settings
from models.mercado_bis import MarketOfferBis


class MarketDeleteMyOffersModalBis(discord.ui.Modal, title="Delete uma oferta"):
    offer_id = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Número da Oferta",
        required=True,
        placeholder="Digite o Número da Oferta",
    )

    async def on_submit(self, interaction: discord.Interaction):
        offer_id = self.offer_id.value

        try:
            offer_id = int(offer_id)
            offer = MarketOfferBis.fetch_by_id(offer_id)

            if not offer.vendor_id == interaction.user.id:
                return await interaction.response.send_message(
                    "Você não é o dono dessa oferta ou ela não existe."
                )
            else:
                embed = discord.Embed(
                    title="**Você realmente deseja DELETAR essa oferta?**",
                    color=discord.Color.red(),
                )
                return await interaction.response.send_message(
                    embed=embed,
                    view=MarketDeleteMyOffersViewBis(offer=offer),
                    ephemeral=True,
                )
        except ValueError:
            return await interaction.response.send_message(
                f"` {offer_id} ` não é um número."
            )


class MarketDeleteMyOffersViewBis(discord.ui.View):
    def __init__(self, offer):
        self.offer = offer
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Confirmar Deleção",
        style=discord.ButtonStyle.danger,
        custom_id="delete_my_offer_market_bis",
    )
    async def delete_my_offer_market_bis(
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
            title="**Sua oferta foi deletada.**",
            color=discord.Color.yellow(),
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)
