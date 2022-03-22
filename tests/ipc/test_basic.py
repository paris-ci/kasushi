import discord
import pytest
import asyncio
import logging

from kasushi.ipc.handlers import GuildInfoHandler, ShardStatusHandler, FindMemberHandler
from kasushi.ipc.client import IPCClient
from kasushi.ipc.server import IPCServer
from utils import setup_logger

setup_logger()
logger = logging.getLogger(__name__)

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
        "handlers": [GuildInfoHandler, ShardStatusHandler, FindMemberHandler],  # See above for handlers.
    }


class BotMock:
    def __init__(self):
        self.shards = {}
        self.guilds = []

    def get_guild(self, id):
        for guild in self.guilds:
            if guild.id == id:
                return guild
        return None


class GuildMock(discord.Object):
    def __init__(self, id):
        super().__init__(id)
        self.name = "Guild {}".format(id)
        self.member_count = id * 121

    def get_member(self, id):
        if str(self.id).startswith(str(id)):
            return True


class ShardMock(discord.Object):
    def __init__(self, id):
        super().__init__(id)
        self.latency = id * 201

    def is_ws_ratelimited(self):
        return False

    def is_closed(self):
        return False


@pytest.mark.asyncio
async def test_simple_login():
    logger.info("Starting test_simple_login")
    botMockClient1 = BotMock()
    botMockClient2 = BotMock()

    botMockClient1.shards = {0: ShardMock(0)}
    botMockClient1.guilds = [GuildMock(id=0), GuildMock(id=1), GuildMock(id=2)]

    botMockClient2.shards = {1: ShardMock(1)}
    botMockClient2.guilds = [GuildMock(id=10), GuildMock(id=11)]

    server = IPCServer(configuration)
    await server.async_setup()

    client1 = IPCClient(botMockClient1, configuration)
    client2 = IPCClient(botMockClient2, configuration)
    await client1.async_setup()
    await client2.async_setup()

    await client1.online.wait()
    await client2.online.wait()

    assert len(server._active_ws) == 2
    assert 0 in server.shard_to_ws_mapping.keys()
    assert 1 in server.shard_to_ws_mapping.keys()

    await server.async_teardown()
    await client1.async_teardown()
    await client2.async_teardown()


@pytest.mark.asyncio
async def test_direct_query():
    botMockClient1 = BotMock()
    botMockClient2 = BotMock()

    botMockClient1.shards = {0: ShardMock(0)}
    botMockClient1.guilds = [GuildMock(id=0), GuildMock(id=1), GuildMock(id=2)]

    botMockClient2.shards = {1: ShardMock(1)}
    botMockClient2.guilds = [GuildMock(id=10), GuildMock(id=11)]

    server = IPCServer(configuration)
    await server.async_setup()

    client1 = IPCClient(botMockClient1, configuration)
    client2 = IPCClient(botMockClient2, configuration)
    await client1.async_setup()
    await client2.async_setup()

    guild_info = await client1.send_request('guild_info', guild_id=10)

    assert guild_info['success'] is True
    assert guild_info['guild']['id'] == 10
    assert guild_info['guild']['name'] == "Guild 10"
    assert guild_info['guild']['member_count'] == 1210

    await server.async_teardown()
    await client1.async_teardown()
    await client2.async_teardown()


@pytest.mark.asyncio
async def test_broadcast_query():
    botMockClient1 = BotMock()
    botMockClient2 = BotMock()

    botMockClient1.shards = {0: ShardMock(0)}
    botMockClient1.guilds = [GuildMock(id=0), GuildMock(id=1), GuildMock(id=2)]

    botMockClient2.shards = {1: ShardMock(1)}
    botMockClient2.guilds = [GuildMock(id=10), GuildMock(id=11)]

    server = IPCServer(configuration)
    await server.async_setup()

    client1 = IPCClient(botMockClient1, configuration)
    client2 = IPCClient(botMockClient2, configuration)
    await client1.async_setup()
    await client2.async_setup()

    shard_status = await client1.send_request('shard_status')

    assert shard_status['0']['latency'] == 0
    assert shard_status['1']['latency'] == 201
    assert shard_status['0']['ws_ratelimited'] is False
    assert shard_status['1']['ws_ratelimited'] is False
    assert shard_status['0']['closed'] is False
    assert shard_status['1']['closed'] is False

    await server.async_teardown()
    await client1.async_teardown()
    await client2.async_teardown()


@pytest.mark.asyncio
async def test_find_member():
    botMockClient1 = BotMock()
    botMockClient2 = BotMock()

    botMockClient1.shards = {0: ShardMock(0)}
    botMockClient1.guilds = [GuildMock(id=0), GuildMock(id=1), GuildMock(id=2)]

    botMockClient2.shards = {1: ShardMock(1)}
    botMockClient2.guilds = [GuildMock(id=10), GuildMock(id=11)]

    server = IPCServer(configuration)
    await server.async_setup()

    client1 = IPCClient(botMockClient1, configuration)
    client2 = IPCClient(botMockClient2, configuration)
    await client1.async_setup()
    await client2.async_setup()

    find_member = await client1.send_request('find_member', user_id=1)

    assert len(find_member) == 3
    assert 1 in find_member
    assert 10 in find_member
    assert 11 in find_member

    await server.async_teardown()
    await client1.async_teardown()
    await client2.async_teardown()
