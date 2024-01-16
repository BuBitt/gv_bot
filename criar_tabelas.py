from database import db
from models.account import Account
from models.donation import Donation
from models.guild import Guild
from models.mercado import MarketOffer
from models.mercado_bis import MarketOfferBis
from models.vendas import SellInfo
from models.vendas_bis import SellInfoBis

db.create_tables(
    [
        MarketOfferBis,
        SellInfoBis,
        Account,
        Guild,
        Donation,
        MarketOffer,
        SellInfo,
    ]
)
