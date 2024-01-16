import csv

import peewee

from database import db
from models.items_bis import ItemBis

db.connect()

db.create_tables([ItemBis])


# Function to populate the table from CSV
def populate_table_from_csv(file_path):
    with open(file_path, "r") as csvfile:
        csvreader = csv.DictReader(csvfile)
        i = 0
        for row in csvreader:
            i += 1
            print(f"{i} - {row}")
            ItemBis.create(
                tier_name=row["tier_name"],
                item_name=row["item_name"],
                item_quantity=row["item_quantity"],
            )

# Example usage
csv_file_path = "items_bis.csv"
populate_table_from_csv(csv_file_path)
db.close()
