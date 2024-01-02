import typing
import discord
import settings
import polars as pl
from database import db_name
from discord import Role, app_commands
from models.account import Account
from sqlalchemy import create_engine
from views.profile import UserProfileView, GuildProfileView


logger = settings.logging.getLogger(__name__)


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
    @app_commands.command(description="Gerencie seu perfil")
    async def me(self, interaction: discord.Interaction):
        account = Account.fetch(interaction)
        table = transactions_table()

        # calcula e aplica a pontuação na db
        # TODO if é desnecssário. Pode ser removido com uma database vazia
        if account.points == 0:
            points = table
            points = (
                points.filter(pl.col("requester_id") == interaction.user.id)
                .select("quantity", "market_price")
                .with_columns(
                    (pl.col("quantity") * pl.col("market_price")).alias("points")
                )
                .select(pl.sum("points"))
                .to_dicts()[0]
                .get("points")
            )
            logger.info(
                f"{interaction.user.name} teve {points} pontos adormecidos registrados ao criar o perfil"
            )
            account.points = points
            account.save()

        # primeira interação com o comando (registro de lvl e role)
        if account.role == "No Role":
            new_account_embed = discord.Embed(
                title="**🔒 Você não concluiu o seu cadastro**",
                color=discord.Color.yellow(),
                description=f"\n\n\
1 - Edite seu ` LVL ` com o comando:  `/profile edit_lvl`\n\
2 - Edite seu ` ROLE ` com o comando: `/profile edit_role`\n\n\
_**Após feito o cadastro seu perfil estará disponível para consulta. Caso deseje editar essas informações novamente, execute os mesmo comandos**_.",
            )
            await interaction.response.send_message(
                embed=new_account_embed, ephemeral=True
            )

        else:
            # TODO embed: código duplicado
            embed_me = discord.Embed()
            embed_me.set_author(
                name=f"Perfil de {interaction.user.name if interaction.user.nick == None else interaction.user.nick}",
                icon_url=interaction.user.display_avatar,
            )
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
                name="_**Últimas Transações:**_", value=f"""```{table.head(5)}```"""
            )

            await interaction.response.send_message(embed=embed_me)

    @app_commands.command(description="Perfil da guilda")
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
        table_send = (
            transactions_table(bool=True)
            .drop("manager_id", "requester_id")
            .sort("id", descending=True)
        )
        guild_embed_message = await interaction.response.send_message(
            embed=embed_guild,
            view=GuildProfileView(table_send, g_profile_embed=embed_guild),
        )

    @app_commands.command(
        name="see", description="Envia no chat o perfil de outro usuário"
    )
    @app_commands.describe(user="O usuário que terá o perfil enviado no chat")
    async def see(self, interaction: discord.Interaction, user: discord.Member):
        account = Account.fetch(user)
        table = transactions_table()

        # constroi tabela de balanço
        table = (
            table.filter(pl.col("requester_id") == user.id)
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

        embed_me = discord.Embed()
        embed_me.set_author(
            name=f"Perfil de {user.name if user.nick == None else user.nick}",
            icon_url=user.display_avatar,
        )
        embed_me.add_field(name="**Level**", value=account.level)
        embed_me.add_field(name="**Pontuação**", value=account.points)
        embed_me.add_field(name="**Role**", value=account.role)
        embed_me.add_field(
            name="_**Últimas Transações:**_",
            value=f"""```{table.head(5)}```""",
            inline=False,
        )
        await interaction.response.send_message(embed=embed_me)

    @app_commands.command(name="edit_lvl", description="Editar o lvl do seu perfil")
    @app_commands.describe(lvl="lvl atual da classe principal")
    async def edit_lvl(self, interaction: discord.Interaction, lvl: int):
        validate = True if lvl > 0 and lvl < 75 else False
        account = Account.fetch(interaction)

        if validate:
            embed_me = discord.Embed(color=discord.Colour.green())
            embed_me.set_author(
                name=f"{interaction.user.name if interaction.user.nick == None else interaction.user.nick}",
                icon_url=interaction.user.display_avatar,
            )
            embed_me.add_field(name="**Novo Level:**", value=f"> {lvl}")
            account.level = lvl
            account.save()
            await interaction.response.send_message(embed=embed_me, ephemeral=True)
        else:
            embed_me = discord.Embed(color=discord.Colour.red())
            embed_me.add_field(name=f"**` {lvl} ` é um valor inválido**", value="")
            await interaction.response.send_message(embed=embed_me, ephemeral=True)

    # TODO o input não possui qualquer tipo de validação
    @app_commands.command(
        name="edit_role", description="Edita o role principal do seu perfil"
    )
    @app_commands.describe(role="role")
    async def edit_role(self, interaction: discord.Interaction, role: str):
        account = Account.fetch(interaction)

        embed_me = discord.Embed(color=discord.Colour.green())
        embed_me.set_author(
            name=f"{interaction.user.name if interaction.user.nick == None else interaction.user.nick}",
            icon_url=interaction.user.display_avatar,
        )
        await interaction.response.send_message(embed=embed_me)
        embed_me.add_field(name="**Novo Role:**", value=f"> {role}")
        account.role = role
        account.save()


async def setup(bot):
    bot.tree.add_command(Profile(name="profile", description="Comandos do perfil"))
