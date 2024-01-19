from datetime import datetime
import difflib
import time

from errors.errors import IsNegativeError, IsNotLinkError, IsNotLinkError

from models.mercado import MarketOffer
import settings

import discord
from discord import app_commands
from discord import utils

from utils.utilities import is_valid_regex, mention_by_id, search_offer_table_construct
from views.mercado import MarketOfferInterest
from database import db


logger = settings.logging.getLogger(__name__)


class MercadoCommands(app_commands.Group):
    @app_commands.command(name="criar", description="Cria uma oferta no market")
    @app_commands.describe(
        item="Nome do item oferecido ex: Cloth T4",
        preço="Preço do item",
        quantidade="quantidade de itens",
        print="Print do item com os atributos, envie no canal de imagens",
    )
    @app_commands.checks.cooldown(3, 60.0, key=lambda i: i.user.id)
    @app_commands.checks.has_any_role(
        settings.MEMBRO_INICIANTE_ROLE,
        settings.MEMBRO_ROLE,
        settings.OFFICER_ROLE,
        settings.COMMANDER_ROLE,
        settings.VICE_LIDER_ROLE,
        settings.LEADER_ROLE,
    )
    async def market_new_offer(
        self,
        interaction: discord.Interaction,
        item: str,
        preço: int,
        quantidade: int,
        print: str,
    ):
        regex = r"^https?://.*\.(png|jpe?g|gif|bmp|tiff?)(\?.*)?$"

        try:
            if preço < 1 or quantidade < 1:
                raise IsNegativeError

            elif not is_valid_regex(print, regex):
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
                offer_dict["image"] = print
                offer_dict["timestamp"] = timestamp

                # encontra o canal mercado
                market_channel = utils.get(
                    interaction.guild.text_channels, id=settings.MARKET_OFFER_CHANNEL
                )

                # encontra o ultimo ID da tabela para definir o número da oferta
                last_id = (
                    MarketOffer.select(MarketOffer.id)
                    .order_by(MarketOffer.id.desc())
                    .limit(1)
                    .scalar()
                )

                embed_offer = discord.Embed(
                    title=f"",
                    color=discord.Color.dark_green(),
                    timestamp=datetime.fromtimestamp(int(timestamp)),
                )
                embed_offer.set_footer(
                    text=f"Oferta N° {last_id + 1}  •  {item.title()}"
                )
                embed_offer.add_field(
                    name="", value=f"**```{item.title()}```**", inline=False
                )
                embed_offer.add_field(name="", value=f"```{preço} Silver```")
                embed_offer.add_field(name="", value=f"```{quantidade} Disponíveis```")
                embed_offer.set_author(
                    name=f"{vendor_name} está vendendo",
                    icon_url=interaction.user.display_avatar,
                )
                embed_offer.set_image(url=print)

                # mensasgem publicada no canal mercado
                message = await market_channel.send(
                    content=" ", embed=embed_offer, view=MarketOfferInterest()
                )

                offer_dict["offer_message_id"] = message.id
                offer_dict["offer_jump_url"] = message.jump_url

                # escreve oferta no banco de dados
                db.create_tables([MarketOffer])
                MarketOffer.new(offer_dict)

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
                    interaction.guild.text_channels, id=settings.MARKET_LOGS
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

    @app_commands.command(
        name="minhas-ofertas",
        description="mostra suas ofertas abertas",
    )
    @app_commands.checks.has_any_role(
        settings.MEMBRO_INICIANTE_ROLE,
        settings.MEMBRO_ROLE,
        settings.OFFICER_ROLE,
        settings.COMMANDER_ROLE,
        settings.VICE_LIDER_ROLE,
        settings.LEADER_ROLE,
    )
    async def my_offers(self, interaction: discord.Interaction):
        # Consulta ofertas ativas no mercado no banco de dados
        query_search_for = MarketOffer.select().where(
            (MarketOffer.vendor_id == interaction.user.id)
            & (MarketOffer.is_active == True)
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
        query_search_for = MarketOffer.select().where(
            (MarketOffer.vendor_id == player.id) & (MarketOffer.is_active == True)
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
            content=f"**` Loja - {player_name} `**\n{offers_table}", ephemeral=True
        )


async def setup(bot):
    bot.tree.add_command(
        MercadoCommands(name="mercado", description="Comandospara o mercado")
    )
