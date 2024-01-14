import logging
import os
import pathlib
from logging.config import dictConfig

import discord
from dotenv import load_dotenv

load_dotenv()


# DISCORD CONFIG
DISCORD_API_SECRET = os.getenv("DISCORD_API_TOKEN")
GUILDS_ID = discord.Object(id=int(os.getenv("GUILD")))


# DISCORD ROLES
MEMBRO_INICIANTE_ROLE = int(os.getenv("DISCORD_MEMBRO_INICIANTE_ROLE"))
VICE_LIDER_ROLE = int(os.getenv("DISCORD_VICE_LIDER_ROLE"))
COMMANDER_ROLE = int(os.getenv("DISCORD_COMMANDER_ROLE"))
CRAFTER_ROLE = int(os.getenv("DISCORD_CRAFTER_ROLE"))
OFFICER_ROLE = int(os.getenv("DISCORD_OFFICER_ROLE"))
LEADER_ROLE = int(os.getenv("DISCORD_LEADER_ROLE"))
MEMBRO_ROLE = int(os.getenv("DISCORD_MEMBRO_ROLE"))


# DISCORD CHANNELS
DONATION_CHANNEL = int(os.getenv("DISCORD_DONATION_CHANNEL"))
MARKET_OFFER_CHANNEL = int(os.getenv("DISCORD_MARKET_OFFER_CHANNEL"))
MARKET_LOGS = int(os.getenv("DISCORD_MARKET_LOGS"))
MARKET_BIS_OFFER_CHANNEL = int(os.getenv("DISCORD_MARKET_BIS_OFFER_CHANNEL"))
MARKET_BIS_LOG_CHANNEL = int(os.getenv("DISCORD_MARKET_BIS_LOG_CHANNEL"))
ADMIN_LOGS_CHANNEL = int(os.getenv("DISCORD_ADMIN_LOGS_CHANNEL"))
MARKET_IMAGES_DUMP = int(os.getenv("DISCORD_MARKET_IMAGES_DUMP"))
DONATION_PANEL_CHANNEL = int(os.getenv("DISCORD_DONATION_PANEL_CHANNEL"))


# POSTGRES CONFIG
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# CONFIG DIRETÓRIOS
BASE_DIR = pathlib.Path(__file__).parent
CMDS_DIR = BASE_DIR / "cmds"
COGS_DIR = BASE_DIR / "cogs"
SCMDS_DIR = BASE_DIR / "slashcmds"

# LOG CONFIG
LOGGING_CONFIG = {
    "version": 1,
    "disabled_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)-10s - %(asctime)s - %(module)-15s : %(message)s"
        },
        "standard": {"format": "%(levelname)-10s - %(name)-15s : %(message)s"},
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "console2": {
            "level": "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "logs/infos.log",
            "mode": "w",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "bot": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "discord": {
            "handlers": ["console2", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

dictConfig(LOGGING_CONFIG)
