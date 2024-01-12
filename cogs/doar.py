import difflib
import re
import time
import datetime

from datetime import datetime
from beautifultable import BeautifulTable

import discord
from discord import utils
from discord.ext import commands

import settings
from models.items import Items
from views.doar import ConfirmTransactionPm

from errors.errors import IsNegativeError, IsNotCrafter, IsNotMention


logger = settings.logging.getLogger(__name__)


def truncar_string(input_string, max_length=13):
    if len(input_string) > max_length:
        result = input_string[: max_length - 3] + "…"
        return result
    else:
        return input_string


class ActionNature(discord.ui.View):
    answer1 = None

    @discord.ui.select(
        placeholder="Qual a natureza da ação?",
        options=[
            discord.SelectOption(label="Doação", value="D"),
            discord.SelectOption(label="Pedido", value="P"),
        ],
    )
    async def select_nature(
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
    @commands.has_any_role("Membro", "Membro Iniciante")
    async def doar(self, ctx: commands.context.Context):
        logger.debug(f"context: {ctx}")
        if ctx.channel.name.startswith("DOAÇÃO -"):
            transaction_dict = {}
            run = 0

            def id_converter(raw_id: str):
                """### Converte uma menção para um formato de id"""
                return int(raw_id[2:-1])

            def is_valid_regex(message, regex_pattern):
                """### Validação de padrão regex"""

                match = re.match(regex_pattern, message)
                return bool(match)

            def search_or_similar(termo_de_pesquisa, all_items, limiar=0.5):
                """
                Busca pelo termo fornecido na lista de strings do modelo Peewee.
                Retorna uma lista de strings similares usando o difflib.
                """

                # Percorre os itens no modelo Peewee
                for item in all_items:
                    # Verifica se o termo de pesquisa está no item ou se o item é similar
                    if termo_de_pesquisa.lower() == item:
                        return (True, 1)

                # Usa o difflib para obter correspondências próximas
                correspondencias = difflib.get_close_matches(
                    termo_de_pesquisa, all_items, n=10, cutoff=limiar
                )
                if correspondencias:
                    return (False, correspondencias)
                return (False, 0)

            def controi_tabela(list, header=None):
                table = BeautifulTable()
                table.set_style(BeautifulTable.STYLE_COMPACT)

                table.columns.append(list, header)
                table.columns.alignment = BeautifulTable.ALIGN_LEFT
                return table

            # Encontra todos os crafters de cada categoria pelo Role
            cooking = discord.utils.get(ctx.guild.roles, name="Cooking").members
            blacksmith = discord.utils.get(ctx.guild.roles, name="Blacksmith").members
            weaving = discord.utils.get(ctx.guild.roles, name="Weaving").members
            carpentry = discord.utils.get(ctx.guild.roles, name="Carpentry").members
            breeding = discord.utils.get(ctx.guild.roles, name="Moa").members

            # Loop do Crafter
            while True:
                # embed da menção do crafter
                first_embed = discord.Embed(
                    title="**Crafter**",
                    description="` Marque o crafter aqui com @NomeDoCrafter `",
                    color=discord.Color.dark_blue(),
                )
                first_embed.add_field(
                    name="> Cooking", value=f"{controi_tabela(cooking)}"
                )
                first_embed.add_field(
                    name="> Blacksmith", value=f"{controi_tabela(blacksmith)}"
                )
                first_embed.add_field(
                    name="> Weaving", value=f"{controi_tabela(weaving)}"
                )
                first_embed.add_field(
                    name="> Carpentry", value=f"{controi_tabela(carpentry)}"
                )
                first_embed.add_field(name="> Breeding", value=f"{controi_tabela(breeding)}")

                # envia o embed se está iniciando o formulário
                if run == 0:
                    message_sent = await ctx.send(embed=first_embed)

                response = await self.bot.wait_for(
                    "message",
                    check=lambda msg: msg.channel == ctx.channel
                    and msg.author == ctx.author,
                )
                crafter_mention = response.content
                # deleta mensagem de erro
                if run == 1:
                    await message_send_error.delete()

                # validador da menção
                regex = "^<@[0-9]+>$"

                try:
                    if not is_valid_regex(crafter_mention, regex):
                        raise IsNotMention("")

                    # checa se o mencionado é crafter
                    crafter_id = id_converter(crafter_mention)
                    crafter_user_object = utils.get(ctx.guild.members, id=crafter_id)
                    crafter_role = discord.utils.get(ctx.guild.roles, name="Crafter")

                    is_crafter = (
                        True if crafter_role in crafter_user_object.roles else False
                    )

                    if is_crafter:
                        # verifica se o doador possui um nick no server
                        donor_name = (
                            ctx.message.author.nick
                            if ctx.message.author.nick != None
                            else ctx.message.author.name
                        )

                        donor_id = ctx.message.author.id

                        # informações do crafter
                        crafter_name = (
                            crafter_user_object.nick
                            if crafter_user_object.nick != None
                            else crafter_user_object.name
                        )

                        # Adiciona ids e nomes ao dicionário auxiliar do banco de dados.
                        transaction_dict["crafter_id"] = crafter_id
                        transaction_dict["crafter_name"] = crafter_name
                        transaction_dict["donor_id"] = donor_id
                        transaction_dict["donor_name"] = donor_name

                        # muda a cor do embed ao responder corretamente
                        first_embed.color = discord.Color.green()
                        await message_sent.edit(embed=first_embed)

                        # Log da operação (terminal)
                        # log_message_terminal = f"{donor_name}(ID: {donor_id}) iniciou um processo de doação. Crafter: {donor_name}(ID: {donor_id})."
                        # logger.info(log_message_terminal)

                        # timestamp = str(time.time()).split('.')[0]
                        # log_message_ch = f"<t:{timestamp}:F>` - `{ctx.author.mention}` iniciou um processo de doação. Crafter: `{crafter_user_object.mention}"
                        # channel = utils.get(ctx.guild.text_channels, name="logs")

                        # await channel.send(log_message_ch)
                        run = 0

                        break

                    else:
                        raise IsNotCrafter("Erro: o player não é um crafter")

                except IsNotCrafter:
                    if crafter_mention == "!cancelar":
                        embed = discord.Embed(
                            title="**Cadastro cancelado**",
                            color=discord.Color.dark_red(),
                        )
                        return await ctx.send(embed=embed)

                    # Muda a cor do embed para vermelho (erro)
                    first_embed.color = discord.Color.dark_red()

                    first_embed_error = discord.Embed(
                        title="**Não é Crafter**",
                        description="Você mencionou um player que não é Crafter da guilda.",
                        color=discord.Color.dark_red(),
                    )

                    message_send_error = await ctx.send(embed=first_embed_error)
                    run = 1

                except IsNotMention:
                    if crafter_mention == "!cancelar":
                        embed = discord.Embed(
                            title="**Cadastro cancelado**",
                            color=discord.Color.dark_red(),
                        )
                        return await ctx.send(embed=embed)

                    # Muda a cor do embed para vermelho (erro)
                    first_embed.color = discord.Color.dark_red()

                    first_embed_error = discord.Embed(
                        title="**Formato não aceito**",
                        description="Você não enviou uma menção do discord, digite @NomeDoPlayer.",
                        color=discord.Color.dark_red(),
                    )

                    message_send_error = await ctx.send(embed=first_embed_error)
                    run = 1

            # Loop do nome do Item
            while True:
                if run == 0:
                    embed_item = discord.Embed(
                        title="**Item**",
                        description="A existência do item é verificada no banco de dados.\nCaso o item não exista no jogo você precisará escrever novamente.",
                        color=discord.Color.dark_blue(),
                    )
                    message_sent = await ctx.send(embed=embed_item)

                response = await self.bot.wait_for(
                    "message",
                    check=lambda msg: msg.channel == ctx.channel
                    and msg.author == ctx.author,
                )
                input_item = response.content.lower()

                # deleta mensagem de erro
                if run == 1:
                    await message_send_error.delete()

                # Verifica se o imput existe na tabela de items do banco de dados.
                item_list = [item.item for item in list(Items.select(Items.item))]

                search_result = search_or_similar(input_item, item_list)
                search_result_is_valid = search_result[0]

                if search_result_is_valid:
                    transaction_dict["item"] = input_item.lower()

                    # Muda a cor do embed para verde (sucesso)
                    embed_item.color = discord.Color.green()
                    await message_sent.edit(embed=embed_item, view=None)

                    run = 0
                    break
                else:
                    if input_item == "!cancelar":
                        embed = discord.Embed(
                            title="**Cadastro cancelado**",
                            color=discord.Color.dark_red(),
                        )
                        return await ctx.send(embed=embed)

                    # verifica se há sugrestoẽs
                    if search_result[1] == 0:
                        table = "Não há sugestões..."
                    else:
                        table = BeautifulTable()
                        table.set_style(BeautifulTable.STYLE_COMPACT)

                        table.columns.append(search_result[1], header=None)
                        table.columns.alignment = BeautifulTable.ALIGN_LEFT

                    # cria embed
                    embed_item_error = discord.Embed(
                        title="**O item não existe**",
                        description=f"` {response.content.title()} ` não é um item do jogo;\nDigite novamente.",
                        color=discord.Color.dark_red(),
                    )
                    embed_item_error.add_field(name="Sugestões", value=f"```{table}```")
                    message_send_error = await ctx.send(embed=embed_item_error)

                    # Muda a cor do embed para vermelho (erro)
                    embed_item.color = discord.Color.dark_red()
                    await message_sent.edit(embed=embed_item, view=None)

                    run = 1

            message_sent = None
            # Loop da quantidade de itens
            while True:
                if run == 0:
                    embed_qte_item = discord.Embed(
                        title="**Quantidade**",
                        description="A quantidade de itens deve ser positiva",
                        color=discord.Color.dark_blue(),
                    )
                    message_sent = await ctx.send(embed=embed_qte_item)

                response = await self.bot.wait_for(
                    "message",
                    check=lambda msg: msg.channel == ctx.channel
                    and msg.author == ctx.author,
                )

                # deleta mensagem de erro
                if run == 1:
                    await message_send_error.delete()

                try:
                    qte_item = int(response.content)

                    if qte_item < 1:
                        raise IsNegativeError
                    else:
                        # Gera a pontuação
                        transaction_dict["quantity"] = int(qte_item)

                        # Muda a cor do embed para vermelho (erro)
                        embed_qte_item.color = discord.Color.green()
                        await message_sent.edit(embed=embed_qte_item, view=None)

                        run = 0
                        break

                except IsNegativeError:
                    qte_item = response.content

                    # break cadastro
                    if qte_item == "!cancelar":
                        embed = discord.Embed(
                            title="**Cadastro cancelado**",
                            color=discord.Color.dark_red(),
                        )
                        return await ctx.send(embed=embed)

                    # error message
                    embed_item_error = discord.Embed(
                        title="**A quantidade é inválida**",
                        description=f"{qte_item} não é um maior que 0",
                        color=discord.Color.dark_red(),
                    )
                    message_send_error = await ctx.send(embed=embed_item_error)

                    # Muda a cor do embed para vermelho (erro)
                    embed_qte_item.color = discord.Color.dark_red()
                    await message_sent.edit(embed=embed_qte_item, view=None)

                    run = 1

                except ValueError:
                    qte_item = response.content

                    # break cadastro
                    if qte_item == "!cancelar":
                        embed = discord.Embed(
                            title="**Cadastro cancelado**",
                            color=discord.Color.dark_red(),
                        )
                        return await ctx.send(embed=embed)

                    # error message
                    embed_item_error = discord.Embed(
                        title="**A quantidade é inválida**",
                        description=f"{qte_item} não é um número",
                        color=discord.Color.dark_red(),
                    )
                    message_send_error = await ctx.send(embed=embed_item_error)

                    # Muda a cor do embed para vermelho (erro)
                    embed_qte_item.color = discord.Color.dark_red()
                    await message_sent.edit(embed=embed_qte_item, view=None)

                    run = 1

            # # menu de seleção da natureza da operação
            # view = ActionNature()
            # await ctx.send(view=view)
            # await view.wait()
            # transaction_dict["operation_type"] = view.answer1[0]
            # if view.answer1[0] == "P":
            #     transaction_dict["quantity"] -= 2 * transaction_dict["quantity"]

            # Print
            while True:
                if run == 0:
                    embed_print = discord.Embed(
                        title="**Envie um print**",
                        description="Uma prova é necessária, envie uma imagem do trade. A imagem pode ser enviada pelo discord, ou por um link externo.",
                        color=discord.Color.dark_blue(),
                    )
                    message_sent = await ctx.send(embed=embed_print)

                response = await self.bot.wait_for(
                    "message",
                    check=lambda msg: msg.channel == ctx.channel
                    and msg.author == ctx.author,
                )

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

                    # Muda a cor do embed para vermelho (erro)
                    embed_print.color = discord.Color.green()
                    await message_sent.edit(embed=embed_print, view=None)

                    run = 0
                    break
                else:
                    # break cadastro
                    if print_proof == "!cancelar":
                        embed = discord.Embed(
                            title="**Cadastro cancelado**",
                            color=discord.Color.dark_red(),
                        )
                        return await ctx.send(embed=embed)

                    # Muda a cor do embed para vermelho (erro)
                    embed_print.color = discord.Color.dark_red()
                    await message_sent.edit(embed=embed_print, view=None)

                    # error message
                    embed_print_error = discord.Embed(
                        title="**Print inválido**",
                        description=f"Por favor envie uma imagem.",
                        color=discord.Color.dark_red(),
                    )
                    message_send_error = await ctx.send(embed=embed_print_error)
                    run = 1

            # Embed de Confirmação
            crafter_user_object = utils.get(
                ctx.guild.members, id=transaction_dict.get("crafter_id")
            )
            crafter_name = (
                crafter_user_object.nick
                if crafter_user_object.nick != None
                else crafter_user_object.name
            )

            donor_user_object = utils.get(
                ctx.guild.members, id=transaction_dict.get("donor_id")
            )
            donor_name = (
                donor_user_object.nick
                if donor_user_object.nick != None
                else donor_user_object.name
            )

            embed_confirm = discord.Embed(
                title=f"**Recibo: {donor_name}**",
                description=f"{donor_name} ajudou a guilda a tornar-se mais forte. ajude você também!",
                color=discord.Color.brand_green(),
                timestamp=datetime.fromtimestamp(
                    int(transaction_dict.get("timestamp"))
                ),
            )
            embed_confirm.set_author(
                name=f"Crafter {crafter_name}",
                icon_url=crafter_user_object.display_avatar,
            )
            embed_confirm.set_footer(text="Recibo de doação")
            embed_confirm.set_image(url=transaction_dict.get("print"))
            embed_confirm.set_thumbnail(url=donor_user_object.display_avatar)

            embed_confirm.add_field(
                name="Item Doado", value=f'> {transaction_dict.get("item").title()}'
            )
            embed_confirm.add_field(
                name="Quantidade",
                value=f'> {abs(transaction_dict.get("quantity"))}',
                inline=True,
            )

            # encontra o canal chamado "doações"
            channel = utils.get(ctx.guild.text_channels, name="doações")

            # envia os embeds aos canais de interesse
            user_pm = discord.utils.get(
                ctx.guild.members, id=transaction_dict.get("crafter_id")
            )
            await ctx.send(embed=embed_confirm)

            waiting_confirm_embed = discord.Embed(
                title="Aguardando a confirmação da doação...",
                description=f"Aguarde enquanto o Crafter ` {transaction_dict.get('crafter_name')} ` confirma sua doação.",
                color=discord.Color.yellow(),
            )

            # envia a mensagem de aguardo de confirmação
            waiting_message = await ctx.send(embed=waiting_confirm_embed)

            # envia a mensagem privada de confirmação
            embed_warning_new_confirmation = discord.Embed(
                title=f"**Novo pedido de confirmação de doação enviado por `{transaction_dict.get('crafter_name')}`**",
                color=discord.Color.yellow(),
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

    @doar.error
    async def add_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRole):
            await ctx.send("Você não tem permissão para executar esse comando.")


async def setup(bot):
    await bot.add_cog(CadastroTransacao(bot))
