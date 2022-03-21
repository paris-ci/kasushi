# Test websockets connection
import discord
import pytest
import asyncio

from kasushi.ipc.client import IPCClient
from kasushi.ipc.server import IPCServer
from utils import setup_logger

setup_logger()

configuration = {
    "server_host": "http://127.0.0.1:12321",  # Ignored on shard 0
    "server_listen_host": "0.0.0.0",
    "server_listen_port": 12321,
    "shared_secret": "secret",  # This is used to authenticate with the IPC server.
}


class BotMock:
    def __init__(self):
        self.shards = {}
        self.guilds = []


@pytest.mark.asyncio
async def test_simple_login():
    botMockServer = BotMock()
    botMockClient = BotMock()

    botMockServer.shards = {0: None}
    botMockServer.guilds = [discord.Object(id=0), discord.Object(id=1), discord.Object(id=2)]

    botMockClient.shards = {1: None}
    botMockClient.guilds = [discord.Object(id=10), discord.Object(id=11)]

    server = IPCServer(botMockServer, configuration)
    await server.async_setup()

    client = IPCClient(botMockClient, configuration)
    await client.async_setup()

    await asyncio.sleep(2)
    assert server.clients_count == 1

    await server.async_teardown()
    await client.async_teardown()
