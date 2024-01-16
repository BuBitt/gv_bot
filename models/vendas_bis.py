from database import db
from ast import Dict
import settings
import peewee


logger = settings.logging.getLogger(__name__)


class SellInfoBis(peewee.Model):
    vendor_id: int = peewee.BigIntegerField()
    vendor_name: str = peewee.CharField(max_length=255)
    buyer_id: int = peewee.BigIntegerField(default=0)
    buyer_name: str = peewee.CharField(max_length=255)
    offer_id: int = peewee.IntegerField()
    item_name: str = peewee.CharField(max_length=255)
    item_tier_name: str = peewee.CharField(max_length=255, null=False)
    quantity: int = peewee.IntegerField(default=1)
    timestamp: str = peewee.CharField(max_length=255)
    hash_proof: str = peewee.CharField(max_length=255)

    class Meta:
        database = db
        db_table = "market_sells_bis"

    @staticmethod
    def new(sell: Dict):
        try:
            sell = SellInfoBis.create(
                vendor_id=sell.get("vendor_id"),
                vendor_name=sell.get("vendor_name"),
                buyer_id=sell.get("buyer_id"),
                buyer_name=sell.get("buyer_name"),
                offer_id=sell.get("offer_id"),
                item_tier_name=sell.get("item_tier_name"),
                item_name=sell.get("item_name"),
                quantity=sell.get("quantity"),
                timestamp=sell.get("timestamp"),
                hash_proof=sell.get("hash_proof"),
            )
        except peewee.ProgrammingError:
            db.create_tables([SellInfoBis])
            sell = SellInfoBis.create(
                vendor_id=sell.get("vendor_id"),
                vendor_name=sell.get("vendor_name"),
                buyer_id=sell.get("buyer_id"),
                buyer_name=sell.get("buyer_name"),
                offer_id=sell.get("offer_id"),
                item_tier_name=sell.get("item_tier_name"),
                item_name=sell.get("item_name"),
                quantity=sell.get("quantity"),
                timestamp=sell.get("timestamp"),
                hash_proof=sell.get("hash_proof"),
            )

        return sell

    @staticmethod
    def fetch(hash_proof):
        db.create_tables([SellInfoBis])
        try:
            sell = SellInfoBis.get(
                SellInfoBis.hash_proof == hash_proof,
            )
        except peewee.DoesNotExist:
            return None
        return sell
