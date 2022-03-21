import discord
import pytest
import asyncio

from kasushi.ipc.handlers import GuildInfoHandler
from kasushi.ipc.client import IPCClient
from kasushi.ipc.server import IPCServer
from utils import setup_logger

setup_logger()

configuration = \
    {
        "shared_secret": "secret",  # This is used to authenticate with the IPC server.
        "server": {
            "host": "0.0.0.0",
            "port": 12321,
        },
        "client": {
            "server_url": "http://127.0.0.1:12321",
        },
        "handlers": [GuildInfoHandler],  # See above for handlers.
    }


class BotMock:
    def __init__(self):
        self.shards = {}
        self.guilds = []


@pytest.mark.asyncio
async def test_simple_login():
    botMockClient1 = BotMock()
    botMockClient2 = BotMock()

    botMockClient1.shards = {0: None}
    botMockClient1.guilds = [discord.Object(id=0), discord.Object(id=1), discord.Object(id=2)]

    botMockClient2.shards = {1: None}
    botMockClient2.guilds = [discord.Object(id=10), discord.Object(id=11)]

    server = IPCServer(configuration)
    await server.async_setup()

    client1 = IPCClient(botMockClient1, configuration)
    client2 = IPCClient(botMockClient2, configuration)
    await client1.async_setup()
    await client2.async_setup()

    await asyncio.sleep(2)
    assert len(server._active_ws) == 2
    assert 0 in server.shard_to_ws_mapping.keys()
    assert 1 in server.shard_to_ws_mapping.keys()

    await server.async_teardown()
    await client1.async_teardown()
    await client2.async_teardown()
