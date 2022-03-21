import inspect
from typing import Optional

from discord.ext import commands

from kasushi.exceptions import InvalidConfigurationError
from kasushi.ipc.base import IPC
from kasushi.ipc.client import IPCClient
from kasushi.ipc.server import IPCServer


class IPCCog(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot) -> None:
        self.bot = bot
        self.bot.ipc = IPC(bot, {})

    async def config_check(self) -> dict:
        config: dict = self.bot._kasushi_config
        ipc_config: Optional[dict] = config.get('ipc')
        if not ipc_config:
            raise InvalidConfigurationError(
                message="IPC isn't configured. Please set the `ipc` in your config."
            )

        ipc_server = ipc_config.get('server_host')
        if not ipc_server:
            raise InvalidConfigurationError(
                message="IPC isn't configured. Please set the `server_host` key in your ipc config."
            )

        shared_secret = ipc_config.get('shared_secret')
        if not shared_secret:
            raise InvalidConfigurationError(
                message="IPC isn't configured. "
                        "Please set the `shared_secret` key in your ipc config to a random string of your choosing."
            )

        return config

    async def cog_load(self) -> None:
        config = await self.config_check()

    async def on_ready(self) -> None:
        config = await self.config_check()

        shard_zero = self.bot.get_shard(0)
        if shard_zero:
            self.bot.ipc = IPCServer(self.bot, config['ipc'])
        else:
            self.bot.ipc = IPCClient(self.bot, config['ipc'])

        await self.bot.ipc.async_setup()

    async def cog_unload(self) -> None:
        await self.bot.ipc.async_teardown()


async def async_setup(bot: commands.AutoShardedBot):
    """
    The async setup function defining the jishaku.cog and jishaku extensions.
    """

    await bot.add_cog(IPCCog(bot=bot))


def setup(bot: commands.AutoShardedBot):
    """
    The setup function defining the jishaku.cog and jishaku extensions.
    """

    if inspect.iscoroutinefunction(bot.add_cog):
        return async_setup(bot)

    bot.add_cog(IPCCog(bot=bot))
