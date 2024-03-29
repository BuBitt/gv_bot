import discord
from discord import utils

from peewee import *

from discord import app_commands
from beautifultable import BeautifulTable

import settings
from models.account import Account


logger = settings.logging.getLogger(__name__)


def truncar_string(input_string, max_length=17):
    if len(input_string) > max_length:
        result = input_string[: max_length - 3] + "…"
        return result
    else:
        return input_string


class Rankings(app_commands.Group):
    @app_commands.command(
        name="geral", description="Mostra o ranking de pontuação geral da guilda"
    )
    @app_commands.checks.has_any_role(
        settings.MEMBRO_INICIANTE_ROLE,
        settings.MEMBRO_ROLE,
        settings.OFFICER_ROLE,
        settings.COMMANDER_ROLE,
        settings.VICE_LIDER_ROLE,
        settings.LEADER_ROLE,
    )
    @app_commands.checks.cooldown(5, 300.0, key=lambda i: i.user.id)
    async def geral(self, interaction: discord.Interaction):
        account = Account.fetch(interaction)

        # Define a window function using ROW_NUMBER()
        window_function = fn.ROW_NUMBER().over(order_by=[Account.points.desc()])

        # Construct the query with the window function
        account_query = Account.select(
            Account.user_name,
            Account.user_id,
            Account.points,
            window_function.alias("row_number"),
        ).order_by(Account.points.desc())

        general_position = (
            Account.select(
                account_query.c.user_id,
                account_query.c.points,
                account_query.c.row_number,
            )
            .from_(account_query)
            .where(account_query.c.user_id == str(interaction.user.id))
        )

        # Get position
        for pos in general_position:
            points = pos.points
            general_rank_position = pos.row_number

        table = BeautifulTable()
        table.set_style(BeautifulTable.STYLE_NONE)

        headers = ["", " ", "  "]
        table.columns.header = headers

        table.columns.alignment[""] = BeautifulTable.ALIGN_RIGHT
        table.columns.alignment[" "] = BeautifulTable.ALIGN_LEFT
        table.columns.alignment["  "] = BeautifulTable.ALIGN_RIGHT

        for user in account_query.limit(30):
            try:
                user_object = utils.get(interaction.guild.members, id=int(user.user_id))

                name = (
                    user_object.name if user_object.nick == None else user_object.nick
                )
            except:
                name = user.user_name

            row = [
                user.row_number,
                truncar_string(name),
                round(user.points),
            ]
            table.rows.append(row)

        user_name = (
            interaction.user.nick
            if interaction.user.nick != None
            else interaction.user.name
        )

        embed_position = discord.Embed(
            title=f"**`{user_name}`**  •  Posição: `{general_rank_position}`  •  Pontos: **`{points}`**",
            color=discord.Color.yellow(),
        )
        table.show_headers = False
        embed_ranking = discord.Embed(
            title="**Ranking Geral - TOP 30**", color=discord.Color.dark_purple()
        )
        embed_ranking.add_field(name=" ", value=f"```{table}```", inline=False)

        logger.info(
            f"{interaction.user.nick}(ID: {interaction.user.id}) consultou o rank geral"
        )

        await interaction.response.send_message(embeds=[embed_ranking, embed_position])


async def setup(bot):
    bot.tree.add_command(Rankings(name="rank", description="Comandos do ranking"))
