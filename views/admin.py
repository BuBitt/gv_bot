import discord
import settings


logger = settings.logging.getLogger(__name__)


class AdminClass(discord.ui.View):
    def __init__(self, new_item, points, changer_id) -> None:
        self.new_item = new_item
        self.points = points
        self.changer_id = changer_id
        super().__init__(timeout=None)