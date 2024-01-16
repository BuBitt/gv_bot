import difflib
import discord
import settings
from discord import app_commands
import background_tasks
from utils.utilities import search_offer_table_construct

logger = settings.logging.getLogger(__name__)


class Wiki(app_commands.Group):
    @app_commands.command(name="busca", description="Busca uma informação na wiki")
    @app_commands.checks.has_any_role(
        settings.MEMBRO_INICIANTE_ROLE,
        settings.MEMBRO_ROLE,
        settings.OFFICER_ROLE,
        settings.COMMANDER_ROLE,
        settings.VICE_LIDER_ROLE,
        settings.LEADER_ROLE,
    )
    @app_commands.describe(termo="Termo que deseja pesquisar")
    @app_commands.checks.cooldown(1, 0.0, key=lambda i: i.user.id)
    async def wiki_search(
        self,
        interaction: discord.Interaction,
        termo: str,
    ):
        target_value = "🔽𝐖𝐈𝐊𝐈-𝐆𝐕🔽"
        text_channels = interaction.user.guild.text_channels

        target_index = next(
            (
                i
                for i, channel in enumerate(text_channels)
                if channel.name == target_value
            ),
            len(text_channels),
        )
        remaining_channels = text_channels[target_index:]

        similar_channels = [
            channel.mention
            for channel in remaining_channels
            if difflib.SequenceMatcher(
                None, termo.lower(), channel.name.lower()
            ).ratio()
            > 0.45
        ]

        if similar_channels:
            return await interaction.response.send_message(
                f"` Encontrei esses canais que podem te ajudar: `\n{search_offer_table_construct(similar_channels)}",
                ephemeral=True,
            )
        else:
            return await interaction.response.send_message(
                f"Não consegui encontrar {termo} :c", ephemeral=True
            )


async def setup(bot):
    bot.tree.add_command(Wiki(name="wiki", description="Comandos do perfil"))
