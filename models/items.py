import peewee
from database import db


class Items(peewee.Model):
    item: str = peewee.CharField(max_length=255)

    class Meta:
        database = db
        db_table = 'items'

    @staticmethod
    def fetch(item):
        try:
            item_check = Items.get(
                Items.item == item,
            )
            return True
        except peewee.DoesNotExist:
            return False
