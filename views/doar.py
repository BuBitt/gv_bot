import time
import discord
import settings
from discord import utils
from models.items import Items
from models.account import Account
from models.donation import Donation
from views.interface import Main


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
            self.waiting_message.guild.text_channels, id=settings.DONATION_CHANNEL
        )
        # atualiza a mensagem para desligar os botões
        press_count = 1
        press_type = "S"
        self.update_buttons(press_count, press_type)
        await interaction.message.edit(view=self)

        # envia o embed da doação para o canal doações
        donation_msg = await donation_channel.send(embed=self.embed)

        # envia o feedback da confirmação para o manager
        embed_confirm_transaction = discord.Embed(
            title="**Doação Confirmada!**",
            description=f"A sua doação de foi publicada: {donation_msg.jump_url}",
            color=discord.Color.green(),
        )
        await self.waiting_message.edit(embed=embed_confirm_transaction)  # Main())

        # adiciona a jump url a doação
        self.transaction_dict["jump_url"] = donation_msg.jump_url

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

        # envia avisos de doação no chat da guilda
        guild_chat = utils.get(
            self.waiting_message.guild.text_channels, id=settings.GUILD_CHAT
        )

        donation_chat_mesage = f'`{self.transaction_dict["donor_name"]}` doou {self.transaction_dict["quantity"]} {self.transaction_dict["item"]} para a Guilda! → {self.transaction_dict.get("jump_url")}'
        embed = discord.Embed(
            title=donation_chat_mesage, color=discord.Color.dark_purple()
        )
        # await guild_chat.send(embed=embed)

        # envia o feedback da confirmação para o doador
        embed_sucess_pm = discord.Embed(
            title="**Doação Confirmada!**",
            description=f"A doação de ` {self.transaction_dict.get('donor_name')} ` foi aceita e publicada: {self.transaction_dict.get('jump_url')}",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed_sucess_pm)

        # Log da operação (terminal)
        donor = utils.get(
            donation_channel.guild.members, id=self.transaction_dict.get("donor_id")
        )
        crafter = utils.get(
            donation_channel.guild.members, id=self.transaction_dict.get("crafter_id")
        )
        
        channel = utils.get(
            donation_channel.guild.text_channels, id=settings.ADMIN_LOGS_CHANNEL
        )

        log_message_terminal = f'Doação Nº {transaction} foi efetuada com sucesso. {self.transaction_dict["donor_name"]} doou {self.transaction_dict["quantity"]} {self.transaction_dict["item"]}, Crafter {self.transaction_dict.get("crafter_name")}'
        logger.info(log_message_terminal)

        timestamp = str(time.time()).split(".")[0]
        log_message_ch = f'<t:{timestamp}:F>` - Doação Nº {transaction} foi efetuada com sucesso. `{donor.mention}` doou {self.transaction_dict["quantity"]} {self.transaction_dict["item"]} ao Crafter `{crafter.mention}'

        

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
        await self.waiting_message.edit(embed=transaction_denaied_embed)

        # envia o feedback da confirmação para o doador
        embed_sucess_pm = discord.Embed(
            title="**Doação Negada.**",
            description=f"O Crafter {self.transaction_dict['crafter_name']} negou a doação e a ela não será publicada.",
            color=discord.Color.green(),
        )
        return await interaction.response.send_message(embed=embed_sucess_pm)
