from datetime import datetime
from typing import List
import difflib
import time

from errors.errors import IsNegativeError, IsNotLinkError, IsNotLinkError
from models.guild import Guild
from models.items_bis import ItemBis

import settings
from beautifultable import BeautifulTable

import discord
from discord import app_commands
from discord import utils

import settings
from models.items import Items
from models.mercado_bis import MarketOfferBis

from utils.utilities import (
    constroi_tabela,
    enviar_loja_table_construct,
    is_valid_regex,
    mention_by_id,
    search_offer_table_construct,
    separate_offers_by_name,
)
from views.mercado_bis import MarketOfferInterestBis
from database import db


logger = settings.logging.getLogger(__name__)


def completar_string(input_string, max_length=17):
    if len(input_string) < max_length:
        result = input_string + (max_length - len(input_string)) * " "
        return result
    else:
        return input_string


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
        print="Print do item com os atributos, envie o print no canal imagens e copie o link",
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
        print: str,
    ):
        regex = r"^https?://.*\.(png|jpe?g|gif|bmp|tiff?)(\?.*)?$"

        try:
            if not is_valid_regex(print, regex):
                raise IsNotLinkError

            else:
                vendor_name = (
                    interaction.user.nick
                    if interaction.user.nick != None
                    else interaction.user.name
                )

                # encontra o tipo de item (helmet, armor, legs legs, and weapons)
                item_lower = item.lower()
                offer_dict = {}

                item_type_mapping = {
                    "helmet": "HELMET",
                    "armor": "ARMOR",
                    "legs": "LEGS",
                    "boots": "BOOTS",
                    "bow": "BOW",
                    "shield": "SHIELD",
                    "staff": "STAFF",
                    "sceptre": "SCEPTRE",
                    "buckler": "BUCKLER",
                    "light blade": "LIGHT BLADE",
                    "hammer": "HAMMER",
                    "greatsword": "SWORD",
                    "greateaxe": "AXE",
                    "dagger": "DAGGER",
                    "club": "CLUB",
                }

                for keyword, item_type in item_type_mapping.items():
                    if keyword in item_lower:
                        offer_dict["item_type"] = item_type
                        break

                # timestamp
                timestamp = str(time.time()).split(".")[0]

                # converte o item para tier_name
                if not item.startswith(("T2", "T3", "T4", "T5", "T6")):
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
                offer_dict["image"] = print
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
                    text=f"Oferta N° {last_id + 1}  •  {item_name.title()}"
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
                embed_offer.set_image(url=print)

                # mensasgem publicada no canal mercado
                message = await market_channel.send(
                    content=" ", embed=embed_offer, view=MarketOfferInterestBis()
                )

                offer_dict["offer_message_id"] = message.id
                offer_dict["offer_jump_url"] = message.jump_url

                await interaction.response.send_message(
                    f"`✪ Sua oferta foi criada: `{message.jump_url}", ephemeral=True
                )

                # enviar no chat geral
                guild_channel = utils.get(
                    interaction.guild.text_channels, id=settings.GUILD_CHAT
                )
                embed = discord.Embed(
                    title=f"**`{offer_dict.get('member_name')}`** postou um novo item BIS no mercado",
                    color=discord.Color.dark_purple(),
                    description=f"_Clique na `#` para ir até a ofeta_\n{message.jump_url}**` {offer_dict.get('item_tier_name')} • {offer_dict.get('atributes')} `**",
                )
                geral_chat_msg = await guild_channel.send(embed=embed)
                offer_dict["guild_msg_chat_id"] = geral_chat_msg.id

                # escreve oferta no banco de dados
                db.create_tables([MarketOfferBis])
                MarketOfferBis.new(offer_dict)

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
                f"`✪ {print} ` não é um link válido.", ephemeral=True
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
        description="envia sua loja é um bom formato no chat",
    )
    @app_commands.checks.has_any_role(
        settings.MEMBRO_INICIANTE_ROLE,
        settings.MEMBRO_ROLE,
        settings.OFFICER_ROLE,
        settings.COMMANDER_ROLE,
        settings.VICE_LIDER_ROLE,
        settings.LEADER_ROLE,
    )
    async def player_send_offers_bis(
        self, interaction: discord.Interaction, player: discord.User
    ):
        # Consulta ofertas ativas no mercado no banco de dados
        query_search_for = (
            MarketOfferBis.select()
            .where(
                (MarketOfferBis.vendor_id == player.id)
                & (MarketOfferBis.is_active == True)
            )
            .order_by(MarketOfferBis.item_tier_name.desc())
        )

        player_name = player.nick if player.nick != None else player.name

        if not query_search_for:
            # Se nenhum resultado for encontrado envia uma mensagem
            return await interaction.response.send_message(
                f"{player.mention}` não possui ofertas ativas. `",
                ephemeral=True,
            )

        offers = [
            f"{my_offer.jump_url}` → {completar_string(my_offer.item_tier_name)} • {my_offer.atributes.upper()} `"
            for my_offer in query_search_for
        ]
        separate_offers = separate_offers_by_name(offers)

        table_construct = enviar_loja_table_construct(separate_offers)

        embed = discord.Embed(
            title=f"**``` Loja - {player_name} ```**",
            description=f"Clique na `#` para ir até a ofeta\n\n{table_construct}",
            color=discord.Color.dark_purple(),
        )
        return await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="enviar-loja",
        description="envia sua loja é um bom formato no chat",
    )
    @app_commands.checks.has_any_role(
        settings.CRAFTER_ROLE,
        settings.VICE_LIDER_ROLE,
        settings.LEADER_ROLE,
    )
    async def player_send_offers(self, interaction: discord.Interaction):
        # Consulta ofertas ativas no mercado no banco de dados
        query_search_for = (
            MarketOfferBis.select()
            .where(
                (MarketOfferBis.vendor_id == interaction.user.id)
                & (MarketOfferBis.is_active == True)
            )
            .order_by(MarketOfferBis.item_tier_name.desc())
        )

        player_name = (
            interaction.user.nick
            if interaction.user.nick != None
            else interaction.user.name
        )

        if not query_search_for:
            # Se nenhum resultado for encontrado envia uma mensagem
            return await interaction.response.send_message(
                f"{interaction.user.mention}` não possui ofertas ativas. `",
                ephemeral=True,
            )

        offers = [
            f"{my_offer.jump_url}` → {my_offer.item_tier_name} • {my_offer.atributes.upper()} `"
            for my_offer in query_search_for
        ]
        offers_table = search_offer_table_construct(offers)
        embed = discord.Embed(
            title=f"**``` Loja - {player_name} ```**",
            description=f"{offers_table}",
            color=discord.Color.dark_purple(),
        )
        return await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="itens",
        description="envia a pontuação dos itens no chat",
    )
    @app_commands.checks.has_any_role(
        settings.MEMBRO_INICIANTE_ROLE,
        settings.MEMBRO_ROLE,
        settings.OFFICER_ROLE,
        settings.COMMANDER_ROLE,
        settings.VICE_LIDER_ROLE,
        settings.LEADER_ROLE,
    )
    async def items_poits(self, interaction: discord.Interaction):
        # busca no banco de dados os itens com pontuação diferente de 1
        items = (
            Items.select()
            .where(Items.points != 1)
            .order_by(Items.points.desc())
            .execute()
        )

        # cria a tabela com as pontuações
        table_items = BeautifulTable()
        table_items.set_style(BeautifulTable.STYLE_COMPACT)

        headers = ["ITEM", "PONTOS"]
        table_items.columns.header = headers

        table_items.columns.alignment["ITEM"] = BeautifulTable.ALIGN_LEFT
        table_items.columns.alignment["PONTOS"] = BeautifulTable.ALIGN_RIGHT

        items = list(items)

        for item in items:
            row = [item.item, item.points]
            table_items.rows.append(row)

        # cria o embed de pontuações
        embed = discord.Embed(
            title="**Pontuação dos Itens**",
            description="Todos os itens que não estão nessa lista\nvalem `1.0` ponto.",
            color=discord.Color.purple(),
        )
        embed.add_field(name="", value=f"```{table_items}```")

        logger.info(
            f"{interaction.user.nick}(ID: {interaction.user.id}) consultou a pontuação geral dos itens."
        )

        # envia apontuação
        return await interaction.response.send_message(embed=embed)


async def setup(bot):
    bot.tree.add_command(
        MercadoBisCommands(
            name="bis", description="Comandos para o mercado de itens craftados"
        )
    )
