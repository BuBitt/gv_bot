from datetime import datetime
from typing import List
import difflib
import time

from errors.errors import IsNegativeError, IsNotLinkError, IsNotLinkError

import settings

import discord
from discord import app_commands
from discord import utils

from models.items import Items
from models.mercado_bis import MarketOfferBis

from utils.utilities import is_valid_regex, mention_by_id, search_offer_table_construct
from views.mercado_bis import MarketOfferInterestBis
from database import db


logger = settings.logging.getLogger(__name__)


class MercadoBisCommands(app_commands.Group):
    async def fruit_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> List[app_commands.Choice[str]]:
        itens = Items.select(Items.item)
        items = [item.item for item in list(itens)]
        return [
            app_commands.Choice(name=item, value=item)
            for item in items
            if current.lower() in item.lower()
        ]

    @app_commands.command(
        name="oferecer-test", description="Cria uma oferta no market de craft"
    )
    @app_commands.checks.has_any_role(
        settings.CRAFTER_ROLE, settings.VICE_LIDER_ROLE, settings.BOT_MANAGER_ROLE
    )
    @app_commands.describe(item="Comece a escrever o nome do item")
    @app_commands.autocomplete(item=fruit_autocomplete)
    async def fruits(self, interaction: discord.Interaction, item: str):
        await interaction.response.send_message(f"item: {item}")

    @app_commands.command(name="oferecer", description="Cria uma oferta no market")
    @app_commands.describe(
        item="Nome do item oferecido ex: Cloth T4",
        preço="Preço do item",
        quantidade="quantidade de itens",
        imagem="Imagem do item com os atributos",
    )
    @app_commands.checks.has_any_role(
        settings.CRAFTER_ROLE, settings.VICE_LIDER_ROLE, settings.BOT_MANAGER_ROLE
    )
    async def market_new_offer(
        self,
        interaction: discord.Interaction,
        item: str,
        preço: int,
        quantidade: int,
        imagem: str,
    ):
        regex = (
            "((http|https)://)(www.)?"
            + "[a-zA-Z0-9@:%._\\+~#?&//=]"
            + "{2,256}\\.[a-z]"
            + "{2,6}\\b([-a-zA-Z0-9@:%"
            + "._\\+~#?&//=]*)"
        )

        try:
            if preço < 1 or quantidade < 1:
                raise IsNegativeError

            elif not is_valid_regex(imagem, regex):
                print(is_valid_regex(imagem, regex))
                raise IsNotLinkError

            else:
                vendor_name = (
                    interaction.user.nick
                    if interaction.user.nick != None
                    else interaction.user.name
                )
                timestamp = str(time.time()).split(".")[0]

                # controi oferta
                offer_dict = {}
                offer_dict["member_id"] = interaction.user.id
                offer_dict["member_name"] = vendor_name
                offer_dict["item"] = item
                offer_dict["quantity"] = quantidade
                offer_dict["price"] = preço
                offer_dict["image"] = imagem
                offer_dict["timestamp"] = timestamp

                # encontra o canal mercado
                market_channel = utils.get(
                    interaction.guild.text_channels,
                    id=settings.MARKET_OFFER_CHANNEL_BIS,
                )

                embed_offer = discord.Embed(
                    title=f"",
                    color=discord.Color.dark_green(),
                    timestamp=datetime.fromtimestamp(int(timestamp)),
                )
                embed_offer.add_field(
                    name="", value=f"```{item.title()}```", inline=False
                )
                embed_offer.add_field(name="", value=f"```{preço} Silver```")
                embed_offer.add_field(name="", value=f"```{quantidade} Disponíveis```")
                embed_offer.set_author(
                    name=f"{vendor_name} está vendendo:",
                    icon_url=interaction.user.display_avatar,
                )
                embed_offer.set_image(url=imagem)

                # mensasgem publicada no canal mercado
                message = await market_channel.send(
                    content=" ", embed=embed_offer, view=MarketOfferInterestBis()
                )

                offer_dict["offer_message_id"] = message.id
                offer_dict["offer_jump_url"] = message.jump_url

                # escreve oferta no banco de dados
                db.create_tables([MarketOfferBis])
                MarketOfferBis.new(offer_dict)

                await interaction.response.send_message(
                    f"`► Sua oferta foi criada: `{message.jump_url}", ephemeral=True
                )

                # log da operação
                log_message_terminal = f"{interaction.user.name} cirou uma nova oferta"
                logger.info(log_message_terminal)

                log_message_ch = f"<t:{str(time.time()).split('.')[0]}:F>` - `{interaction.user.mention}` criou uma nova oferta `{message.jump_url}"
                channel = utils.get(
                    interaction.guild.text_channels, id=settings.ADMIN_LOGS_CHANNEL
                )
                await channel.send(log_message_ch)

        except IsNotLinkError:
            await interaction.response.send_message(
                f"`► {imagem} ` não é um link válido.", ephemeral=True
            )

        except IsNegativeError:
            await interaction.response.send_message(
                f"`► {item} ` não é um link válido.", ephemeral=True
            )

    @app_commands.command(
        name="procurar",
        description="procura ofertas por item",
    )
    @app_commands.describe(item="busca por item")
    @app_commands.checks.has_any_role(
        settings.MEMBRO_ROLE, settings.MEMBRO_INICIANTE_ROLE
    )
    async def market_search(self, interaction: discord.Interaction, item: str):
        # Fetch active market offers from the database
        query_search_for = MarketOfferBis.select().where(MarketOfferBis.is_active)

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
            content=f"`    Ofertas:    `\n{offers_table}", ephemeral=True
        )

    @app_commands.command(
        name="minhas-ofertas",
        description="mostra suas ofertas abertas",
    )
    @app_commands.checks.has_any_role(
        settings.CRAFTER_ROLE, settings.VICE_LIDER_ROLE, settings.BOT_MANAGER_ROLE
    )
    async def my_offers(self, interaction: discord.Interaction):
        # Consulta ofertas ativas no mercado no banco de dados
        query_search_for = MarketOfferBis.select().where(
            (MarketOfferBis.vendor_id == interaction.user.id)
            & (MarketOfferBis.is_active == True)
        )

        if not query_search_for:
            # Se nenhum resultado for enquantrado envia uma menságem
            return await interaction.response.send_message(
                "Você não possui ofertas ativas", ephemeral=True
            )

        # Exibe os resultados
        offers = [
            f"{my_offer.jump_url}` N° {my_offer.id} → Item: {my_offer.item}; Preço: {my_offer.price}; Quantidade: {my_offer.quantity} `"
            for my_offer in query_search_for
        ]

        # Constroi uma tabela com as ofertas ativas
        offers_table = search_offer_table_construct(offers)

        # Envia a tabela contruida
        await interaction.response.send_message(
            content=f"`   Ofertas:   `\n{offers_table}", ephemeral=True
        )

    @app_commands.command(
        name="ver-loja",
        description="mostra as ofertas de um player específico",
    )
    @app_commands.describe(player="Player dono da loja")
    @app_commands.checks.has_any_role(
        settings.MEMBRO_ROLE, settings.MEMBRO_INICIANTE_ROLE
    )
    async def player_offers(
        self, interaction: discord.Interaction, player: discord.User
    ):
        # Consulta ofertas ativas no mercado no banco de dados
        query_search_for = MarketOfferBis.select().where(
            (MarketOfferBis.vendor_id == player.id) & (MarketOfferBis.is_active == True)
        )

        player_name = player.nick if player.nick != None else player.name

        if not query_search_for:
            # Se nenhum resultado for enquantrado envia uma menságem
            return await interaction.response.send_message(
                f"{player.mention}` não possui ofertas ativas. `", ephemeral=True
            )

        # Exibe os resultados
        offers = [
            f"{my_offer.jump_url}` → Item: {my_offer.item}; Preço: {my_offer.price}; Quantidade: {my_offer.quantity} `"
            for my_offer in query_search_for
        ]

        # Constroi uma tabela com as ofertas ativas
        offers_table = search_offer_table_construct(offers)

        # Envia a tabela contruida
        await interaction.response.send_message(
            content=f"` Loja de {player_name}: `\n{offers_table}", ephemeral=True
        )


async def setup(bot):
    bot.tree.add_command(
        MercadoBisCommands(
            name="mercado-bis", description="Comandos para o mercado de itens craftados"
        )
    )
