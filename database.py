from peewee import *
from playhouse.postgres_ext import *
from settings import DB_HOST, DB_NAME, DB_PASSWORD, DB_PORT, DB_USER

# general_db_name = "database.db"
db = PostgresqlExtDatabase(
    DB_NAME,
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
)
# db = peewee.SqliteDatabase(db_name)
