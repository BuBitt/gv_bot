import peewee
from database import db


class Account(peewee.Model):
    user_id: str = peewee.CharField(max_length=255)
    user_name: str = peewee.CharField(max_length=255)
    guild_id: str = peewee.CharField(max_length=255)
    amount: int = peewee.IntegerField()

    class Meta:
        database = db

    @staticmethod
    def fetch(message):
        try:
            account = Account.get(
                Account.user_id == message.author.id,
                Account.guild_id == message.guild.id,
                Account.user_name == message.author.name,
            )
        except peewee.DoesNotExist:
            account = Account.create(
                user_id=message.author.id,
                user_name=message.author.name,
                guild_id=message.guild.id,
                amount=10,
            )
        return account
