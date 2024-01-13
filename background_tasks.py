import settings as st
from discord.ext import commands, tasks


@tasks.loop(seconds=300)  # Run the task every 60 seconds
async def fetch_crafters_bt_role():
    # Your background task logic goes here
    print("Running background task...")
