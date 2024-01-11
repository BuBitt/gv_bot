import csv

import peewee

from database import db
from models.items import Items

db.connect()

db.create_tables([Items])


# Function to populate the table from CSV
def populate_table_from_csv(file_path):
    with open(file_path, "r") as csvfile:
        csvreader = csv.DictReader(csvfile)
        i = 0
        for row in csvreader:
            i += 1
            print(f"{i} - {row}")
            Items.create(
                item=row["\ufeffitem"],
                add_by_id=row["add_by_id"],
                points=row["points"],
            )


# Example usage
csv_file_path = "items.csv"
populate_table_from_csv(csv_file_path)
db.close()
