import peewee
from database import db


class Account(peewee.Model):
    user_id: str = peewee.CharField(max_length=255)
    user_name: str = peewee.CharField(max_length=255)
    points: int = peewee.IntegerField()
    level: int = peewee.IntegerField()
    role: str = peewee.CharField(max_length=255)

    class Meta:
        database = db
        db_table = 'account'

    @staticmethod
    def fetch(interaction):
        try:
            account = Account.get(
                Account.user_id == interaction.user.id,
                Account.user_name == interaction.user.name,
            )
        except peewee.DoesNotExist:
            account = Account.create(
                user_id=interaction.user.id,
                user_name=interaction.user.name,
                level=1,
                role="No Role",
                points=0
            )
        return account
