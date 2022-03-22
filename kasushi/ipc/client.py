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
        self.online = asyncio.Event()
        self.closed = False
        self.ws = None
        self.session = None
        self.waiting_events = {}

        self.add_handler(LoginHandler)

        for handler in self.config['handlers']:
            self.add_handler(handler)

    def add_handler(self, handler: Type[Handler]):
        self.handlers[handler.name] = handler(self)

    async def send_request(self, name, *args, **kwargs):
        await self.online.wait()
        handler = self.handlers.get(name)
        if handler:
            return await self.handlers[name].send_request(*args, **kwargs)
        else:
            raise Exception("Handler not found. Available handlers: " + str(list(self.handlers.keys())))

    async def handle_message(self, data):
        type = data.get('type')
        rtoken = data.get('rtoken')
        handler = data.get('handler')
        if rtoken and type == 'response':
            event = self.waiting_events.get(rtoken)
            if event:
                event.response = data['data']
                event.set()
            else:
                pass
            return

        res = await self.handlers[handler].get_response(data['data'])
        if res:
            ret = {'data': res, 'handler': handler, 'rtoken': rtoken, 'type': 'response'}
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
                asyncio.ensure_future(
                    self.handlers['login'].send_request())  # Don't use client.send_request, we are not online yet.
                logger.debug("IPC Client login sent")

                async for msg in self.ws:
                    logger.debug("IPC Client message recv'd: " + str(msg))
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        await self.handle_message(json.loads(msg.data))
                    elif msg.type in (aiohttp.WSMsgType.CLOSED,
                                      aiohttp.WSMsgType.ERROR):
                        break
            self.online.clear()
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
