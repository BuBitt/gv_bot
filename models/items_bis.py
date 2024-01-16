import discord
import peewee

from database import db


class ItemBis(peewee.Model):
    tier_name: str = peewee.CharField(max_length=255)
    item_name: str = peewee.CharField(max_length=255)
    item_quantity: int - peewee.IntegerField()

    class Meta:
        database = db
        db_table = "item_bis"

    @staticmethod
    def fetch_by_tier_name(item_search):
        db.create_tables([ItemBis])
        try:
            item_name = ItemBis.get(
                ItemBis.tier_name == item_search,
            )
        except peewee.DoesNotExist:
            return None
        return item_name.item_name

    @staticmethod
    def fetch_by_name(item_search):
        db.create_tables([ItemBis])
        try:
            item_name = ItemBis.get(
                ItemBis.item_name == item_search,
            )
        except peewee.DoesNotExist:
            return None
        return item_name.tier_name
