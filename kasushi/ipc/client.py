import asyncio
import json
import logging

import aiohttp
from discord.ext import commands

from .base import IPC

logger = logging.getLogger(__name__)


class IPCClient(IPC):
    type: str = None

    def __init__(self, bot: commands.AutoShardedBot, config: dict):
        super().__init__(bot, config)
        self._URL = config['server_host'] + "/ws"
        self.closed = False
        self.ws = None
        self.session = None

    async def handle_message(self, data):
        type = data['type']
        if type == 'login_success':
            logger.info("IPC Client authenticated")
            self.online = True

    async def async_setup(self):
        self.session = aiohttp.ClientSession()
        asyncio.create_task(self.background())

    async def background(self):
        first = True
        logger.debug("Starting IPC Client")
        while not self.closed:
            if first:
                logger.debug("Starting first IPC Client connection to server")
                first = False
            else:
                logger.debug("Starting IPC Client re-connection to server in 5 seconds")
                await asyncio.sleep(2)

            async with self.session.ws_connect(self._URL) as ws:
                logger.debug("IPC Client websocket connection established")
                await ws.send_json({'type': 'login',
                                    'secret': self.config['shared_secret'],
                                    'shards': list(self.bot.shards.keys()),
                                    'guilds': [guild.id for guild in self.bot.guilds]
                                    })
                logger.debug("IPC Client login sent")
                self.ws = ws
                async for msg in self.ws:
                    logger.debug("IPC Client message recv'd: " + str(msg))
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        await self.handle_message(json.loads(msg.data))
                    elif msg.type in (aiohttp.WSMsgType.CLOSED,
                                      aiohttp.WSMsgType.ERROR):
                        break
            logger.debug("IPC Client websocket closed")
            await asyncio.sleep(2)

    async def async_teardown(self):
        logger.debug("IPC Client closing")
        self.closed = True
        self.online = False

        if self.ws:
            logger.debug("IPC Client closing websocket connection")
            await self.ws.close()
            logger.debug("IPC Client websocket connection closed")

        if self.session:
            logger.debug("IPC Client closing session")
            await self.session.close()
            logger.debug("IPC Client session closed")


type = 'client'
