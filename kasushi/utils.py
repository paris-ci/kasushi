from discord.ext import commands


async def configure(bot: commands.Bot, settings: dict):
    bot._kasushi_settings = settings
