import discord
from discord import app_commands


class Profile(app_commands.Group):
    @app_commands.command()
    async def me(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"ping")

    @app_commands.command()
    async def guilda(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"pong")


async def setup(bot):
    bot.tree.add_command(Profile(name="profile", description="Comandos do perfil"))
