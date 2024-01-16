import difflib
import traceback
import discord
import settings

from models.mercado import MarketOffer
from models.vendas import SellInfo
from utils.utilities import mention_by_id, search_offer_table_construct


class MarketSearchModal(discord.ui.Modal, title="Busque ofertas de um item"):
    item = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Item",
        required=True,
        placeholder="Digite o nome do item",
    )

    async def on_submit(self, interaction: discord.Interaction):
        item = self.item.value

        # Fetch active market offers from the database
        query_search_for = MarketOffer.select().where(MarketOffer.is_active)

        # Consulta ofertas ativas no mercado no banco de dados
        search_results = [
            (
                offer,
                difflib.SequenceMatcher(None, item.lower(), offer.item.lower()).ratio(),
            )
            for offer in query_search_for
        ]

        # Calcula as taxas de similaridade usando list comprehension
        filtered_results = [offer for offer, ratio in search_results if ratio > 0.46]

        if not filtered_results:
            return await interaction.response.send_message(
                f"Não foram encontradas ofertas com `{item.title()}`.", ephemeral=True
            )

        # Exibe os resultados
        offers = [
            f"{my_offer.jump_url}` → Item: {my_offer.item}; Preço: {my_offer.price}; Quantidade: {my_offer.quantity}; Vendedor:`{mention_by_id(my_offer.vendor_id)}"
            for my_offer in filtered_results
        ]
        offers_table = search_offer_table_construct(offers)
        await interaction.response.send_message(
            content=f"{offers_table}", ephemeral=True
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        traceback.print_tb(error.__traceback__)


class MarketDeleteMyOffersModal(discord.ui.Modal, title="Delete uma oferta"):
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

            if not offer.vendor_id == interaction.user.id:
                return await interaction.response.send_message(
                    "Você não é o dono dessa oferta ou ela não existe.", ephemeral=True
                )
            else:
                embed = discord.Embed(
                    title="**Você realmente deseja DELETAR essa oferta?**",
                    color=discord.Color.red(),
                )
                return await interaction.response.send_message(
                    embed=embed,
                    view=MarketDeleteMyOffersView(offer=offer),
                    ephemeral=True,
                )
        except ValueError:
            return await interaction.response.send_message(
                f"` {offer_id} ` não é um número."
            )


class MarketDeleteMyOffersView(discord.ui.View):
    def __init__(self, offer):
        self.offer = offer
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Confirmar Deleção",
        style=discord.ButtonStyle.danger,
        custom_id="delete_my_offer_market",
    )
    async def delete_my_offer_market(
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
            title="**Sua oferta foi deletada.**",
            color=discord.Color.yellow(),
        )
        return await interaction.response.send_message(embed=embed, ephemeral=True)


class MarketVerifyMyOffersModal(discord.ui.Modal, title="Verificar Venda"):
    hash_value = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Comprovante do recibo",
        required=True,
        placeholder="Cole o comprovante aqui",
    )

    async def on_submit(self, interaction: discord.Interaction):
        offer_number = self.hash_value.value
        offer = SellInfo.fetch(offer_number)

        if offer == None:
            embed_invalid = discord.Embed(
                title="**Venda Inexistente.**",
                description="A venda não existe.",
                color=discord.Color.dark_red(),
            )
            return await interaction.response.send_message(
                embed=embed_invalid, ephemeral=True
            )

        # embed comprovante
        embed_offer = discord.Embed(
            title=f"**RECIBO**", color=discord.Color.brand_green()
        )
        embed_offer.add_field(name="", value=f"```Item: {offer.item}```", inline=False)
        embed_offer.insert_field_at(
            name="", value=f"```Oferta N°: {offer.offer_id}```", index=1
        )
        embed_offer.insert_field_at(
            name="", value=f"```Preço: {offer.price}```", index=1
        )
        embed_offer.insert_field_at(
            name="", value=f"```Qte vendida: {offer.quantity}```", index=2
        )
        embed_offer.insert_field_at(
            name="",
            value=f"```Total: {offer.quantity * offer.price}```",
            index=2,
        )

        return await interaction.response.send_message(
            embed=embed_offer, ephemeral=True
        )
