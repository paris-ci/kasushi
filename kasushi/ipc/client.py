import asyncio
import json
import logging
import random
import uuid
from typing import Dict, Type

import aiohttp
from discord.ext import commands

from .base import Handler, LoginHandler

logger = logging.getLogger(__name__)


class WaitingEvent(asyncio.Event):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response = None


class IPCClient:
    type: str = None

    def __init__(self, bot: commands.AutoShardedBot, config: dict):
        self.handlers: Dict[str, Handler] = {}
        self.bot = bot
        self.config = config
        self._URL = config['client']['server_url'] + "/ws"
        self.online = False
        self.closed = False
        self.ws = None
        self.session = None
        self.waiting_events = {}

        self.add_handler(LoginHandler)

    def add_handler(self, handler: Type[Handler]):
        self.handlers[handler.name] = handler(self)

    async def handle_message(self, data):
        type = data.get('type')
        rtoken = data.get('rtoken')
        handler = data.get('handler')
        if rtoken and type == 'response':
            event = self.waiting_events.get(rtoken)
            if event:
                event.response = data['data']
                event.set()
                return

        ret = await self.handlers[handler].get_response(data['data'])
        if ret:
            ret['handler'] = handler
            ret['rtoken'] = rtoken
            ret['type'] = 'response'
            await self.send(ret)

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
                self.ws = ws
                await self.handlers['login'].send_request()
                logger.debug("IPC Client login sent")

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

    async def send_wait(self, data):
        data['rtoken'] = uuid.uuid4().hex
        event = WaitingEvent()
        self.waiting_events[data['rtoken']] = event
        await self.send(data)
        await event.wait()
        del self.waiting_events[data['rtoken']]

        return event.response

    async def send(self, data):
        await self.ws.send_json(data)
