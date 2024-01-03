import csv
import peewee
from models.items import Items
from database import db

db.connect()

db.create_tables([Items])
# Function to populate the table from CSV
def populate_table_from_csv(file_path):
    with open(file_path, 'r') as csvfile:
        csvreader = csv.DictReader(csvfile)
        i = 0
        for row in csvreader:
            i += 1
            print(f"{i}/606 - {row['items']}")
            Items.create(item=row['items'])

# Example usage
csv_file_path = 'items.csv'
populate_table_from_csv(csv_file_path)
db.close()