from ast import Dict
import peewee
from database import db


class Transaction(peewee.Model):
    manager_id: int = peewee.IntegerField()
    manager_name: str = peewee.CharField(max_length=255)
    requester_id: int = peewee.IntegerField()
    requester_name: str = peewee.CharField(max_length=255)
    item: str = peewee.CharField(max_length=255)
    quantity: int = peewee.IntegerField()
    operation_type: str = peewee.CharField(max_length=255)
    print_proof: str = peewee.CharField(max_length=1024)
    timestamp: str = peewee.CharField(max_length=255)

    class Meta:
        database = db
        db_table = 'transactions'

    @staticmethod
    def new(transaction_dict: Dict):
        try:
            transaction = Transaction.create(
                manager_id=transaction_dict.get("manager_id"),
                manager_name=transaction_dict.get("manager_name"),
                requester_id=transaction_dict.get("requester_id"),
                requester_name=transaction_dict.get("requester_name"),
                item=transaction_dict.get("item"),
                quantity=transaction_dict.get("quantity"),
                operation_type=transaction_dict.get("operation_type"),
                print_proof=transaction_dict.get("print"),
                timestamp=transaction_dict.get("timestamp"),
            )
        except peewee.OperationalError:
            Transaction.create_table()
            transaction = Transaction.create(
                manager_id=transaction_dict.get("manager_id"),
                manager_name=transaction_dict.get("manager_name"),
                requester_id=transaction_dict.get("requester_id"),
                requester_name=transaction_dict.get("requester_name"),
                item=transaction_dict.get("item"),
                quantity=transaction_dict.get("quantity"),
                operation_type=transaction_dict.get("operation_type"),
                print_proof=transaction_dict.get("print"),
                timestamp=transaction_dict.get("timestamp"),
            )
            
        return transaction
