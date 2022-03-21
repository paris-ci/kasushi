from discord.ext import commands


class IPC:
    type: str = None

    def __init__(self, bot: commands.AutoShardedBot, config: dict):
        self.bot = bot
        self.config = config
        self.online: bool = False

    async def async_setup(self):
        pass
