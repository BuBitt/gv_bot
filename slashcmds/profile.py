import discord
import polars as pl
from database import db_name
from discord import app_commands
from models.account import Account
from sqlalchemy import create_engine
from views.profile import UserProfileView, GuildProfileView


# Polars configs
def transactions_table(bool=False):
    pl.Config.set_tbl_cols(10)
    pl.Config.set_tbl_rows(10)
    pl.Config.set_fmt_str_lengths(18)
    pl.Config.set_tbl_formatting("NOTHING")
    pl.Config.set_tbl_hide_dataframe_shape(True)
    pl.Config.set_tbl_hide_column_data_types(True)
    pl.Config.set_tbl_cell_numeric_alignment("RIGHT")
    if bool:
        pl.Config.set_tbl_rows(100)
        pl.Config.set_fmt_str_lengths(30)

    conn = create_engine(f"sqlite:///{db_name}")
    query = "SELECT * FROM transactions"
    return pl.read_database(query=query, connection=conn.connect())


class Profile(app_commands.Group):
    @app_commands.command(description="seu perfil")
    async def me(self, interaction: discord.Interaction):
        account = Account.fetch(interaction)
        embed_me = discord.Embed()
        embed_me.set_author(
            name=f"Perfil de {interaction.user.name if interaction.user.nick == None else interaction.user.nick}",
            icon_url=interaction.user.display_avatar,
        )
        table = transactions_table()
        table = (
            table.filter(pl.col("requester_id") == interaction.user.id)
            .select("id", "manager_name", "item", "quantity")
            .sort("id", descending=True)
        )
        table = table.rename(
            {
                "id": "N°",
                "manager_name": "GUILD BANKER",
                "item": "ITEM",
                "quantity": "QUANTIDADE",
            }
        )

        embed_me.add_field(name="**Level**", value=account.level)
        embed_me.add_field(name="**Pontuação**", value=account.points)
        embed_me.add_field(name="**Role**", value=account.role)
        embed_me.add_field(
            name="_**últimas Transações:**_", value=f"""```{table.head(5)}```"""
        )

        view = UserProfileView()
        await interaction.response.send_message(embed=embed_me, view=view)

    @app_commands.command(description="perfil da guilda")
    async def guilda(self, interaction: discord.Interaction):
        table = transactions_table()
        table = table.select(
            "id", "manager_name", "requester_name", "item", "quantity"
        ).sort("id", descending=True)
        table = table.rename(
            {
                "id": "N°",
                "manager_name": "GUILD BANKER",
                "requester_name": "REQUERENTE",
                "item": "ITEM",
                "quantity": "QUANTIDADE",
            }
        ).drop("N°")

        embed_guild = discord.Embed()
        embed_guild.set_author(
            name=f"Guilda {interaction.guild.name}", icon_url=interaction.guild.icon
        )
        embed_guild.add_field(
            name="Membros",
            value=len([m for m in interaction.guild.members if not m.bot]),
        )
        embed_guild.add_field(name="Online", value=None)
        embed_guild.add_field(name="teste", value="test")
        embed_guild.add_field(
            name="_**Últimas Transações:**_",
            value=f"```{table.head(10)}```",
            inline=True,
        )
        table_send = transactions_table(bool=True).drop("manager_id", "requester_id").sort("id", descending=True)
        guild_embed_message = await interaction.response.send_message(
            embed=embed_guild, view=GuildProfileView(table_send)
        )


async def setup(bot):
    bot.tree.add_command(Profile(name="profile", description="Comandos do perfil"))
