import inspect
from typing import Optional

from discord.ext import commands

from kasushi.exceptions import InvalidConfigurationError
from kasushi.ipc.client import IPCClient
from kasushi.ipc.server import IPCServer


class IPCCog(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot) -> None:
        self.server = None
        self.bot = bot

    async def config_check(self) -> dict:
        config: dict = self.bot._kasushi_config['ipc']

        shared_secret = config.get('shared_secret')
        if not shared_secret:
            raise InvalidConfigurationError('IPC `shared_secret` is not set')
        elif shared_secret == '' or shared_secret == 'secret':
            raise InvalidConfigurationError('IPC `shared_secret` is not secret enough')

        try:
            ipc_server = config['ipc_server']
        except KeyError:
            raise InvalidConfigurationError('IPC `ipc_server` is not set')
        else:
            try:
                ipc_server_host = ipc_server['host']
            except KeyError:
                raise InvalidConfigurationError('IPC `ipc_server.host` is not set')

            try:
                ipc_server_port = ipc_server['port']
            except KeyError:
                raise InvalidConfigurationError('IPC `ipc_server.port` is not set')

        try:
            ipc_client = config['client']
        except KeyError:
            raise InvalidConfigurationError('IPC `client` is not set')
        else:
            try:
                ipc_client_server_url = ipc_client['server_url']
            except KeyError:
                raise InvalidConfigurationError('IPC `client.server_url` is not set')
            else:
                if not ipc_client_server_url.startswith('http'):
                    raise InvalidConfigurationError('IPC `client.server_url` must start with http or https')

        config.setdefault('handlers', [])

        return config

    async def cog_load(self) -> None:
        config = await self.config_check()

    async def on_ready(self) -> None:
        config = await self.config_check()

        shard_zero = self.bot.get_shard(0)
        if shard_zero:
            self.server = IPCServer(config['server'])

            for handler in config['handlers']:
                self.server.add_handler(handler)

            await self.server.async_setup()

        self.bot.ipc = IPCClient(self.bot, config['client'])
        for handler in config['handlers']:
            self.bot.ipc.add_handler(handler)

        await self.bot.ipc.async_setup()

    async def cog_unload(self) -> None:
        if self.server:
            await self.server.async_teardown()

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
