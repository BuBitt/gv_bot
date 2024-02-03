import peewee
from database import db


class Items(peewee.Model):
    item = peewee.CharField(primary_key=True, max_length=255)
    add_by_id = peewee.BigIntegerField()
    points = peewee.FloatField()

    class Meta:
        database = db

    @staticmethod
    def is_in_db(item):
        try:
            item_check = Items.get(
                Items.item == item,
            )
            return True
        except peewee.DoesNotExist:
            return False

    @staticmethod
    def fetch(item):
        try:
            item = Items.get(
                Items.item == item,
            )
        except peewee.DoesNotExist:
            return None
        return item
