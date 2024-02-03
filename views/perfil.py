import csv
import datetime
import os
import time

import discord
from discord import utils
from discord.ext import commands

import cogs.doar as cd
from models.mercado_bis import MarketOfferBis

import settings
from models.account import Account
from models.donation import Donation

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
            Donation.select()
            .where(Donation.donor_id == self.ctx_menu_interaction.id)
            .order_by(Donation.id.desc())
        )
        csv_filename = f"data-user-{self.ctx_menu_interaction.name}-{self.ctx_menu_interaction.id}.csv"

        # Fetch all rows as tuples
        results = list(query)

        # Write data to CSV file
        capibara_pulled_user = (
            self.ctx_menu_interaction.name
            if self.ctx_menu_interaction.nick == None
            else self.ctx_menu_interaction.nick
        )

        # check if teh user has transactions
        try:
            t_history = [field.name for field in results[0]._meta.sorted_fields]
        except IndexError:
            os.remove(csv_filename)
            return await interaction.response.send_message(
                f"{capibara_pulled_user} não possui transações",
                ephemeral=True,
            )

        # write file
        with open(csv_filename, "w", encoding="utf-8", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)

            # Write header

            csv_writer.writerow(t_history)

            # Write rows
            for result in results:
                csv_writer.writerow(
                    [
                        getattr(result, field.name)
                        for field in result._meta.sorted_fields
                    ]
                )
        interaction_name_check = (
            interaction.user.name
            if interaction.user.nick == None
            else interaction.user.nick
        )
        logger.info(
            f"{interaction_name_check} puxou a capivara de {capibara_pulled_user}"
        )

        # create a discord file object
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
        interaction_name_check = (
            interaction.user.name
            if interaction.user.nick == None
            else interaction.user.nick
        )
        account = Account.fetch(interaction)

        embed_me = discord.Embed(
            title="**Novo Role: Tank**", color=discord.Colour.green()
        )
        embed_me.set_author(
            name=f"{interaction_name_check}",
            icon_url=interaction.user.display_avatar,
        )

        await interaction.response.send_message(embed=embed_me, ephemeral=True)
        account.role = "Tank"
        account.save()
        logger.info(
            f"{interaction_name_check}(id: {interaction.user.id}) mudou o role para Tank"
        )

    @discord.ui.button(
        label="Healer",
        style=discord.ButtonStyle.success,
        custom_id="profile_healer_role",
    )
    async def healer_profile_edit(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        interaction_name_check = (
            interaction.user.name
            if interaction.user.nick == None
            else interaction.user.nick
        )
        account = Account.fetch(interaction)
        embed_me = discord.Embed(
            title="**Novo Role: Healer**", color=discord.Colour.green()
        )
        embed_me.set_author(
            name=f"{interaction_name_check}",
            icon_url=interaction.user.display_avatar,
        )

        await interaction.response.send_message(embed=embed_me, ephemeral=True)
        account.role = "Healer"
        account.save()
        logger.info(
            f"{interaction_name_check}(id: {interaction.user.id}) mudou o role para Healer"
        )

    @discord.ui.button(
        label="Damage",
        style=discord.ButtonStyle.danger,
        custom_id="profile_damage_role",
    )
    async def damage_profile_edit(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        interaction_name_check = (
            interaction.user.name
            if interaction.user.nick == None
            else interaction.user.nick
        )
        account = Account.fetch(interaction)
        embed_me = discord.Embed(
            title="**Novo Role: Damage**", color=discord.Colour.green()
        )
        embed_me.set_author(
            name=f"{interaction_name_check}",
            icon_url=interaction.user.display_avatar,
        )

        await interaction.response.send_message(embed=embed_me, ephemeral=True)
        account.role = "Damage"
        account.save()
        logger.info(
            f"{interaction_name_check}(id: {interaction.user.id}) mudou o role para Damage"
        )


class LvlModal(discord.ui.Modal, title="Escreva seu lvl"):
    lvl = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Level",
        required=True,
        placeholder="Um número entre 1 e 75",
    )

    async def on_submit(self, interaction: discord.Interaction):
        interaction_name_check = (
            interaction.user.name
            if interaction.user.nick == None
            else interaction.user.nick
        )

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
                    name=f"{interaction_name_check}",
                    icon_url=interaction.user.display_avatar,
                )

                account.level = lvl
                account.save()
                await interaction.response.send_message(embed=embed_me, ephemeral=True)
                logger.info(
                    f"{interaction_name_check}(id: {interaction.user.id}) editou o lvl para {lvl}"
                )
            else:
                embed_me = discord.Embed(
                    title=f"**` {lvl} ` não está entre `0` e `75`**",
                    color=discord.Colour.red(),
                )
                await interaction.response.send_message(embed=embed_me, ephemeral=True)
        except:
            embed = discord.Embed(
                title=f"**` {lvl} ` não é um número inteiro**",
                color=discord.Color.dark_red(),
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
        view = UserProfileRoles()
        await interaction.response.send_message(view=view, ephemeral=True)


class GuildProfileView(discord.ui.View):
    def __init__(self, g_profile_embed) -> None:
        self.g_profile_embed = g_profile_embed
        # self.balance_all = balance_all
        super().__init__(timeout=None)
        # TODO concertar cd
        self.cooldown = commands.CooldownMapping.from_cooldown(
            1, 300.0, commands.BucketType.member
        )

    @discord.ui.button(
        label="Baixar Doações",
        style=discord.ButtonStyle.success,
        custom_id="guild_allt_button",
    )
    async def guild_download_transactions(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        # Cooldown checker
        interaction.message.author = interaction.user
        bucket = self.cooldown.get_bucket(interaction.message)
        retry = bucket.update_rate_limit()
        if retry:
            return await interaction.response.send_message(
                f"Vá com calma! Você poderá baixar novamente o arquivo por essa mensagem alguns minutos!",
                ephemeral=True,
            )

        # query all transactions
        query = Donation.select().order_by(Donation.id.desc())

        # Fetch all rows as tuples
        results = list(query)

        # Write data to CSV file
        csv_filename = f"data-transactions-{interaction.message.id}.csv"

        with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
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
        interaction_name_check = (
            interaction.user.name
            if interaction.user.nick == None
            else interaction.user.nick
        )
        os.remove(csv_filename)

        # log da operação
        log_message_terminal = (
            f"{interaction_name_check} baixou os dados de doação da guilda"
        )
        logger.info(log_message_terminal)

        log_message_ch = f"<t:{str(time.time()).split('.')[0]}:F>` - `{interaction.user.mention}` baixou os dados de doação da guilda `"
        channel = utils.get(
            interaction.guild.text_channels, id=settings.ADMIN_LOGS_CHANNEL
        )
        await channel.send(log_message_ch)


class ProfileCrafterUi(discord.ui.View):
    def __init__(self, crafter) -> None:
        self.crafter = crafter
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Baixar Itens Publicados",
        style=discord.ButtonStyle.success,
        custom_id="download_crafted_itens",
    )
    async def download_crafted_itens(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        crafter = self.crafter

        crafter_offers = (
            MarketOfferBis.select(
                MarketOfferBis.id,
                MarketOfferBis.vendor_id,
                MarketOfferBis.item_tier_name,
                MarketOfferBis.item_type,
                MarketOfferBis.atributes,
                MarketOfferBis.image,
            )
            .where(MarketOfferBis.vendor_id == crafter.id)
            .order_by(MarketOfferBis.id.desc())
        )

        crafter_offers = crafter_offers.select(
            MarketOfferBis.item_type,
            MarketOfferBis.item_tier_name,
            MarketOfferBis.atributes,
            MarketOfferBis.image,
        )
        csv_file_path = (
            f"historico-de-craft-{crafter.nick}-{datetime.datetime.now()}.csv"
        )

        with open(csv_file_path, "w", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)

            # Write header
            csv_writer.writerow(["TIPO", "ITEM", "ATRIBUTOS", "IMAGEM"])

            # Write data
            for row in crafter_offers.dicts():
                csv_writer.writerow(row.values())

        file = discord.File(csv_file_path)

        await interaction.response.send_message(
            f"Histórico de Craft: {crafter.nick}",
            ephemeral=True,
            file=file,
        )

        os.remove(csv_file_path)

        log_message_terminal = f"{interaction.user.nick}(ID: {interaction.user.id}) baixou o historico do crafter {crafter.nick}(ID: {crafter.id})"
        logger.info(log_message_terminal)

    @discord.ui.button(
        label="Baixar Doações Recebidas",
        style=discord.ButtonStyle.success,
        custom_id="download_crafted_recived_donations",
    )
    async def download_crafted_recived_donations(
        self, interaction: discord.Interaction, button: discord.Button
    ):
        crafter = self.crafter

        crafter_offers = (
            Donation.select()
            .where(Donation.crafter_id == crafter.id)
            .order_by(Donation.id.desc())
        )

        crafter_offers = crafter_offers.select(
            Donation.item, Donation.timestamp, Donation.print_proof, Donation.jump_url
        )

        csv_file_path = f"historico-de-doações-recebidas-{crafter.nick}-{datetime.datetime.now()}.csv"

        with open(csv_file_path, "w", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)

            # Write header
            csv_writer.writerow(["ITEM", "DATA", "IMAGEM", "MENSAGEM"])

            # Write data
            for row in crafter_offers.dicts():
                csv_writer.writerow(
                    [
                        row.get("item"),
                        datetime.datetime.fromtimestamp(int(row.get("timestamp"))),
                        row.get("print_proof"),
                        row.get("jump_url"),
                    ]
                )

        file = discord.File(csv_file_path)

        await interaction.response.send_message(
            f"Histórico de Doações Recebidas: {crafter.nick}",
            ephemeral=True,
            file=file,
        )

        os.remove(csv_file_path)

        log_message_terminal = f"{interaction.user.nick}(ID: {interaction.user.id}) baixou o historico de itens recebidos do crafter {crafter.nick}(ID: {crafter.id})"
        logger.info(log_message_terminal)
