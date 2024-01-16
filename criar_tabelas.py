from database import db
from models.account import Account
from models.guild import Guild
from models.mercado_bis import MarketOfferBis
from models.vendas_bis import SellInfoBis

db.create_tables([MarketOfferBis, SellInfoBis, Account, Guild])
