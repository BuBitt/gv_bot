import discord
import settings
import polars as pl
from discord import app_commands
from models.account import Account
from views.profile import GuildProfileView, UserProfileEdit


logger = settings.logging.getLogger(__name__)


# Polars configs
def transactions_table(bool=False):
    pl.Config.set_tbl_cols(10)
    pl.Config.set_tbl_rows(10)
    pl.Config.set_fmt_str_lengths(12)
    pl.Config.set_tbl_formatting("NOTHING")
    pl.Config.set_tbl_hide_dataframe_shape(True)
    pl.Config.set_tbl_hide_column_data_types(True)
    pl.Config.set_tbl_cell_numeric_alignment("RIGHT")
    if bool:
        pl.Config.set_tbl_rows(100)
        pl.Config.set_fmt_str_lengths(30)

    # connect to DB
    query = "SELECT * FROM transactions"
    return pl.read_database_uri(query=query, uri=settings.DB_URI)


class Profile(app_commands.Group):
    @staticmethod
    def embed_me(interaction):
        user = (
            interaction.user
            if type(interaction) == discord.Interaction
            else interaction
        )
        account = Account.fetch(interaction)
        table = transactions_table()

        embed_me = discord.Embed()
        embed_me.set_author(
            name=f"Perfil de {user.name if user.nick == None else user.nick}",
            icon_url=user.display_avatar,
        )
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

        embed_me.add_field(name="**Level**", value=account.level)
        embed_me.add_field(name="**Pontuação**", value=account.points)
        embed_me.add_field(name="**Role**", value=account.role)
        embed_me.add_field(
            name="_**Últimas Transações:**_", value=f"""```{table.head(5)}```"""
        )
        return embed_me

    @app_commands.command(description="Gerencie seu perfil")
    async def me(self, interaction: discord.Interaction):
        account = Account.fetch(interaction)

        # primeira interação com o comando (registro de lvl e role)
        if account.role == "No Role":
            new_account_embed = discord.Embed(
                title="**🔒 Você não concluiu o seu cadastro**",
                color=discord.Color.yellow(),
                description=f"\n\n\
1 - Edite seu Perfil com o comando:  `/profile edit`\n\n\
_**Após feito o cadastro seu perfil estará disponível para consulta. Caso deseje editar essas informações novamente execute o mesmo comando**_.",
            )
            await interaction.response.send_message(
                embed=new_account_embed, ephemeral=True
            )

        else:
            await interaction.response.send_message(embed=self.embed_me(interaction))

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

        embed_guild = discord.Embed(
            title="**Informações Gerais**",
            color=discord.Color.dark_green(),
            description=f"Com {interaction.guild.member_count} membros, é uma guilda do jogo Ravendawn.",
        )
        embed_guild.set_author(
            name=f"Guilda {interaction.guild.name}", icon_url=interaction.guild.icon
        )
        embed_guild.add_field(
            name="Tanks",
            value=Account.select().where(Account.role == "Tank").count(),
        )
        embed_guild.add_field(
            name="Healers",
            value=Account.select().where(Account.role == "Healer").count(),
        )
        embed_guild.add_field(
            name="Damagers",
            value=Account.select().where(Account.role == "Damage").count(),
        )
        embed_guild.add_field(
            name="_**Últimas Transações:**_",
            value=f"```{table.head(10)}```",
            inline=False,
        )

        balance = (
            table.select("ITEM", "QUANTIDADE")
            .group_by("ITEM")
            .sum()
            .sort("QUANTIDADE", descending=True)
        )

        lista = []
        for dicionario in balance.to_dicts():
            item = dicionario["ITEM"].title()
            maiores = (
                table.filter(pl.col("ITEM") == item)
                .select("REQUERENTE", "QUANTIDADE")
                .group_by("REQUERENTE")
                .sum()
                .sort("QUANTIDADE", descending=True)
                .row(0)
            )
            lista.append(maiores)

        most_donator = pl.DataFrame(lista, schema=["MAIOR DOADOR", "DOAÇÃO"])
        table_balance = pl.concat([balance, most_donator], how="horizontal")

        pl.Config.set_fmt_str_lengths(14)
        embed_guild.add_field(
            name="_**Balanço de Itens:**_",
            value=f"```{table_balance}```",
            inline=False,
        )

        await interaction.response.send_message(
            embed=embed_guild,
            view=GuildProfileView(
                transactions_table=transactions_table(),
                g_profile_embed=embed_guild,
                balance_all=table_balance,
            ),
        )

    @app_commands.command(
        name="see", description="Envia no chat o perfil de outro usuário"
    )
    @app_commands.describe(user="O usuário que terá o perfil enviado no chat")
    async def see(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.send_message(embed=self.embed_me(user))

    @app_commands.command(
        name="edit", description="Edita o role principal do seu perfil"
    )
    async def edit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=self.embed_me(interaction),
            view=UserProfileEdit(profile_embed=self.embed_me(interaction)),
            ephemeral=True,
        )


async def setup(bot):
    bot.tree.add_command(Profile(name="profile", description="Comandos do perfil"))
