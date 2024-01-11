import peewee
from database import db


class Items(peewee.Model):
    item: str = peewee.CharField(max_length=255)
    add_by_id: int = peewee.IntegerField()
    points: int = peewee.IntegerField()

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
