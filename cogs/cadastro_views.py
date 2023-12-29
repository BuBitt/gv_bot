import discord
import settings
from discord.ext import commands
from models.cadastro import Transaction
from discord import utils, app_commands


logger = settings.logging.getLogger(__name__)


class CadastroBreak(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=180)
    
    @discord.ui.button(
        label="Cancelar Cadastro",
        style=discord.ButtonStyle.primary,
        custom_id="break_button",
    )
    async def transaction(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_message("!break")   
        


class TransactionLauncher(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Criar Transação",
        style=discord.ButtonStyle.success,
        custom_id="transaction_button",
    )
    async def transaction(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        transaction = utils.get(
            interaction.guild.text_channels,
            name=f"gb-transaction-{interaction.user.name}",
        )

        logger.info(transaction)
        if transaction is not None:
            await interaction.response.send_message(
                f"Você já possui um canal de transação aberto {transaction.mention}",
                ephemeral=True,
            )
        else:
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(
                    view_channel=False
                ),
                interaction.user: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    attach_files=True,
                    embed_links=True,
                ),
                interaction.guild.me: discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_message_history=True
                ),
            }

            channel = await interaction.guild.create_text_channel(
                name=f"gb-transaction-{interaction.user.name}",
                overwrites=overwrites,
                reason=f"Canal de transação para {interaction.user}",
            )

            instructions_embed = discord.Embed(
                title=f"**Instruções de uso**",
                description="1 - Para iniciar um novo cadastro digite `!cadastro` no chat;\n \
                    2 - Na parte `Item` o nome deve ser escrito em inglês;\n \
                    3 - Para cancelar o cadastro a qualquer momento digite `!break`\n \
                    4 - Na parte `Print` envie uma imagem pelo discord ou por um link externo.",
                color=discord.Color.yellow(),
            )
            await channel.send(
                f"{interaction.user.mention} criou um canal de transação.",
                embed=instructions_embed,
                view=Main(),
            )
            await interaction.response.send_message(
                f"Canal de transação criado para {channel.mention}.", ephemeral=True
            )
            logger.info(
                f"Canal de transação {channel.name} criado para {interaction.user.nick}(ID: {interaction.user.id})."
            )


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
    def __init__(self, ctx, embed: discord.Embed, transaction_dict: dict) -> None:
        self.ctx = ctx
        self.embed = embed
        self.transaction_dict = transaction_dict
        super().__init__(timeout=30)

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
        label="Confirmar Transação",
        style=discord.ButtonStyle.success,
        custom_id="confirm_transaction_pm",
    )
    async def confirm_transaction_pm(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        donation_channel = discord.utils.get(
            self.ctx.guild.text_channels, name="doações"
        )
        # atualiza a mensagem para desligar os notões
        press_count = 1
        press_type = "S"
        self.update_buttons(press_count, press_type)
        await interaction.message.edit(embed=self.embed, view=self)

        # envia o embed da doação para o canal doações
        await donation_channel.send(embed=self.embed)

        # envia o feedback da confirmação para o manager
        embed_confirm_transaction = discord.Embed(
            title="**Transação Aceita!**",
            description=f"A sua transação foi aceita e publicada no canal {donation_channel}",
            color=discord.Color.green(),
        )
        await self.ctx.send(embed=embed_confirm_transaction, view=Main())

        # escreve a tansação no banco de dados
        transaction = Transaction.new(self.transaction_dict)
        logger.info(
            f'Transação Nº {transaction} para {self.transaction_dict.get("requester_name")} criada por {self.transaction_dict.get("manager_name")} foi gravada com sucesso.'
        )

        # envia o feedback da confirmação para o requerente
        embed_sucess_pm = discord.Embed(
            title="**Transação Confirmada!**",
            description="Sua transação foi publicada no canal de doações.",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed_sucess_pm)

    @discord.ui.button(
        label="Negar Transação",
        style=discord.ButtonStyle.danger,
        custom_id="cancel_transaction_pm",
    )
    async def cancel_transaction_pm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        # atualiza a mensagem para desligar os notões
        press_count = 1
        press_type = "C"
        self.update_buttons(press_count, press_type)
        await interaction.message.edit(embed=self.embed, view=self)

        # envia o feedback da confirmação para o manager
        transaction_denaied_embed = discord.Embed(
            title=f"**Transação Negada.**",
            description=f"{self.transaction_dict.get('requester_name')} negou o pedido de confirmação.",
            color=discord.Color.red(),
        )
        await self.ctx.send(embed=transaction_denaied_embed, view=Main())

        # log da operação
        logger.info(
            f'`{self.transaction_dict.get("requester_name")}` negou a transação cirada por {self.transaction_dict.get("manager_name")}'
        )

        # envia o feedback da confirmação para o requerente
        embed_sucess_pm = discord.Embed(
            title="**Transação Negada.**",
            description="Você negou a transação.",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed_sucess_pm)


class CogImport(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="transaction_button", description="Inicia o sistema de cadastro"
    )
    @app_commands.checks.has_role("Admin")
    async def transactioning(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"Para criar um novo canal de transação pressione o botão abaixo.",
            color=discord.Color.blue(),
        )
        await interaction.channel.send(embed=embed, view=TransactionLauncher())
        await interaction.response.send_message(
            f"{interaction.user.mention} Botão criado.",
            ephemeral=True,
        )

    @app_commands.command(name="close", description="Fecha o canal de cadastro")
    @app_commands.checks.has_role("Guild Banker")
    async def close_command(self, interaction: discord.Interaction):
        if "gb-transaction-" in interaction.channel.name:
            embed = discord.Embed(
                title=f"Você tem certeza que deseja cancelar o cadastro?",
                color=discord.Color.red(),
            )
            await interaction.response.send_message(
                embed=embed, view=Confirm(), ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"{interaction.user.mention} isn't a Ticket.",
                ephemeral=True,
            )

    @app_commands.command(name="add", description="Adds a user to the ticket.")
    @app_commands.describe(user="The user you want to add to the ticket")
    @app_commands.checks.has_role("Guild Banker")
    async def add_command(self, interaction: discord.Interaction, user: discord.Member):
        if "gb-transaction-" in interaction.channel.name:
            await interaction.channel.set_permissions(
                user,
                view_channel=True,
                send_messages=True,
                attach_files=True,
                embed_links=True,
            )
            await interaction.response.send_message(
                f"{user.mention} has been added to ticket {interaction.user.mention}"
            )
        else:
            await interaction.response.send_message(
                f"This isn't a ticket.", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(CogImport(bot))
