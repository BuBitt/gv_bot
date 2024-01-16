from datetime import datetime
import difflib
import traceback
import discord
import settings

from models.mercado_bis import MarketOfferBis
from models.vendas_bis import SellInfoBis
from utils.utilities import mention_by_id, search_offer_table_construct


class MarketSearchModalBis(discord.ui.Modal, title="Busque ofertas de um item"):
    item = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Item",
        required=True,
        placeholder="Digite o nome do item",
    )

    async def on_submit(self, interaction: discord.Interaction):
        item = self.item.value

        # Fetch active market offers from the database
        query_is_active = MarketOfferBis.select().where(MarketOfferBis.is_active)

        # Consulta ofertas ativas no mercado no banco de dados
        search_results = [
            (
                offer,
                difflib.SequenceMatcher(
                    None, item.lower(), offer.item_tier_name.lower()
                ).ratio(),
            )
            for offer in query_is_active
        ]

        # Calcula as taxas de similaridade usando list comprehension
        filtered_results = [offer for offer, ratio in search_results if ratio > 0.46]

        if not filtered_results:
            return await interaction.response.send_message(
                f"Não foram encontradas ofertas com `{item.title()}`.", ephemeral=True
            )

        # Exibe os resultados
        offers = [
            f"{my_offer.jump_url}` → Item: {my_offer.item_tier_name}; Atributos: {my_offer.atributes.upper()}; Quantidade: {my_offer.quantity}; Vendedor:`{mention_by_id(my_offer.vendor_id)}"
            for my_offer in filtered_results
        ]
        offers_table = search_offer_table_construct(offers)
        await interaction.response.send_message(
            content=f"{offers_table}", ephemeral=True
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        traceback.print_tb(error.__traceback__)


class MarketVerifyMyOffersModalBis(discord.ui.Modal, title="Verificar Venda"):
    hash_value = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Comprovante do recibo",
        required=True,
        placeholder="Cole o comprovante aqui",
    )

    async def on_submit(self, interaction: discord.Interaction):
        offer_number = self.hash_value.value
        offer = SellInfoBis.fetch(offer_number)

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
            title=f"**RECIBO**", color=discord.Color.dark_purple()
        )
        embed_offer.add_field(
            name="",
            value=f"```Item: {offer.item_tier_name} / {offer.item_name}```",
            inline=False,
        )
        embed_offer.insert_field_at(
            name="", value=f"```Oferta N°: {offer.offer_id}```", index=1
        )
        embed_offer.insert_field_at(
            name="", value=f"```Qte entregue: {offer.quantity}```", index=2
        )

        return await interaction.response.send_message(
            embed=embed_offer, ephemeral=True
        )
