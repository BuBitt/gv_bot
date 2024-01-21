import discord
import peewee

from database import db


class Account(peewee.Model):
    user_id: int = peewee.BigIntegerField()
    user_name: str = peewee.CharField(max_length=255)
    points: int = peewee.IntegerField(default=0)
    silver_quantity: int = peewee.BigIntegerField(default=0)
    level: int = peewee.IntegerField(default=1)
    role: str = peewee.CharField(max_length=255)
    got_boots: bool = peewee.BooleanField(default=False, null=False)
    got_helmet: bool = peewee.BooleanField(default=False, null=False)
    got_armor: bool = peewee.BooleanField(default=False, null=False)
    got_legs: bool = peewee.BooleanField(default=False, null=False)
    set_lock: str = peewee.CharField(max_length=2, default="no", null=False)

    class Meta:
        database = db
        db_table = "account"

    @staticmethod
    def fetch(interaction):
        if isinstance(interaction, (discord.Message, discord.Interaction)):
            user_object = (
                interaction.author
                if isinstance(interaction, discord.Message)
                else interaction.user
            )
        elif isinstance(interaction, (discord.Member, discord.User)):
            user_object = interaction

        try:
            account = Account.get(
                Account.user_id == user_object.id,
            )
        except peewee.DoesNotExist:
            db.create_tables([Account])
            account = Account.create(
                user_id=user_object.id,
                user_name=user_object.name,
                role="No Role",
            )
        return account
