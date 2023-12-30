import polars as pl
from sqlalchemy import create_engine

conn = create_engine(f"sqlite:///database.db")
query = "SELECT * FROM transactions"

data = pl.read_database(query=query, connection=conn.connect())

res = pl.SQLContext(frame=data).execute(
"""
SELECT item, SUM(quantity)
FROM frame
GROUP BY item
ORDER BY SUM(quantity) DESC
""", eager=True)

print(res.collect())
