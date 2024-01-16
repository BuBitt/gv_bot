from sqlalchemy import null
from database import db
from ast import Dict
import settings
import peewee


logger = settings.logging.getLogger(__name__)


class MarketOfferBis(peewee.Model):
    vendor_id: int = peewee.BigIntegerField()
    vendor_name: str = peewee.CharField(max_length=255)
    message_id: int = peewee.BigIntegerField()
    item_name: str = peewee.CharField(max_length=255, null=False)
    item_tier_name: str = peewee.CharField(max_length=255, null=False)
    item_type: str = peewee.CharField(max_length=255, null=False)
    atributes: str = peewee.CharField(max_length=255, null=False)
    quantity: int = peewee.IntegerField(default=1, null=False)
    min_points_req: int = peewee.IntegerField(null=False)
    is_active: bool = peewee.BooleanField(default=True, null=False)
    timestamp: str = peewee.CharField(max_length=255)
    jump_url: int = peewee.CharField(max_length=1024)
    image: str = peewee.CharField(max_length=1024, null=False)

    class Meta:
        database = db
        db_table = "market_offers_bis"

    @staticmethod
    def new(market_offer: Dict):
        try:
            market_offer = MarketOfferBis.create(
                vendor_id=market_offer.get("member_id"),
                vendor_name=market_offer.get("member_name"),
                message_id=market_offer.get("offer_message_id"),
                jump_url=market_offer.get("offer_jump_url"),
                item_name=market_offer.get("item_name"),
                item_type=market_offer.get("item_type"),
                item_tier_name=market_offer.get("item_tier_name"),
                min_points_req=market_offer.get("min_points_req"),
                atributes=market_offer.get("atributes"),
                quantity=market_offer.get("quantity"),
                image=market_offer.get("image"),
                timestamp=market_offer.get("timestamp"),
            )
        except peewee.OperationalError:
            db.create_tables([MarketOfferBis])
            market_offer = MarketOfferBis.create(
                vendor_id=market_offer.get("member_id"),
                vendor_name=market_offer.get("member_name"),
                message_id=market_offer.get("offer_message_id"),
                jump_url=market_offer.get("offer_jump_url"),
                item_name=market_offer.get("item_name"),
                item_type=market_offer.get("item_type"),
                item_tier_name=market_offer.get("item_tier_name"),
                min_points_req=market_offer.get("min_points_req"),
                atributes=market_offer.get("atributes"),
                quantity=market_offer.get("quantity"),
                image=market_offer.get("image"),
                timestamp=market_offer.get("timestamp"),
            )

        return market_offer

    @staticmethod
    def fetch(message_id):
        db.create_tables([MarketOfferBis])
        try:
            market_offer = MarketOfferBis.get(
                MarketOfferBis.message_id == message_id,
            )
        except peewee.DoesNotExist:
            return None
        return market_offer

    @staticmethod
    def fetch_by_jump_url(jump_url):
        db.create_tables([MarketOfferBis])
        try:
            market_offer = MarketOfferBis.get(
                MarketOfferBis.jump_url == jump_url,
            )
        except peewee.DoesNotExist:
            return None
        return market_offer

    @staticmethod
    def fetch_by_id(offer_id):
        db.create_tables([MarketOfferBis])
        try:
            market_offer = MarketOfferBis.get(
                MarketOfferBis.id == offer_id,
            )
        except peewee.DoesNotExist:
            return None
        return market_offer
