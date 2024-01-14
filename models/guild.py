import peewee
from database import db


class Guild(peewee.Model):
    guild_id: str = peewee.BigIntegerField()
    guild_silver: str = peewee.IntegerField(default=0)
    t2_requirement: int = peewee.IntegerField(default=0)
    t3_requirement: int = peewee.IntegerField(default=0)
    t4_requirement: int = peewee.IntegerField(default=0)
    t5_requirement: int = peewee.IntegerField(default=0)
    t6_requirement: int = peewee.IntegerField(default=0)

    class Meta:
        database = db
        db_table = "guild"

    @staticmethod
    def fetch(guild):
        db.create_tables([Guild])
        try:
            account = Guild.get(
                Guild.guild_id == guild.id,
            )
        except peewee.DoesNotExist:
            account = Guild.create(guild_id=guild.id)
        return account
