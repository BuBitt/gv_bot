import datetime
import re
import time
import discord
import settings
from datetime import datetime
from discord import utils
from discord.ext import commands
from models.cadastro import Transaction
from models.items import Items


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
    async def cadastro(self, ctx):
        transaction_dict = {}
        run = 0

        def id_converter(raw_id: str):
            return int(raw_id[2:-1])

        def is_valid_url(url):
            # Regex to check valid URL
            regex = (
                "((http|https)://)(www.)?"
                + "[a-zA-Z0-9@:%._\\+~#?&//=]"
                + "{2,256}\\.[a-z]"
                + "{2,6}\\b([-a-zA-Z0-9@:%"
                + "._\\+~#?&//=]*)"
            )

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
            if run == 0:
                first_embed = discord.Embed(
                    title="**Mencione abaixo o solicitante**",
                    description="Uma menção usual (@NomeDoPlayer)",
                    color=discord.Color.dark_blue(),
                )
                await ctx.send(embed=first_embed)

            response = await self.bot.wait_for("message")
            requester_mention = response.content

            if requester_mention.startswith("<@"):
                # Variáveis auxiliares portando os ids e nomes dos envolvidos na transação.
                manager_id = ctx.message.author.id
                logger.info(type(manager_id))
                manager_name = ctx.message.author.nick
                requester_id = id_converter(requester_mention)
                requester = await self.bot.fetch_user(requester_id)
                requester_name = requester.display_name

                # Adiciona ids e nomes ao dicionário auxiliar do banco de dados.
                transaction_dict["manager_id"] = manager_id
                transaction_dict["manager_name"] = manager_name
                transaction_dict["requester_id"] = requester_id
                transaction_dict["requester_name"] = requester_name

                # Log da operação
                logger.info(
                    f"{manager_name}(ID: {manager_id}) abriu uma transação para {requester_name}(ID: {requester_id})."
                )

                run = 0
                break
            else:
                first_embed_error = discord.Embed(
                    title="**Formato não aceito**",
                    description="Você não enviou uma menção do discord, digite @NomeDoPlayer.",
                    color=discord.Color.dark_red(),
                )
                await ctx.send(embed=first_embed_error)
                run = 1

        # Loop do nome do Item
        while True:
            if run == 0:
                embed_item = discord.Embed(
                    title="**Escreva abaixo o nome do Item**",
                    description="Caso o item não exista no jogo voçê precisará escrever novamente.",
                    color=discord.Color.dark_blue(),
                )
                await ctx.send(embed=embed_item)

            response = await self.bot.wait_for("message")
            input_item = response.content.lower()

            # Verifica se o imput existe na tabela de items no banco de dados.
            item_check = Items.fetch(input_item)
            
            if item_check:
                transaction_dict["item"] = input_item

                run = 0
                break
            else:
                embed_item_error = discord.Embed(
                    title="**O item não existe, digite novamente**",
                    description=f"{response.content} não é um item do jogo.",
                    color=discord.Color.dark_red(),
                )
                await ctx.send(embed=embed_item_error)
                run = 1

        # Loop da quantidade de itens
        while True:
            if run == 0:
                embed_qte_item = discord.Embed(
                    title="**Quantidade**",
                    description="A quantidade de itens da operação.",
                    color=discord.Color.dark_blue(),
                )
                await ctx.send(embed=embed_qte_item)

            response = await self.bot.wait_for("message")

            # Verifica se o input é um número
            try:
                qte_item = int(response.content)

            except:
                # Feedback de erro.
                qte = response.content

                embed_item_error = discord.Embed(
                    title="Isso não é um número",
                    description=f"{qte} não é um número, digite novamente.",
                    color=discord.Color.brand_red(),
                )
                await ctx.send(embed=embed_item_error)

                run = 1
                continue

            # Verifica se o input é maior que 0
            if qte_item > 0:
                transaction_dict["quantity"] = int(qte_item)
                run = 0
                break
            else:
                embed_item_error = discord.Embed(
                    title="**A quantidade é inválida**",
                    description=f"{qte_item} não é um número positivo.",
                    color=discord.Color.dark_red(),
                )
                await ctx.send(embed=embed_item_error)
                run = 1

        # menu de seleção da natureza da operação
        view = ActionNature()
        await ctx.send(view=view)
        await view.wait()
        transaction_dict["operation_type"] = view.answer1[0]

        # Print
        while True:
            if run == 0:
                embed_print = discord.Embed(
                    title="**Envie um print**",
                    description="Uma prova é necessária, envie uma imagem do trade. A imagem pode ser enviada pelo discord, ou por um link externo.",
                    color=discord.Color.dark_blue(),
                )
                await ctx.send(embed=embed_print)

            response = await self.bot.wait_for("message")

            try:
                print_proof = response.attachments[0].url.split("?ex=")[0]
            except:
                print_proof = response.content

            if is_valid_url(print_proof):
                transaction_dict["print"] = print_proof
                transaction_dict['timestamp'] = str(time.time()).split(".")[0]
                logger.info(transaction_dict)

                run = 0
                break
            else:
                embed_print_error = discord.Embed(
                    title="**Print inválido**",
                    description=f"Por favor envie uma imagem.",
                    color=discord.Color.dark_red(),
                )
                await ctx.send(embed=embed_print_error)
                run = 1

        # Embed de Confirmação
        manager_user = self.bot.get_user(transaction_dict.get("manager_id"))
        requester_user = self.bot.get_user(transaction_dict.get("requester_id"))
        operation_type = transaction_dict.get("operation_type")
        
        embed_confirm = discord.Embed(
            title=f"**Recibo - {transaction_dict.get('requester_name')}**",
            description=f"{transaction_dict.get('requester_name')} ajudou a guilda a tornar-se mais forte. ajude você também!",
            color=discord.Color.brand_green(),
        )
        embed_confirm.set_author(
            name=f'Guild Banker {transaction_dict.get("manager_name")}', icon_url=manager_user.display_avatar
        )
        embed_confirm.set_footer(text=f'{datetime.fromtimestamp(int(transaction_dict.get("timestamp")))}')
        embed_confirm.set_image(url=transaction_dict.get("print"))
        embed_confirm.set_thumbnail(url=requester_user.display_avatar)
        if operation_type == 'D':
            embed_confirm.add_field(name="Item Doado", value=transaction_dict.get("item"))
        else:
            embed_confirm.add_field(name="Item Retirado", value=transaction_dict.get("item"))
        embed_confirm.add_field(
            name="Quantidade", value=transaction_dict.get("quantity"), inline=True
        )

        channel = utils.get(
            ctx.guild.text_channels,
            name="doações"
        )
        
        await channel.send(embed=embed_confirm)
        await ctx.send(embed=embed_confirm)
        
        # Bando de dados
        transaction = Transaction.new(transaction_dict)
        logger.info(transaction)


async def setup(bot):
    await bot.add_cog(CadastroTransacao(bot))
