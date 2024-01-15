from database import db
from ast import Dict
import settings
import peewee


logger = settings.logging.getLogger(__name__)


class Donation(peewee.Model):
    crafter_id: int = peewee.BigIntegerField()
    crafter_name: str = peewee.CharField(max_length=255)
    donor_id: int = peewee.BigIntegerField()
    donor_name: str = peewee.CharField(max_length=255)
    item: str = peewee.CharField(max_length=255)
    quantity: int = peewee.IntegerField()
    timestamp: str = peewee.CharField(max_length=255)
    print_proof: str = peewee.CharField(max_length=1024)


    class Meta:
        database = db
        db_table = "donation"

    @staticmethod
    def new(transaction_dict: Dict):
        try:
            transaction = Donation.create(
                crafter_id=transaction_dict.get("crafter_id"),
                crafter_name=transaction_dict.get("crafter_name"),
                donor_id=transaction_dict.get("donor_id"),
                donor_name=transaction_dict.get("donor_name"),
                item=transaction_dict.get("item"),
                quantity=transaction_dict.get("quantity"),
                print_proof=transaction_dict.get("print"),
                timestamp=transaction_dict.get("timestamp"),
            )
        except peewee.OperationalError:
            db.create_tables([Donation])
            transaction = Donation.create(
                crafter_id=transaction_dict.get("crafter_id"),
                crafter_name=transaction_dict.get("crafter_name"),
                donor_id=transaction_dict.get("donor_id"),
                donor_name=transaction_dict.get("donor_name"),
                item=transaction_dict.get("item"),
                quantity=transaction_dict.get("quantity"),
                print_proof=transaction_dict.get("print"),
                timestamp=transaction_dict.get("timestamp"),
            )

        return transaction
