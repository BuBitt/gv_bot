import time
import discord
import settings
import traceback
from discord import utils
from models.items import Items
from models.account import Account
from models.donation import Donation


logger = settings.logging.getLogger(__name__)


# confirmação da transção pela dm
class ConfirmTransactionPm(discord.ui.View):
    def __init__(
        self, embed: discord.Embed, transaction_dict: dict, waiting_message
    ) -> None:
        self.embed = embed
        self.transaction_dict = transaction_dict
        self.waiting_message = waiting_message
        super().__init__(timeout=None)

    press_count = 0

    def update_buttons(self, press_count, press_type):
        if press_count == 1:
            self.confirm_transaction_pm.disabled = True
            self.cancel_transaction_pm.disabled = True
        if press_type == "S":
            self.confirm_transaction_pm.label = "Confirmado"
            self.cancel_transaction_pm.style = discord.ButtonStyle.gray
        else:
            self.cancel_transaction_pm.label = "Negado"
            self.confirm_transaction_pm.style = discord.ButtonStyle.gray

    @discord.ui.button(
        label="Confirmar Doação",
        style=discord.ButtonStyle.success,
        custom_id="confirm_transaction_pm",
    )
    async def confirm_transaction_pm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        donation_channel = discord.utils.get(
            self.waiting_message.guild.text_channels, name="doações"
        )
        # atualiza a mensagem para desligar os botões
        press_count = 1
        press_type = "S"
        self.update_buttons(press_count, press_type)
        await interaction.message.edit(embed=self.embed, view=self)

        # envia o embed da doação para o canal doações
        await donation_channel.send(embed=self.embed)

        # envia o feedback da confirmação para o manager
        embed_confirm_transaction = discord.Embed(
            title="**Doação Confirmada!**",
            description=f"A sua doação de foi publicada no canal de doações.",
            color=discord.Color.green(),
        )
        await self.waiting_message.edit(embed=embed_confirm_transaction, view=Main())

        # escreve a tansação na tabela transactions no banco de dados
        transaction = Donation.new(self.transaction_dict)

        # escreve a pontuação na tabela accounts do banco de dados
        user_to_add = discord.utils.get(
            self.waiting_message.guild.members,
            id=self.transaction_dict.get("donor_id"),
        )

        # encontra no banco de dados o item para usar sua pontuação
        item = Items.fetch(self.transaction_dict["item"].lower())

        account = Account.fetch(user_to_add)
        account.points += self.transaction_dict["quantity"] * item.points
        account.save()

        # Log da operação (terminal)
        donor = utils.get(
            donation_channel.guild.members, id=self.transaction_dict.get("donor_id")
        )
        crafter = utils.get(
            donation_channel.guild.members, id=self.transaction_dict.get("crafter_id")
        )

        log_message_terminal = f'Doação Nº {transaction} foi efetuada com sucesso. {self.transaction_dict["donor_name"]} doou {self.transaction_dict["quantity"]} {self.transaction_dict["item"]}, Crafter {self.transaction_dict.get("crafter_name")}'
        logger.info(log_message_terminal)

        timestamp = str(time.time()).split(".")[0]
        log_message_ch = f'<t:{timestamp}:F>` - Doação Nº {transaction} foi efetuada com sucesso. `{donor.mention}` doou {self.transaction_dict["quantity"]} {self.transaction_dict["item"]} ao Crafter `{crafter.mention}'

        channel = utils.get(donation_channel.guild.text_channels, name="logs")
        await channel.send(log_message_ch)

        # envia o feedback da confirmação para o doador
        embed_sucess_pm = discord.Embed(
            title="**Doação Confirmada!**",
            description=f"A doação de ` {self.transaction_dict.get('donor_name')} ` foi aceita e publicada no canal {donation_channel}",
            color=discord.Color.green(),
        )

        await interaction.response.send_message(embed=embed_sucess_pm)

    @discord.ui.button(
        label="Negar Doação",
        style=discord.ButtonStyle.danger,
        custom_id="cancel_transaction_pm",
    )
    async def cancel_transaction_pm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        # atualiza a mensagem para desligar os botões
        press_count = 1
        press_type = "C"
        self.update_buttons(press_count, press_type)
        await interaction.message.edit(embed=self.embed, view=self)

        # envia o feedback da confirmação para o user
        transaction_denaied_embed = discord.Embed(
            title=f"**Doação Negada.**",
            description=f"` {self.transaction_dict.get('donor_name')} ` negou o pedido de confirmação e a doação não será publicada.",
            color=discord.Color.dark_red(),
        )
        await self.waiting_message.edit(embed=transaction_denaied_embed, view=Main())

        # log da operação
        donor = utils.get(
            interaction.guild.members, id=self.transaction_dict.get("donor_id")
        )
        crafter = utils.get(
            interaction.guild.members, id=self.transaction_dict.get("crafter_id")
        )

        log_message_terminal = f"Doação negada. Criada por {self.transaction_dict.get('donor_name')}, negada por {self.transaction_dict.get('crafter_name')}"
        logger.info(log_message_terminal)

        log_message_ch = f"<t:{str(time.time()).split('.')[0]}:F>` - Doação negada. Criada por `{donor.mention}`, negada por `{crafter.mention}"
        channel = utils.get(interaction.guild.text_channels, name="logs")
        await channel.send(log_message_ch)

        # envia o feedback da confirmação para o doador
        embed_sucess_pm = discord.Embed(
            title="**Doação Negada.**",
            description=f"O Crafter {self.transaction_dict['crafter_name']} negou a doação e a ela não será publicada.",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed_sucess_pm)