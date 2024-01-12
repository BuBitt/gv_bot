import peewee
from database import db


class Items(peewee.Model):
    item = peewee.CharField(primary_key=True, max_length=255)
    add_by_id = peewee.IntegerField()
    points = peewee.IntegerField()

    class Meta:
        database = db

    @staticmethod
    def fetch(item):
        try:
            item_check = Items.get(
                Items.item == item,
            )
            return True
        except peewee.DoesNotExist:
            return False
