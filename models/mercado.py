from database import db
from ast import Dict
import settings
import peewee


logger = settings.logging.getLogger(__name__)


class MarketOffer(peewee.Model):
    vendor_id: int = peewee.BigIntegerField()
    buyer_id: int = peewee.BigIntegerField(default=0)
    vendor_name: str = peewee.CharField(max_length=255)
    message_id: int = peewee.BigIntegerField()
    jump_url: int = peewee.CharField(max_length=1024)
    item: str = peewee.CharField(max_length=255)
    price: int = peewee.IntegerField()
    quantity: int = peewee.IntegerField(default=1)
    image: str = peewee.CharField(max_length=1024)
    is_active: bool = peewee.BooleanField(default=True, null=False)
    timestamp: str = peewee.CharField(max_length=255)
    # hash_proof: str = peewee.CharField(max_length=15, default="not yet")

    class Meta:
        database = db
        db_table = "market_offers"

    @staticmethod
    def new(market_offer: Dict):
        try:
            market_offer = MarketOffer.create(
                vendor_id=market_offer.get("member_id"),
                vendor_name=market_offer.get("member_name"),
                message_id=market_offer.get("offer_message_id"),
                jump_url=market_offer.get("offer_jump_url"),
                item=market_offer.get("item"),
                price=market_offer.get("price"),
                quantity=market_offer.get("quantity"),
                image=market_offer.get("image"),
                timestamp=market_offer.get("timestamp"),
            )
        except peewee.OperationalError:
            MarketOffer.create_table()
            market_offer = MarketOffer.create(
                vendor_id=market_offer.get("member_id"),
                vendor_name=market_offer.get("member_name"),
                message_id=market_offer.get("offer_message_id"),
                jump_url=market_offer.get("offer_jump_url"),
                item=market_offer.get("item"),
                price=market_offer.get("price"),
                quantity=market_offer.get("quantity"),
                image=market_offer.get("image"),
                timestamp=market_offer.get("timestamp"),
            )

        return market_offer

    @staticmethod
    def fetch(message_id):
        MarketOffer.create_table()
        try:
            market_offer = MarketOffer.get(
                MarketOffer.message_id == message_id,
            )
        except peewee.DoesNotExist:
            return None
        return market_offer

    @staticmethod
    def fetch_by_jump_url(jump_url):
        MarketOffer.create_table()
        try:
            market_offer = MarketOffer.get(
                MarketOffer.jump_url == jump_url,
            )
        except peewee.DoesNotExist:
            return None
        return market_offer
