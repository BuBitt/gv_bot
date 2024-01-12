import time
import discord
import settings
import traceback
import cogs.cadastro as cd
from discord import utils
from models.items import Items
from models.account import Account
from models.donation import Donation


logger = settings.logging.getLogger(__name__)


class NewItemLauncher(discord.ui.View):
    def __init__(self, new_item) -> None:
        self.new_item = new_item
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Confirmar",
        style=discord.ButtonStyle.success,
        custom_id="confirm_new_item_button",
    )
    async def confirm_new_item(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        item_instance = Items.create(item=self.new_item)
        item_instance.save()

        embed_new_item = discord.Embed(
            title=f"**` {self.new_item} ` - Foi adicionado a base de dados**",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed_new_item, ephemeral=True)
        gb_name = (
            interaction.user.nick
            if interaction.user.nick is not None
            else interaction.user.name
        )

        # Log da operação (terminal)
        log_message_terminal = f"{gb_name}(ID: {interaction.user.id}) adicionou o item {self.new_item} a base de dados"
        logger.info(log_message_terminal)
        log_message_ch = f"<t:{str(time.time()).split('.')[0]}:F>` - `{interaction.user.id}` adicionou um novo item a base de dados: {self.new_item} `"
        channel = utils.get(interaction.guild.text_channels, name="logs")
        await channel.send(log_message_ch)


class NewItem(discord.ui.Modal, title="Adicione um novo item"):
    new_item = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Item",
        required=True,
        placeholder="Digite o nome do item",
    )

    async def on_submit(self, interaction: discord.Interaction):
        new_item = self.new_item.value.title()
        embed = discord.Embed(
            title=f"**Confirme o nome do novo item:** ` {new_item} `",
            color=discord.Color.yellow(),
        )
        # verifica se new_item já existe na base de dados
        item_check = Items.fetch(new_item.title())
        if not item_check:
            await interaction.response.send_message(
                embed=embed, view=NewItemLauncher(new_item.title()), ephemeral=True
            )
        else:
            embed = discord.Embed(
                title=f"**O Item ` {new_item} ` já está cadastrado na base de dados**",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        traceback.print_tb(error.__traceback__)


class DonationLauncher(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Abrir Canal de Doações",
        style=discord.ButtonStyle.success,
        custom_id="transaction_button",
    )
    async def transaction(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        global_thread_name = f"DOAÇÃO - {interaction.user.name if interaction.user.nick == None else interaction.user.nick}"
        transaction = utils.get(
            interaction.guild.threads,
            name=global_thread_name,
        )

        if transaction is not None:
            await interaction.response.send_message(
                f"Você já possui um canal de Doações aberto: {transaction.mention}",
                ephemeral=True,
            )
        else:
            channel = await interaction.channel.create_thread(
                name=global_thread_name,
                invitable=False,
                auto_archive_duration=60,
                reason=f"Canal de doação para {interaction.user}",
            )

            instructions_embed = discord.Embed(
                title=f"**Instruções de uso**",
                description="\
1 - Para iniciar um novo cadastro digite `!doar` no chat;\n\
2 - Na parte `Item` o nome deve ser escrito em inglês;\n\
3 - Para cancelar o cadastro a qualquer momento digite `!cancelar`\n\
4 - Na parte `Print` envie uma imagem pelo discord ou por um link externo.",
                color=discord.Color.yellow(),
            )
            await channel.send(
                f"{interaction.user.mention}",
                embed=instructions_embed,
                view=Main(),
            )
            await interaction.response.send_message(
                f"Canal de doação criado para {channel.mention}.", ephemeral=True
            )
            logger.info(
                f"Canal de doação {channel.name} criado para {interaction.user.nick}(ID: {interaction.user.id})."
            )


class CrafterLauncher(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Novo Item",
        style=discord.ButtonStyle.success,
        custom_id="new_item_button",
    )
    async def new_item(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(NewItem())


class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Confirmar", style=discord.ButtonStyle.red, custom_id="confirm"
    )
    async def confirm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        try:
            await interaction.channel.delete()
        except:
            await interaction.response.send_message(
                f"Channel delete failed! make sure I have `manage_channels` persmission.",
                ephemeral=True,
            )


class Main(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Fechar Canal",
        style=discord.ButtonStyle.danger,
        custom_id="close_cannel_button",
    )
    async def close_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="Você tem certeza que deseja fechar esse canal?",
            color=discord.Color.dark_red(),
        )
        await interaction.response.send_message(
            embed=embed, ephemeral=True, view=Confirm()
        )


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
        account = Account.fetch(user_to_add)
        account.points += self.transaction_dict["quantity"]
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

        log_message_ch = f'<t:{str(time.time()).split(".")[0]}:F>` - Doação Nº {transaction} foi efetuada com sucesso. `{donor.mention}` doou {self.transaction_dict["quantity"]} {self.transaction_dict["item"]} ao Crafter `{crafter.mention}'
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
            color=discord.Color.red(),
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
