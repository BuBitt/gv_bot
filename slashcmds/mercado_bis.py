from datetime import datetime
from typing import List, Literal
import difflib
import time

from errors.errors import IsNegativeError, IsNotLinkError, IsNotLinkError
from models.account import Account
from models.guild import Guild
from models.items_bis import ItemBis

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
    async def item_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> List[app_commands.Choice[str]]:
        itens_tier_name = ItemBis.select(ItemBis.tier_name)
        itens_name = ItemBis.select(ItemBis.item_name)
        items_all = [item.tier_name for item in itens_tier_name] + [
            item.item_name for item in itens_name
        ]

        return [
            app_commands.Choice(name=item, value=item)
            for item in items_all
            if current.lower() in item.lower()
        ]

    @app_commands.command(name="criar", description="Cria uma oferta no market")
    @app_commands.autocomplete(item=item_autocomplete)
    @app_commands.describe(
        item="Nome do item oferecido, EX: T3 Plate Helmet ou Harbinger helmet",
        atributos="Exemplo: INT WIZ WP SP HASTE",
        quantidade="quantidade de itens",
        imagem="Imagem do item com os atributos, envie a imagem no canal imagens e copie o link",
    )
    @app_commands.checks.has_any_role(
        settings.CRAFTER_ROLE,
        settings.VICE_LIDER_ROLE,
        settings.BOT_MANAGER_ROLE,
        settings.LEADER_ROLE,
    )
    async def market_new_offer(
        self,
        interaction: discord.Interaction,
        item: str,
        atributos: str,
        quantidade: int,
        imagem: str,
    ):
        regex = "^https?:\/\/.*\.(png|jpe?g|gif|bmp|tiff?)(\?.*)?$"

        try:
            if not is_valid_regex(imagem, regex):
                raise IsNotLinkError

            else:
                vendor_name = (
                    interaction.user.nick
                    if interaction.user.nick != None
                    else interaction.user.name
                )

                # encontra o tipo de item (helmet, armor, legs ou legs)
                item_lower = item.lower()
                offer_dict = {}

                if "helmet" in item_lower:
                    offer_dict["item_type"] = "HELMET"
                elif "armor" in item_lower:
                    offer_dict["item_type"] = "ARMOR"
                elif "legs" in item_lower:
                    offer_dict["item_type"] = "LEGS"
                elif "boots" in item_lower:
                    offer_dict["item_type"] = "BOOTS"

                # timestamp
                timestamp = str(time.time()).split(".")[0]

                # converte o item para tier_name
                if not item.startswith(("T1", "T2", "T3", "T4", "T5", "T6")):
                    item_name = item
                    item_tier_name = ItemBis.fetch_by_name(item)
                else:
                    item_name = ItemBis.fetch_by_tier_name(item)
                    item_tier_name = item

                # constroi oferta
                offer_dict["member_id"] = interaction.user.id
                offer_dict["member_name"] = vendor_name
                offer_dict["item_tier_name"] = item_tier_name
                offer_dict["item_name"] = item_name
                offer_dict["atributes"] = atributos
                offer_dict["quantity"] = quantidade
                offer_dict["image"] = imagem
                offer_dict["timestamp"] = timestamp

                # encontra o canal mercado
                market_channel = utils.get(
                    interaction.guild.text_channels,
                    id=settings.MARKET_OFFER_CHANNEL_BIS,
                )

                # enconta o ultimo id para definir o N° da oferta
                last_id = (
                    MarketOfferBis.select(MarketOfferBis.id)
                    .order_by(MarketOfferBis.id.desc())
                    .limit(1)
                    .scalar()
                )

                embed_offer = discord.Embed(
                    title=f"",
                    color=discord.Color.dark_purple(),
                    timestamp=datetime.fromtimestamp(int(timestamp)),
                )
                embed_offer.add_field(
                    name="", value=f"**```{item_tier_name.title()}```**"
                )
                embed_offer.add_field(
                    name="", value=f"```Atributos: {atributos.upper()}```", inline=False
                )
                embed_offer.set_footer(
                    text=f"Oferta N° {last_id}  •  {item_name.title()}"
                )

                # get the right tier
                tier_name = f"{item_tier_name[0:2].lower()}_requirement"
                tier = getattr(Guild, tier_name)
                tier_points = Guild.select(tier).first()
                value = getattr(tier_points, tier_name)
                offer_dict["min_points_req"] = value

                embed_offer.add_field(name="", value=f"```{value} Pontos Mínimos```")
                embed_offer.add_field(name="", value=f"```{quantidade} Disponíveis```")
                embed_offer.set_author(
                    name=f"{vendor_name} craftou esse item BIS",
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
                    f"`✪ Sua oferta foi criada: `{message.jump_url}", ephemeral=True
                )

                # log da operação
                log_message_terminal = f"{interaction.user.name} cirou uma nova oferta"
                logger.info(log_message_terminal)

                log_message_ch = f"<t:{str(time.time()).split('.')[0]}:F>` - `{interaction.user.mention}` criou uma nova oferta `{message.jump_url}"
                channel = utils.get(
                    interaction.guild.text_channels, id=settings.ADMIN_LOGS_CHANNEL
                )
                await channel.send(log_message_ch)

                channel_bis = utils.get(
                    interaction.guild.text_channels, id=settings.MARKET_LOG_BIS
                )
                await channel_bis.send(log_message_ch)

        except IsNotLinkError:
            await interaction.response.send_message(
                f"`✪ {imagem} ` não é um link válido.", ephemeral=True
            )

        except IsNegativeError:
            await interaction.response.send_message(
                f"`✪ {item} ` não é um link válido.", ephemeral=True
            )

    @app_commands.command(
        name="procurar",
        description="procura ofertas por item",
    )
    @app_commands.describe(item="busca por item")
    @app_commands.checks.has_any_role(
        settings.MEMBRO_INICIANTE_ROLE,
        settings.MEMBRO_ROLE,
        settings.OFFICER_ROLE,
        settings.COMMANDER_ROLE,
        settings.VICE_LIDER_ROLE,
        settings.LEADER_ROLE,
    )
    async def market_search(self, interaction: discord.Interaction, item: str):
        # Fetch active market offers from the database
        query_search_for = MarketOfferBis.select().where(MarketOfferBis.is_active)

        # Consulta ofertas ativas no mercado no banco de dados
        search_results = [
            (
                offer,
                difflib.SequenceMatcher(
                    None, item.lower(), offer.item_tier_name.lower()
                ).ratio(),
            )
            for offer in query_search_for
        ]

        # Calcula as taxas de similaridade usando list comprehension
        filtered_results = [offer for offer, ratio in search_results if ratio > 0.46]

        if not filtered_results:
            return await interaction.response.send_message(
                f"`Não foram encontradas ofertas com `{item.title()}`.", ephemeral=True
            )

        # Exibe os resultados
        offers = [
            f"{my_offer.jump_url}` → Item: {my_offer.item_tier_name}; Atributos: {my_offer.atributes.upper()};  Quantidade: {my_offer.quantity}; Crafter:`{mention_by_id(my_offer.vendor_id)}"
            for my_offer in filtered_results
        ]
        offers_table = search_offer_table_construct(offers)
        await interaction.response.send_message(
            content=f"{offers_table}", ephemeral=True
        )

    @app_commands.command(
        name="minhas-ofertas",
        description="mostra suas ofertas abertas",
    )
    @app_commands.checks.has_any_role(
        settings.CRAFTER_ROLE,
        settings.VICE_LIDER_ROLE,
        settings.BOT_MANAGER_ROLE,
        settings.LEADER_ROLE,
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
            f"{my_offer.jump_url}` N° {my_offer.id} → Item: {my_offer.item_tier_name}; Atributos: {my_offer.atributes.upper()};  Quantidade: {my_offer.quantity} `"
            for my_offer in query_search_for
        ]

        # Constroi uma tabela com as ofertas ativas
        offers_table = search_offer_table_construct(offers)

        # Envia a tabela contruida
        await interaction.response.send_message(
            content=f"{offers_table}", ephemeral=True
        )

    @app_commands.command(
        name="ver-loja",
        description="mostra as ofertas de um player específico",
    )
    @app_commands.describe(player="Player dono da loja")
    @app_commands.checks.has_any_role(
        settings.MEMBRO_INICIANTE_ROLE,
        settings.MEMBRO_ROLE,
        settings.OFFICER_ROLE,
        settings.COMMANDER_ROLE,
        settings.VICE_LIDER_ROLE,
        settings.LEADER_ROLE,
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
            # Se nenhum resultado for encontrado envia uma mensagem
            return await interaction.response.send_message(
                f"{player.mention}` não possui ofertas ativas. `", ephemeral=True
            )

        # Exibe os resultados
        offers = [
            f"{my_offer.jump_url}` → Item: {my_offer.item_tier_name}; Atributos: {my_offer.atributes.upper()};  Quantidade: {my_offer.quantity} `"
            for my_offer in query_search_for
        ]

        # Constroi uma tabela com as ofertas ativas
        offers_table = search_offer_table_construct(offers)

        # Envia a tabela contruida
        await interaction.response.send_message(
            content=f"**` Loja - {player_name} `**\n{offers_table}", ephemeral=True
        )


async def setup(bot):
    bot.tree.add_command(
        MercadoBisCommands(
            name="bis", description="Comandos para o mercado de itens craftados"
        )
    )
