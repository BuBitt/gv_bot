from models.mercado_bis import MarketOfferBis
import settings as st
from discord.ext import commands, tasks

import discord
from discord.ext import commands, tasks
import settings

from datetime import datetime, timedelta, timezone


logger = settings.logging.getLogger(__name__)


class BackgroundTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_offer_time.add_exception_type(Exception)
        self.check_offer_time.start()

    def cog_unload(self) -> None:
        self.check_offer_time.stop()

    # Checagem de ofertas ativas
    @tasks.loop(hours=1)  # Roda a cada 1 hora
    async def check_offer_time(self):
        try:
            gv_guild = self.bot.guilds[0]
            channel = discord.utils.get(
                gv_guild.text_channels, id=settings.MARKET_OFFER_CHANNEL_BIS
            )

            if not channel:
                print("Channel not found.")
                return

            current_time = datetime.now(timezone.utc)

            async for message in channel.history(limit=None):
                offer = MarketOfferBis.fetch(message.id)

                gv_guild = self.bot.guilds[0]
                channel = discord.utils.get(
                    gv_guild.text_channels, id=settings.MARKET_OFFER_CHANNEL_BIS
                )
                vendor = discord.utils.get(gv_guild.members, id=offer.vendor_id)

                # calcula a diferença de tempo entre as ofertas e agora
                time_difference = current_time - message.created_at

                # verifica se 23 horas parrasaram (aviso de deleção)
                if time_difference >= timedelta(hours=23):
                    embed = discord.Embed(
                        title=f"**Seu item {message.jump_url} será deletado em 1 hora.**",
                        color=discord.Color.yellow(),
                    )
                    await vendor.send(embed=embed)

                # verifica se 24 horas parrasaram (avisodeleção)
                if time_difference >= timedelta(hours=24):
                    offer.is_active = False

                    embed = discord.Embed(
                        title="Seu item foi deletado do mercado.",
                        color=discord.Color.yellow(),
                    )
                    embed.set_image(url=offer.image)

                    await vendor.send(embed=embed)
                    await message.delete()

                    offer.save()

        except Exception as e:
            print(e)

    @commands.command()
    async def start(self, ctx):
        self.check_offer_time.start()

    @commands.command()
    async def cancel(self, ctx):
        self.check_offer_time.cancel()

    @commands.command()
    async def change(self, ctx, seconds: int):
        self.check_offer_time.change_interval(seconds=seconds)

    @check_offer_time.before_loop
    async def before_check_users(self):
        logger.warn("Iniciando Checagem diária de ofertas")

    @check_offer_time.after_loop
    async def after_check_users(self):
        logger.warn("Ofertas BIS com mais de 24 horas foram deletadas.")


async def setup(bot):
    await bot.add_cog(BackgroundTasks(bot))
