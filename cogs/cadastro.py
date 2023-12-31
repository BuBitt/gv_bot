import re
import time
import discord
import datetime
from models.account import Account
import settings
from discord import Color, utils
from datetime import datetime
from models.items import Items
from discord.ext import commands
from views.cadastro import Main, ConfirmTransactionPm, CadastroBreak


logger = settings.logging.getLogger(__name__)


class ActionNature(discord.ui.View):
    answer1 = None

    @discord.ui.select(
        placeholder="Qual a natureza da ação?",
        options=[
            discord.SelectOption(label="Doação", value="D"),
            discord.SelectOption(label="Pedido", value="P"),
        ],
    )
    async def select_age(
        self, interaction: discord.Interaction, select_item: discord.ui.Select
    ):
        self.answer1 = select_item.values
        self.children[0].disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.defer()
        self.stop()


class CadastroTransacao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    transaction_dict = {}

    @commands.command()
    @commands.has_role("Guild Banker")
    async def cadastro(self, ctx):
        if ctx.channel.name.startswith("gb-transaction-"):
            transaction_dict = {}
            run = 0

            def id_converter(raw_id: str):
                return int(raw_id[2:-1])

            def is_valid_regex(url, regex):
                # Regex to check valid URL
                # regex = (
                #     "((http|https)://)(www.)?"
                #     + "[a-zA-Z0-9@:%._\\+~#?&//=]"
                #     + "{2,256}\\.[a-z]"
                #     + "{2,6}\\b([-a-zA-Z0-9@:%"
                #     + "._\\+~#?&//=]*)"
                # )

                # Compile the ReGex
                p = re.compile(regex)

                # If the string is empty
                # return false
                if url == None:
                    return False

                # Return if the string
                # matched the ReGex
                if re.search(p, url):
                    return True
                else:
                    return False

            # Loop do solicitante
            while True:
                first_embed = discord.Embed(
                    title="**Mencione abaixo o solicitante**",
                    description="Uma menção usual (@NomeDoPlayer)",
                    color=discord.Color.dark_blue(),
                )
                if run == 0:
                    message_sent = await ctx.send(
                        embed=first_embed, view=CadastroBreak()
                    )

                response = await self.bot.wait_for("message")
                requester_mention = response.content

                # deleta mensagem de erro
                if run == 1:
                    await message_send_error.delete()

                regex = "^<@(\d+)>$"
                if is_valid_regex(requester_mention, regex):
                    # Variáveis auxiliares portando os ids e nomes dos envolvidos na transação.
                    manager_name = ctx.message.author.nick

                    # verifica se o manager possui um nick no server
                    if manager_name is None:
                        manager_name = ctx.message.author.name

                    manager_id = ctx.message.author.id
                    requester_id = id_converter(requester_mention)
                    requester = await self.bot.fetch_user(requester_id)
                    requester_name = requester.display_name

                    # Adiciona ids e nomes ao dicionário auxiliar do banco de dados.
                    transaction_dict["manager_id"] = manager_id
                    transaction_dict["manager_name"] = manager_name
                    transaction_dict["requester_id"] = requester_id
                    transaction_dict["requester_name"] = requester_name

                    # remove os botões da pergunta depois de passada
                    first_embed.color = discord.Color.green()
                    await message_sent.edit(embed=first_embed, view=None)

                    # Log da operação
                    logger.info(
                        f"{manager_name}(ID: {manager_id}) iniciou um cadastro de transação para {requester_name}(ID: {requester_id})."
                    )

                    run = 0
                    break
                else:
                    if requester_mention == "!break":
                        embed = discord.Embed(
                            title="**Cadastro cancelado**",
                            color=discord.Color.dark_red(),
                        )
                        return await ctx.send(embed=embed)

                    # remove os botões da pergunta depois de passada
                    first_embed.color = discord.Color.red()
                    await message_sent.edit(embed=first_embed, view=None)

                    first_embed_error = discord.Embed(
                        title="**Formato não aceito**",
                        description="Você não enviou uma menção do discord, digite @NomeDoPlayer.",
                        color=discord.Color.dark_red(),
                    )

                    message_send_error = await ctx.send(
                        embed=first_embed_error, view=CadastroBreak()
                    )
                    run = 1

            # Loop do nome do Item
            while True:
                if run == 0:
                    embed_item = discord.Embed(
                        title="**Item**",
                        description="A existência do item é verificada no banco de dados.\n \
                            Caso o item não exista no jogo você precisará escrever novamente.",
                        color=discord.Color.dark_blue(),
                    )
                    message_sent = await ctx.send(
                        embed=embed_item, view=CadastroBreak()
                    )

                response = await self.bot.wait_for("message")
                input_item = response.content.lower()

                # deleta mensagem de erro
                if run == 1:
                    await message_send_error.delete()

                # Verifica se o imput existe na tabela de items no banco de dados.
                item_check = Items.fetch(input_item)

                if item_check:
                    transaction_dict["item"] = input_item.title()

                    # remove os botões da pergunta depois de passada
                    embed_item.color = discord.Color.green()
                    await message_sent.edit(embed=embed_item, view=None)

                    run = 0
                    break
                else:
                    if input_item == "!break":
                        embed = discord.Embed(
                            title="**Cadastro cancelado**",
                            color=discord.Color.dark_red(),
                        )
                        return await ctx.send(embed=embed)

                    embed_item_error = discord.Embed(
                        title="**O item não existe, digite novamente**",
                        description=f"{response.content} não é um item do jogo.",
                        color=discord.Color.dark_red(),
                    )
                    message_send_error = await ctx.send(
                        embed=embed_item_error, view=CadastroBreak()
                    )

                    # remove os botões da pergunta depois de passada
                    embed_item.color = discord.Color.red()
                    await message_sent.edit(embed=embed_item, view=None)

                    run = 1

            # Loop da quantidade de itens
            # FIXME valores =< 0 crasham o comando. 
            while True:
                if run == 0:
                    embed_qte_item = discord.Embed(
                        title="**Quantidade**",
                        description="A quantidade de itens da operação.",
                        color=discord.Color.dark_blue(),
                    )
                    message_sent = await ctx.send(
                        embed=embed_qte_item, view=CadastroBreak()
                    )

                response = await self.bot.wait_for("message")
                
                # deleta mensagem de erro
                if run == 1:
                    await message_send_error.delete()
                
                # Verifica se o input é um número
                try:
                    qte_item = int(response.content)

                except:
                    qte = response.content

                    # break cadastro
                    if qte == "!break":
                        embed = discord.Embed(
                            title="**Cadastro cancelado**",
                            color=discord.Color.dark_red(),
                        )
                        return await ctx.send(embed=embed)

                    # error message
                    embed_item_error = discord.Embed(
                        title="Isso não é um número",
                        description=f"{qte} não é um número, digite novamente.",
                        color=discord.Color.brand_red(),
                    )
                    message_send_error = await ctx.send(embed=embed_item_error, view=CadastroBreak())

                    run = 1
                    continue


                # Verifica se o input é maior que 0
                if qte_item > 0:
                    transaction_dict["quantity"] = int(qte_item)

                    # remove os botões da pergunta depois de passada
                    embed_qte_item.color = discord.Color.green()
                    await message_sent.edit(embed=embed_qte_item, view=None)

                    run = 0
                    break
                else:
                    # break cadastro
                    if qte == "!break":
                        embed = discord.Embed(
                            title="**Cadastro cancelado**",
                            color=discord.Color.dark_red(),
                        )
                        return await ctx.send(embed=embed)

                    # error message
                    embed_item_error = discord.Embed(
                        title="**A quantidade é inválida**",
                        description=f"{qte_item} não é um número positivo.",
                        color=discord.Color.dark_red(),
                    )
                    message_send_error = await ctx.send(
                        embed=embed_item_error, view=CadastroBreak()
                    )

                    # remove os botões da pergunta depois de passada
                    embed_qte_item.color = discord.Color.red()
                    await message_sent.edit(embed=embed_qte_item, view=None)

                    run = 1

            # market price input
            while True:
                if run == 0:
                    embed_price = discord.Embed(
                        title="**Preço no Market**",
                        description="O preço precisa ser maior ou igual a 20 e um valor inteiro.",
                        color=discord.Color.dark_blue(),
                    )
                    message_sent = await ctx.send(
                        embed=embed_price, view=CadastroBreak()
                    )

                response = await self.bot.wait_for("message")
                market_price = int(response.content)

                # deleta mensagem de erro
                if run == 1:
                    await message_send_error.delete()

                # Verifica se o imput é maior ou igual a 20 e inteiro
                if market_price >= 20 and type(market_price) == int:
                    transaction_dict["market_price"] = market_price

                    # remove os botões da pergunta depois de passada
                    embed_price.color = discord.Color.green()
                    await message_sent.edit(embed=embed_price, view=None)

                    run = 0
                    break
                else:
                    if input_item == "!break":
                        embed = discord.Embed(
                            title="**Cadastro cancelado**",
                            color=discord.Color.dark_red(),
                        )
                        return await ctx.send(embed=embed)

                    embed_item_error = discord.Embed(
                        title="**O preço fornecido não é válido.**",
                        description=f"{response.content} ou é menor que 20 ou não é um valor inteiro.",
                        color=discord.Color.dark_red(),
                    )
                    message_send_error = await ctx.send(
                        embed=embed_item_error, view=CadastroBreak()
                    )

                    # remove os botões da pergunta depois de passada
                    embed_price.color = discord.Color.red()
                    await message_sent.edit(embed=embed_price, view=None)

                    run = 1

            # menu de seleção da natureza da operação
            view = ActionNature()
            await ctx.send(view=view)
            await view.wait()
            transaction_dict["operation_type"] = view.answer1[0]
            if view.answer1[0] == "P":
                transaction_dict["quantity"] -= 2 * transaction_dict["quantity"]

            # Print
            while True:
                if run == 0:
                    embed_print = discord.Embed(
                        title="**Envie um print**",
                        description="Uma prova é necessária, envie uma imagem do trade. A imagem pode ser enviada pelo discord, ou por um link externo.",
                        color=discord.Color.dark_blue(),
                    )
                    message_sent = await ctx.send(
                        embed=embed_print, view=CadastroBreak()
                    )

                response = await self.bot.wait_for("message")

                try:
                    print_proof = response.attachments[0].url.split("?ex=")[0]
                except:
                    print_proof = response.content

                regex = (
                    "((http|https)://)(www.)?"
                    + "[a-zA-Z0-9@:%._\\+~#?&//=]"
                    + "{2,256}\\.[a-z]"
                    + "{2,6}\\b([-a-zA-Z0-9@:%"
                    + "._\\+~#?&//=]*)"
                )

                # deleta mensagem de erro
                if run == 1:
                    await message_send_error.delete()

                if is_valid_regex(print_proof, regex):
                    transaction_dict["print"] = print_proof
                    transaction_dict["timestamp"] = str(time.time()).split(".")[0]

                    # remove os botões da pergunta depois de passada
                    embed_print.color = discord.Color.green()
                    await message_sent.edit(embed=embed_print, view=None)

                    run = 0
                    break
                else:
                    # break cadastro
                    if print_proof == "!break":
                        embed = discord.Embed(
                            title="**Cadastro cancelado**",
                            color=discord.Color.dark_red(),
                        )
                        return await ctx.send(embed=embed)

                    # remove os botões da pergunta depois de passada
                    embed_print.color = discord.Color.red()
                    await message_sent.edit(embed=embed_print, view=None)

                    # error message
                    embed_print_error = discord.Embed(
                        title="**Print inválido**",
                        description=f"Por favor envie uma imagem.",
                        color=discord.Color.dark_red(),
                    )
                    message_send_error = await ctx.send(
                        embed=embed_print_error, view=CadastroBreak()
                    )
                    run = 1

            # Embed de Confirmação
            manager_user = self.bot.get_user(transaction_dict.get("manager_id"))
            requester_user = self.bot.get_user(transaction_dict.get("requester_id"))
            operation_type = transaction_dict.get("operation_type")

            embed_confirm = discord.Embed(
                title=f"**Recibo: {transaction_dict.get('requester_name')}**",
                description=f"{transaction_dict.get('requester_name')} ajudou a guilda a tornar-se mais forte. ajude você também!",
                color=discord.Color.brand_green(),
                timestamp=datetime.fromtimestamp(
                    int(transaction_dict.get("timestamp"))
                ),
            )
            embed_confirm.set_author(
                name=f'Guild Banker {transaction_dict.get("manager_name")}',
                icon_url=manager_user.display_avatar,
            )
            embed_confirm.set_footer(
                text="Recibo de doação/retirada de itens no Guild Bank."
            )
            embed_confirm.set_image(url=transaction_dict.get("print"))
            embed_confirm.set_thumbnail(url=requester_user.display_avatar)

            if operation_type == "D":
                embed_confirm.add_field(
                    name="Item Doado", value=f'> {transaction_dict.get("item").title()}'
                )
            else:
                embed_confirm.add_field(
                    name="Item Retirado", value=f'> {transaction_dict.get("item")}'
                )
            embed_confirm.add_field(
                name="Quantidade",
                value=f'> {transaction_dict.get("quantity")}',
                inline=True,
            )

            # encontra o canal chamado "doações"
            channel = utils.get(ctx.guild.text_channels, name="doações")

            # envia os embeds aos canais de interesse
            user_pm = discord.utils.get(
                ctx.guild.members, id=transaction_dict.get("requester_id")
            )
            await ctx.send(embed=embed_confirm)

            waiting_confirm_embed = discord.Embed(
                title="Aguardando a confirmação da transação...",
                description=f"Aguarde enquanto ` {transaction_dict.get('requester_name')} ` confirma a ação.",
                color=discord.Color.yellow(),
            )

            # envia a mensagem de aguardo de confirmação
            waiting_message = await ctx.send(embed=waiting_confirm_embed)

            # envia a mensagem privada de confirmação
            embed_warning_new_confirmation = discord.Embed(
                title=f"**Novo pedido de confirmação de transação enviado por `{transaction_dict.get('manager_name')}`**",
                color=discord.Color.yellow(),
            )
            embed_warning_new_confirmation.set_thumbnail(
                url="https://www.freeiconspng.com/img/2749"
            )

            await user_pm.send(embed=embed_warning_new_confirmation)
            await user_pm.send(
                embed=embed_confirm,
                view=ConfirmTransactionPm(
                    embed=embed_confirm,
                    transaction_dict=transaction_dict,
                    waiting_message=waiting_message,
                ),
            )

        else:
            channel = utils.get(ctx.guild.text_channels, name="guild-bank")
            await ctx.send(
                f"Esse comando não pode ser executado nesse canal. Crie uma nova requisição em {channel.mention}"
            )

    @cadastro.error
    async def add_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRole):
            await ctx.send("Você não tem permissão para executar esse comando.")


async def setup(bot):
    await bot.add_cog(CadastroTransacao(bot))
