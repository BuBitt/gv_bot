from sqlalchemy import create_engine
from models.account import Account
from database import db_name
import polars as pl
import settings
import discord
import os


logger = settings.logging.getLogger(__name__)


class PlayerGeneralIfo(discord.ui.View):
    def __init__(self, ctx_menu_interaction) -> None:
        self.ctx_menu_interaction = ctx_menu_interaction
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Puxar Capivara",
        style=discord.ButtonStyle.success,
        custom_id="capibara_pull",
    )
    async def tank_profile_edit(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        # polars config
        pl.Config.set_tbl_cols(10)
        pl.Config.set_tbl_rows(10)
        pl.Config.set_fmt_str_lengths(12)
        pl.Config.set_tbl_formatting("NOTHING")
        pl.Config.set_tbl_hide_dataframe_shape(True)
        pl.Config.set_tbl_hide_column_data_types(True)
        pl.Config.set_tbl_cell_numeric_alignment("RIGHT")

        # acess db
        conn = create_engine(f"sqlite:///{db_name}")
        query = "SELECT * FROM transactions"
        tabel = pl.read_database(query=query, connection=conn.connect())
        
        # cria e envia arquivo com dados do usuário
        transactions = (
            tabel.filter(pl.col("requester_id") == self.ctx_menu_interaction.id)
            .drop("requester_id")
            .write_csv(f"data-user-{self.ctx_menu_interaction.name}-{self.ctx_menu_interaction.id}.csv", separator=",")
        )
        file = discord.File(f"data-user-{self.ctx_menu_interaction.name}-{self.ctx_menu_interaction.id}.csv")

        file_down_embed = discord.Embed(
            title=f"**Todas as trasações do player {self.ctx_menu_interaction.name} estão presentes no arquivo**",
            color=discord.Color.yellow(),
        )
        await interaction.response.send_message(
            embed=file_down_embed, file=file, ephemeral=True
        )
        os.remove(f"data-user-{self.ctx_menu_interaction.name}-{self.ctx_menu_interaction.id}.csv")


class UserProfileRoles(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Tank", style=discord.ButtonStyle.blurple, custom_id="profile_tank_role"
    )
    async def tank_profile_edit(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        account = Account.fetch(interaction)
        embed_me = discord.Embed(color=discord.Colour.green())
        embed_me.set_author(
            name=f"{interaction.user.name if interaction.user.nick == None else interaction.user.nick}",
            icon_url=interaction.user.display_avatar,
        )
        embed_me.add_field(name="**Novo Role: Tank**", value=f"")
        await interaction.response.send_message(embed=embed_me, ephemeral=True)
        account.role = "Tank"
        account.save()

    @discord.ui.button(
        label="Healer",
        style=discord.ButtonStyle.success,
        custom_id="profile_healer_role",
    )
    async def healer_profile_edit(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        account = Account.fetch(interaction)
        embed_me = discord.Embed(color=discord.Colour.green())
        embed_me.set_author(
            name=f"{interaction.user.name if interaction.user.nick == None else interaction.user.nick}",
            icon_url=interaction.user.display_avatar,
        )
        embed_me.add_field(name="**Novo Role: Healer**", value=f"", inline=True)
        await interaction.response.send_message(embed=embed_me, ephemeral=True)
        account.role = "Healer"
        account.save()

    @discord.ui.button(
        label="Damage",
        style=discord.ButtonStyle.danger,
        custom_id="profile_damage_role",
    )
    async def damage_profile_edit(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        account = Account.fetch(interaction)
        embed_me = discord.Embed(color=discord.Colour.green())
        embed_me.set_author(
            name=f"{interaction.user.name if interaction.user.nick == None else interaction.user.nick}",
            icon_url=interaction.user.display_avatar,
        )
        embed_me.add_field(name="**Novo Role: Damage**", value=f"")
        await interaction.response.send_message(embed=embed_me, ephemeral=True)
        account.role = "Damage"
        account.save()


class LvlModal(discord.ui.Modal, title="Escreva seu lvl"):
    lvl = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Level",
        required=True,
        placeholder="Um número entre 1 e 75",
    )

    async def on_submit(self, interaction: discord.Interaction):
        lvl = self.lvl.value.strip()
        account = Account.fetch(interaction)

        try:
            lvl = int(lvl)
            validate = True if lvl > 0 and lvl < 75 else False

            if validate:
                embed_me = discord.Embed(
                    title=f"**Novo Level: {lvl}**", color=discord.Colour.green()
                )
                embed_me.set_author(
                    name=f"{interaction.user.name if interaction.user.nick == None else interaction.user.nick}",
                    icon_url=interaction.user.display_avatar,
                )

                account.level = lvl
                account.save()
                await interaction.response.send_message(embed=embed_me, ephemeral=True)
            else:
                embed_me = discord.Embed(
                    title=f"**` {lvl} ` não está entre `0` e `75`**",
                    color=discord.Colour.red(),
                )
                await interaction.response.send_message(embed=embed_me, ephemeral=True)
        except:
            embed = discord.Embed(
                title=f"**` {lvl} ` não é um número inteiro**",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


class UserProfileEdit(discord.ui.View):
    def __init__(self, profile_embed) -> None:
        self.profile_embed = profile_embed
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Level", style=discord.ButtonStyle.success, custom_id="profile_edit_level"
    )
    async def profile_edit_level(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        await interaction.response.send_modal(LvlModal())

    @discord.ui.button(
        label="Role", style=discord.ButtonStyle.success, custom_id="profile_edit_role"
    )
    async def profile_edit_role(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        account = Account.fetch(interaction)
        view = UserProfileRoles()
        await interaction.response.send_message(view=view, ephemeral=True)


class GuildProfileView(discord.ui.View):
    def __init__(self, transactions_table, g_profile_embed, balance_all) -> None:
        self.transactions_table = transactions_table
        self.g_profile_embed = g_profile_embed
        self.balance_all = balance_all
        super().__init__(timeout=None)

    gpa_pressed = 0
    gpb_pressed = 0

    def update_buttons(self):
        if self.gpa_pressed == 1:
            self.guild_download_transactions.disabled = True
            self.guild_download_transactions.style = discord.ButtonStyle.gray

        if self.gpb_pressed == 1:
            self.guild_download_balance.disabled = True
            self.guild_download_balance.style = discord.ButtonStyle.gray

    @discord.ui.button(
        label="Baixar Transações",
        style=discord.ButtonStyle.success,
        custom_id="guild_allt_button",
    )
    async def guild_download_transactions(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.gpa_pressed = 1
        self.update_buttons()
        await interaction.message.edit(view=self)

        self.transactions_table.write_csv(
            f"data-transactions-{interaction.user.id}.csv", separator=","
        )
        file = discord.File(f"data-transactions-{interaction.user.id}.csv")

        file_down_embed = discord.Embed(
            title="**Todas as trasações já realizadas estão presentes no arquivo**",
            color=discord.Color.yellow(),
        )
        await interaction.response.send_message(
            embed=file_down_embed, file=file, ephemeral=True
        )
        os.remove(f"data-transactions-{interaction.user.id}.csv")

    @discord.ui.button(
        label="Baixar Balanço",
        style=discord.ButtonStyle.success,
        custom_id="guild_balance_button",
    )
    async def guild_download_balance(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.gpb_pressed = 1
        self.update_buttons()
        await interaction.message.edit(view=self)

        self.balance_all.write_csv(
            f"data-balance-{interaction.user.id}.csv", separator=","
        )
        file = discord.File(f"data-balance-{interaction.user.id}.csv")

        file_down_embed = discord.Embed(
            title="**O balanço completo está disponível no arquivo**",
            color=discord.Color.yellow(),
        )
        await interaction.response.send_message(
            embed=file_down_embed, file=file, ephemeral=True
        )
        os.remove(f"data-balance-{interaction.user.id}.csv")
