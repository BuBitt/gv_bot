import csv
import os
import time

import discord
from discord.ext import commands

import settings
from models.account import Account
from models.transactions import Transaction

logger = settings.logging.getLogger(__name__)


class PlayerGeneralIfo(discord.ui.View):
    def __init__(self, ctx_menu_interaction) -> None:
        self.ctx_menu_interaction = ctx_menu_interaction
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Puxar Capivara",
        style=discord.ButtonStyle.success,
        custom_id="capibara_pull_button",
    )
    async def capibara_pull(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        # query all transactions
        query = (
            Transaction.select()
            .where(Transaction.requester_id == self.ctx_menu_interaction.id)
            .order_by(Transaction.id.desc())
        )
        csv_filename = f"data-user-{self.ctx_menu_interaction.name}-{self.ctx_menu_interaction.id}.csv"

        # Fetch all rows as tuples
        results = list(query)

        # Write data to CSV file
        with open(csv_filename, "w", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)

            # Write header
            csv_writer.writerow(
                [field.name for field in results[0]._meta.sorted_fields]
            )

            # Write rows
            for result in results:
                csv_writer.writerow(
                    [
                        getattr(result, field.name)
                        for field in result._meta.sorted_fields
                    ]
                )

        # create a discor file object
        file = discord.File(csv_filename)

        file_down_embed = discord.Embed(
            title="**Todas as trasações já realizadas estão presentes no arquivo**",
            color=discord.Color.yellow(),
        )
        await interaction.response.send_message(
            embed=file_down_embed, file=file, ephemeral=True
        )
        os.remove(csv_filename)


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
        embed_me = discord.Embed(
            title="**Novo Role: Tank**", color=discord.Colour.green()
        )
        embed_me.set_author(
            name=f"{interaction.user.name if interaction.user.nick == None else interaction.user.nick}",
            icon_url=interaction.user.display_avatar,
        )

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
        embed_me = discord.Embed(
            title="**Novo Role: Healer**", color=discord.Colour.green()
        )
        embed_me.set_author(
            name=f"{interaction.user.name if interaction.user.nick == None else interaction.user.nick}",
            icon_url=interaction.user.display_avatar,
        )

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
        embed_me = discord.Embed(
            title="**Novo Role: Damage**", color=discord.Colour.green()
        )
        embed_me.set_author(
            name=f"{interaction.user.name if interaction.user.nick == None else interaction.user.nick}",
            icon_url=interaction.user.display_avatar,
        )

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
    def __init__(self, g_profile_embed) -> None:
        self.g_profile_embed = g_profile_embed
        # self.balance_all = balance_all
        super().__init__(timeout=None)
        self.cooldown = commands.CooldownMapping.from_cooldown(
            1, 300, commands.BucketType.member
        )

    @discord.ui.button(
        label="Baixar Transações",
        style=discord.ButtonStyle.success,
        custom_id="guild_allt_button",
    )
    async def guild_download_transactions(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        interaction.message.author = interaction.user
        bucket = self.cooldown.get_bucket(interaction.message)
        retry = bucket.update_rate_limit()
        if retry:
            return await interaction.response.send_message(
                f"Vá com calma! Você poderá baixar novamente alguns minutos",
                ephemeral=True,
            )

            
        # query all transactions
        query = Transaction.select().order_by(Transaction.id.desc())

        # Fetch all rows as tuples
        results = list(query)

        # Write data to CSV file
        csv_filename = f"data-transactions-{interaction.message.id}.csv"
        
        with open(csv_filename, "w", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)

            # Write header
            csv_writer.writerow(
                [field.name for field in results[0]._meta.sorted_fields]
            )

            # Write rows
            for result in results:
                csv_writer.writerow(
                    [
                        getattr(result, field.name)
                        for field in result._meta.sorted_fields
                    ]
                )

        # create a discor file object
        file = discord.File(csv_filename)

        file_down_embed = discord.Embed(
            title="**Todas as trasações já realizadas estão presentes no arquivo**",
            color=discord.Color.yellow(),
        )
        await interaction.response.send_message(
            embed=file_down_embed, file=file, ephemeral=True
        )
        os.remove(csv_filename)

    # @discord.ui.button(
    #     label="Baixar Balanço",
    #     style=discord.ButtonStyle.success,
    #     custom_id="guild_balance_button",
    # )
    # async def guild_download_balance(
    #     self, interaction: discord.Interaction, button: discord.ui.Button
    # ):
    #     self.gpb_pressed = 1
    #     self.update_buttons()
    #     await interaction.message.edit(view=self)
    #
    #     self.balance_all.write_csv(
    #         f"data-balance-{interaction.user.id}.csv", separator=","
    #     )
    #     file = discord.File(f"data-balance-{interaction.user.id}.csv")
    #
    #     file_down_embed = discord.Embed(
    #         title="**O balanço completo está disponível no arquivo**",
    #         color=discord.Color.yellow(),
    #     )
    #     await interaction.response.send_message(
    #         embed=file_down_embed, file=file, ephemeral=True
    #     )
    #     os.remove(f"data-balance-{interaction.user.id}.csv")
