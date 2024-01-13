import time
from datetime import datetime
from errors.errors import IsNegativeError, IsNotLinkError, IsNotLinkError

import settings
from models.mercado import MarketOffer

import discord
from discord import app_commands
from discord import utils

from utils.utilities import is_valid_regex
from views.mercado import MarketOfferInterest
from database import db


logger = settings.logging.getLogger(__name__)


# TODO adicionar has_any_roles para vice_lider e remover crafter
# TODO selfcheck para não dar pontos a si mesmo


# TODO Validador de link
class MercadoCommands(app_commands.Group):
    @app_commands.command(name="oferecer", description="Cria uma oferta no market")
    @app_commands.describe(
        item="Nome do item oferecido ex: Cloth T4",
        preço="Preço do item",
        imagem="Imagem do item com os atributos",
    )
    @app_commands.checks.has_any_role("Membro", "Membro Iniciante")
    async def market_new_offer(
        self,
        interaction: discord.Interaction,
        item: str,
        preço: int,
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
            if preço < 1:
                raise IsNegativeError
            # elif not is_valid_regex(imagem, regex):
            #     raise IsNotLinkError
            else:
                user_name = (
                    interaction.user.nick
                    if interaction.user.nick != None
                    else interaction.user.name
                )
                timestamp = str(time.time()).split(".")[0]

                # controi oferta
                offer_dict = {}
                offer_dict["member_id"] = interaction.user.id
                offer_dict["member_name"] = user_name
                offer_dict["item"] = item
                offer_dict["price"] = preço
                offer_dict["image"] = imagem
                offer_dict["timestamp"] = timestamp

                # encontra o canal mercado
                market_channel = utils.get(
                    interaction.guild.text_channels, name="mercado"
                )

                embed_offer = discord.Embed(
                    title=f"",
                    color=discord.Color.dark_green(),
                    timestamp=datetime.fromtimestamp(int(timestamp)),
                )
                embed_offer.add_field(name="", value=f"```{item.title()}```")
                embed_offer.add_field(name="", value=f"```{preço} Silver```")
                embed_offer.set_author(
                    name=f"Vendedor: {user_name}",
                    icon_url=interaction.user.display_avatar,
                )
                embed_offer.set_image(url=imagem)

                # mensasgem publicada no canal mercado
                message = await market_channel.send(
                    content=" ", embed=embed_offer, view=MarketOfferInterest()
                )
                print(message.id)
                offer_dict["offer_message_id"] = message.id
                offer_dict["offer_jump_url"] = message.jump_url

                # escreve oferta no banco de dados
                db.create_tables([MarketOffer])
                MarketOffer.new(offer_dict)

                await interaction.response.send_message(
                    f"`Sua oferta foi criada: `{message.jump_url}", ephemeral=True
                )

                print(interaction.message)

                # log da operação
                log_message_terminal = f"{interaction.user.name} cirou uma nova oferta"
                logger.info(log_message_terminal)

                log_message_ch = f"<t:{str(time.time()).split('.')[0]}:F>` - `{interaction.user.mention}` criou uma nova oferta `{message.jump_url}"
                channel = utils.get(interaction.guild.text_channels, name="logs")
                await channel.send(log_message_ch)

        except IsNotLinkError:
            await interaction.response.send_message(
                f"` {imagem} ` não é um link válido.", ephemeral=True
            )

        except IsNegativeError:
            await interaction.response.send_message(
                f"` {item} ` não é um link válido.", ephemeral=True
            )

    @app_commands.command(
        name="procurar",
        description="procura ofertas por item",
    )
    @app_commands.describe(item="item que deseja buscar")
    @app_commands.checks.has_any_role("Membro", "Membro Iniciante")
    async def market_search(self, interaction: discord.Interaction, item: str):
        await interaction.response.send_message("test", ephemeral=True)

    @app_commands.command(
        name="minhas-ofertas",
        description="mostra suas ofertas abertas",
    )
    @app_commands.checks.has_any_role("Membro", "Membro Iniciante")
    async def my_offers(self, interaction: discord.Interaction):
        await interaction.response.send_message("test", ephemeral=True)


async def setup(bot):
    bot.tree.add_command(
        MercadoCommands(name="mercado", description="Comandospara o mercado")
    )
