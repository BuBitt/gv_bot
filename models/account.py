import discord
import peewee
from database import db
import settings

logger = settings.logging.getLogger(__name__)


class Account(peewee.Model):
    user_id: str = peewee.CharField(max_length=255)
    user_name: str = peewee.CharField(max_length=255)
    points: int = peewee.IntegerField()
    level: int = peewee.IntegerField()
    role: str = peewee.CharField(max_length=255)
    amount: int = peewee.IntegerField()

    class Meta:
        database = db
        db_table = "account"

    @staticmethod
    def fetch(interaction):
        if type(interaction) == discord.message.Message:
            user_object = interaction.author

        elif type(interaction) == discord.interactions.Interaction:
            user_object = interaction.user

        elif type(interaction) == discord.member.Member:
            user_object = interaction

        try:
            account = Account.get(
                Account.user_id == user_object.id,
            )
        except peewee.DoesNotExist:
            account = Account.create(
                user_id=user_object.id,
                user_name=user_object.name,
                level=1,
                role="No Role",
                points=0,
            )
        return account
