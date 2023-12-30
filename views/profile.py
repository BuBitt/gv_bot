from turtle import title
import polars as pl
import settings
import discord
import os


logger = settings.logging.getLogger(__name__)


class UserProfileView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Balanço",
        style=discord.ButtonStyle.primary,
        custom_id="me_balance_button",
    )
    async def balanco(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_message("balance")

    @discord.ui.button(
        label="Todas as Transações",
        style=discord.ButtonStyle.secondary,
        custom_id="me_allt_button",
    )
    async def print_all(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_message("search")


class GuildProfileView(discord.ui.View):
    def __init__(self, transactions_table) -> None:
        self.transactions_table = transactions_table
        # self.g_profile_embed = g_profile_embed
        super().__init__(timeout=None)

    gpa_pressed = 0
    gb_pressed = 0

    def update_buttons(self):
        if self.gpa_pressed == 1:
            self.guild_print_all.disabled = True
            self.guild_print_all.style = discord.ButtonStyle.gray

    @discord.ui.button(
        label="Balanço",
        style=discord.ButtonStyle.primary,
        custom_id="guild_balance_button",
    )
    async def guild_balance(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.transactions_table = self.transactions_table.rename(
            {
                "id": "N°",
                "manager_name": "GUILD BANKER",
                "requester_name": "REQUERENTE",
                "item": "ITEM",
                "quantity": "QUANTIDADE",
            }
        )
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
            name="_**Balanço de Itens:**_",
            value=f"```{self.transactions_table.select('ITEM', 'QUANTIDADE').group_by('ITEM').sum().sort('QUANTIDADE', descending=True)}```",
            inline=True,
        )
        await interaction.message.edit(embed=embed_guild, view=self)

    @discord.ui.button(
        label="Baixar Dados",
        style=discord.ButtonStyle.success,
        custom_id="guild_allt_button",
    )
    async def guild_print_all(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.gpa_pressed = 1
        self.update_buttons()
        await interaction.message.edit(view=self)

        self.transactions_table.write_csv(
            f"data-{interaction.user.id}.csv", separator=","
        )
        file = discord.File(f"data-{interaction.user.id}.csv")

        file_down_embed = discord.Embed(
            title="**Todas as trasações já realizadas estão presentes no arquivo:**",
            color=discord.Color.yellow(),
        )
        await interaction.response.send_message(
            embed=file_down_embed, file=file, ephemeral=True
        )
        os.remove(f"data-{interaction.user.id}.csv")
