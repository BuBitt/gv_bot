import discord
from peewee import fn
from discord import app_commands
from beautifultable import BeautifulTable

import settings
from models.account import Account
from models.transactions import Transaction
from views.profile import GuildProfileView, UserProfileEdit

logger = settings.logging.getLogger(__name__)


truncated = {}


def truncar_string(input_string, max_length=13):
    if len(input_string) > max_length:
        result = input_string[: max_length - 3] + "…"
        truncated[result] = input_string
        return result
    else:
        return input_string


class Profile(app_commands.Group):
    @staticmethod
    def embed_me(interaction):
        account = Account.fetch(interaction)

        user = (
            interaction.user
            if type(interaction) == discord.Interaction
            else interaction
        )

        user_query = (
            Transaction.select(
                Transaction.id,
                Transaction.manager_name,
                Transaction.item,
                Transaction.quantity,
            )
            .where(Transaction.requester_id == user.id)
            .order_by(Transaction.id.desc())
            .limit(5)
        )

        table = BeautifulTable()
        table.set_style(BeautifulTable.STYLE_COMPACT)
        headers = ["Nº", "GUILD BANKER", "ITEM", "QUANTIDADE"]
        table.columns.header = headers

        table.columns.alignment["Nº"] = BeautifulTable.ALIGN_RIGHT
        table.columns.alignment["ITEM"] = BeautifulTable.ALIGN_LEFT
        table.columns.alignment["GUILD BANKER"] = BeautifulTable.ALIGN_LEFT
        table.columns.alignment["QUANTIDADE"] = BeautifulTable.ALIGN_RIGHT

        for transaction in list(user_query):
            row = [
                transaction.id,
                truncar_string(transaction.manager_name),
                truncar_string(transaction.item),
                transaction.quantity,
            ]
            table.rows.append(row)

        # Balance
        table_balance = BeautifulTable()
        table_balance.set_style(BeautifulTable.STYLE_COMPACT)

        headers = ["ITEM", "QUANTIDADE"]
        table_balance.columns.header = headers

        table_balance.columns.alignment["ITEM"] = BeautifulTable.ALIGN_LEFT
        table_balance.columns.alignment["QUANTIDADE"] = BeautifulTable.ALIGN_RIGHT

        user_query = (
            Transaction.select(
                Transaction.requester_id,
                Transaction.item,
                fn.SUM(Transaction.quantity).alias("total_quantity"),
            )
            .where(Transaction.requester_id == user.id)
            .group_by(Transaction.requester_id, Transaction.item)
            .order_by(fn.SUM(Transaction.quantity).desc())
        )

        balance_data = list(user_query)
        items = [truncar_string(transaction.item) for transaction in balance_data]

        for transaction in balance_data:
            row = [truncar_string(transaction.item), int(transaction.total_quantity)]
            table_balance.rows.append(row)

        # embed
        embed_me = discord.Embed(color=discord.Color.dark_green())
        embed_me.set_author(
            name=f"Perfil de {user.name if user.nick == None else user.nick}",
            icon_url=user.display_avatar,
        )
        embed_me.add_field(name="**Level**", value=account.level)
        embed_me.add_field(name="**Pontuação**", value=account.points)
        embed_me.add_field(name="**Role**", value=account.role)
        embed_me.add_field(name="_**Últimas Transações**_", value=f"""```{table}```""")
        embed_me.add_field(
            name="_**Balance**_", value=f"```{table_balance}```", inline=False
        )
        return embed_me

    @app_commands.command(description="Gerencie seu perfil")
    async def meu(self, interaction: discord.Interaction):
        account = Account.fetch(interaction)

        # primeira interação com o comando (registro de lvl e role)
        if account.role == "No Role":
            new_account_embed = discord.Embed(
                title="**🔒 Você não concluiu o seu cadastro**",
                color=discord.Color.yellow(),
                description=f"\n\n\
1 - Edite seu Perfil com o comando:  `/perfil edit`\n\n\
_**Após feito o cadastro seu perfil estará disponível para consulta. Caso deseje editar essas informações novamente execute o mesmo comando**_.",
            )
            await interaction.response.send_message(
                embed=new_account_embed, ephemeral=True
            )

        else:
            interactor_name = (
                interaction.user.name
                if interaction.user.nick == None
                else interaction.user.nick
            )
            logger.info(f"{interactor_name} consultou o próprio perfil")
            await interaction.response.send_message(embed=self.embed_me(interaction))

    @app_commands.command(description="Perfil da guilda")
    @app_commands.checks.cooldown(1, 300.0, key=lambda i: i.user.id)
    async def guilda(self, interaction: discord.Interaction):
        last_transactions_query = (
            Transaction.select(
                Transaction.id,
                Transaction.manager_name,
                Transaction.requester_name,
                Transaction.item,
                Transaction.quantity,
            )
            .order_by(Transaction.id.desc())
            .limit(10)
        )

        table = BeautifulTable()
        table.set_style(BeautifulTable.STYLE_COMPACT)

        headers = ["GUILD BANKER", "REQUERENTE", "ITEM", "QUANTIDADE"]
        table.columns.header = headers

        table.columns.alignment["REQUERENTE"] = BeautifulTable.ALIGN_LEFT
        table.columns.alignment["GUILD BANKER"] = BeautifulTable.ALIGN_LEFT
        table.columns.alignment["ITEM"] = BeautifulTable.ALIGN_LEFT
        table.columns.alignment["QUANTIDADE"] = BeautifulTable.ALIGN_RIGHT

        for transaction in last_transactions_query:
            row = [
                truncar_string(transaction.manager_name),
                truncar_string(transaction.requester_name),
                truncar_string(transaction.item),
                transaction.quantity,
            ]
            table.rows.append(row)

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
            name="_**Últimas Transações**_",
            value=f"```{table}```",
            inline=False,
        )

        # Balance
        balance_query = (
            Transaction.select(
                Transaction.item, fn.SUM(Transaction.quantity).alias("total_quantity")
            )
            .group_by(Transaction.item)
            .order_by(fn.SUM(Transaction.quantity).desc())
        )

        table = BeautifulTable()
        table.set_style(BeautifulTable.STYLE_COMPACT)

        headers = ["ITEM", "QUANTIDADE"]
        table.columns.header = headers

        # Fetch all balance data in a single query
        balance_data = list(balance_query)
        items = [truncar_string(transaction.item) for transaction in balance_data]

        for transaction in balance_data:
            row = [truncar_string(transaction.item), int(transaction.total_quantity)]
            table.rows.append(row)

        # Greatest Donators
        items = [truncated.get(item, item) for item in items]

        subquery = (
            Transaction.select(
                Transaction.requester_name,
                Transaction.item,
                fn.SUM(Transaction.quantity).alias("quantity"),
                fn.ROW_NUMBER()
                .over(
                    partition_by=[Transaction.item],
                    order_by=[fn.SUM(Transaction.quantity).desc()],
                )
                .alias("row_num"),
            )
            .where(
                Transaction.item.in_(Transaction.select(Transaction.item).distinct())
            )
            .group_by(Transaction.requester_name, Transaction.item)
            .alias("ranked")
        )

        query = (
            Transaction.select(
                subquery.c.requester_name, subquery.c.item, subquery.c.quantity
            )
            .from_(subquery)
            .where(subquery.c.row_num == 1)
            .limit(10)
        )

        # Execute the query
        results = list(query)

        # Initialize the dictionary
        raw = {}

        # Iterate over the results and populate the dictionary
        for result in results:
            raw[result.item] = [result.requester_name, result.quantity]

        # Populate the lists using a single loop
        column_name = [truncar_string(raw[item][0]) for item in items if item in raw]
        column_qte = [raw[item][1] for item in items if item in raw]

        # Process the greatest donators data

        table.columns.append(column_name, header="MAIOR DOADOR")
        table.columns.append(column_qte, header="QTE DOADA")

        table.columns.alignment["MAIOR DOADOR"] = BeautifulTable.ALIGN_LEFT
        table.columns.alignment["QUANTIDADE"] = BeautifulTable.ALIGN_RIGHT
        table.columns.alignment["ITEM"] = BeautifulTable.ALIGN_LEFT
        table.columns.alignment["QTE DOADA"] = BeautifulTable.ALIGN_RIGHT

        embed_guild.add_field(
            name="_**Balanço de Itens**_",
            value=f"```{table}```",
            inline=False,
        )

        await interaction.response.send_message(
            embed=embed_guild,
            view=GuildProfileView(
                g_profile_embed=embed_guild,
            ),
        )
        interactor_name = (
            interaction.user.name
            if interaction.user.nick == None
            else interaction.user.nick
        )
        logger.info(
            f"{interactor_name}(ID: {interaction.user.id}) consultou o perfil da guilda"
        )

    @app_commands.command(
        name="ver", description="Envia no chat o perfil de outro usuário"
    )
    @app_commands.describe(user="O usuário que terá o perfil enviado no chat")
    @app_commands.checks.cooldown(5, 120.0, key=lambda i: i.user.id)
    async def see(self, interaction: discord.Interaction, user: discord.Member):
        interactor_name = (
            interaction.user.name
            if interaction.user.nick == None
            else interaction.user.nick
        )
        user_name = user.name if user.nick == None else user.nick
        logger.info(
            f"{interactor_name}(ID: {interaction.user.id}) consultou o perfil do membro {user_name}(ID: {user.id})"
        )

        embed = self.embed_me(user)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="edit", description="Edita o role principal do seu perfil"
    )
    @app_commands.checks.cooldown(1, 21600.0, key=lambda i: i.user.id)
    async def edit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=self.embed_me(interaction),
            view=UserProfileEdit(profile_embed=self.embed_me(interaction)),
            ephemeral=True,
        )


async def setup(bot):
    bot.tree.add_command(Profile(name="perfil", description="Comandos do perfil"))
