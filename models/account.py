import discord
import peewee
from database import db
import settings


class Account(peewee.Model):
    user_id: str = peewee.CharField(max_length=255)
    user_name: str = peewee.CharField(max_length=255)
    points: int = peewee.IntegerField()
    level: int = peewee.IntegerField()
    role: str = peewee.CharField(max_length=255)

    class Meta:
        database = db
        db_table = "account"

    @staticmethod
    def fetch(interaction):

        if isinstance(interaction, (discord.Message, discord.Interaction)):
            user_object = interaction.author if isinstance(interaction, discord.Message) else interaction.user
        elif isinstance(interaction, (discord.Member, discord.User)):
            user_object = interaction

        try:
            account = Account.get(
                Account.user_id == user_object.id,
            )
        except peewee.DoesNotExist:
            Account.create_table()
            account = Account.create(
                user_id=user_object.id,
                user_name=user_object.name,
                level=1,
                role="No Role",
                points=0,
            )
        return account
