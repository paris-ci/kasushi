import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional, Type

import aiohttp.web
from aiohttp.web_ws import WebSocketResponse
from discord.ext import commands

from .base import Handler, LoginHandler
from .client import WaitingEvent

logger = logging.getLogger(__name__)


class WSData:
    def __init__(self, ws: WebSocketResponse):
        self.ws = ws
        self.logged_in = False
        self.remote_name = "???"

    def __str__(self):
        return self.remote_name


class IPCServer:
    def __init__(self, config: dict, *args, **kwargs):
        self.config = config
        self.waiting_events: Dict[str, WaitingEvent] = {}

        self._active_ws: List[WSData] = []

        self.return_paths: Dict[str, WSData] = {}

        self.handlers: Dict[str, Handler] = {}

        self.shard_to_ws_mapping: Dict[int, WSData] = {}
        self.guild_to_ws_mapping: Dict[int, WSData] = {}
        self.add_handler(LoginHandler)

        for handler in self.config['handlers']:
            self.add_handler(handler)

    def add_handler(self, handler: Type[Handler]):
        self.handlers[handler.name] = handler(self)

    async def index(self, request):
        return aiohttp.web.Response(text='This is a websocket IPC server for Kasushi IPC')

    async def websocket_handler(self, request):
        # Got websocket connection
        wsd = WSData(aiohttp.web.WebSocketResponse())
        await wsd.ws.prepare(request)
        self._active_ws.append(wsd)

        async for msg in wsd.ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                json_data = msg.json()

                if wsd.logged_in:
                    asyncio.create_task(self.handle_incoming_message(wsd, json_data))
                else:
                    asyncio.create_task(self.handle_login_message(wsd, json_data))

        self._active_ws.remove(wsd)
        return wsd

    async def handle_incoming_message(self, wsd: WSData, data: dict):
        type = data.get('type')
        handler = data.get('handler')
        rtoken = data.get('rtoken')
        if type == 'request':
            logger.debug(f'[{wsd}] -> {data}')
            handler_class = self.handlers.get(handler)
            if handler_class:
                if rtoken and not handler_class.server_reply:
                    self.return_paths[rtoken] = wsd
                await handler_class.server_dispatch(wsd, data)
            else:
                logger.warning(f'[{wsd}] Handler {handler} not found, cannot forward')
        else:
            logger.debug(f'[{wsd}] <- {data}')
            if rtoken:
                maybe_event = self.waiting_events.get(rtoken)
                if maybe_event:
                    maybe_event.response = data
                    maybe_event.set()
                else:
                    try:
                        await self.return_paths[rtoken].ws.send_json(data)
                    except KeyError:
                        logger.warning(f'[{wsd}] No return path for {rtoken}')
                        return

    async def handle_login_message(self, wsd: WSData, data):
        data['handler'] = 'login'
        data['type'] = 'request'
        await self.handle_incoming_message(wsd, data)

    async def async_setup(self):
        app = aiohttp.web.Application()
        app.add_routes([
            aiohttp.web.get('/', self.index),
            aiohttp.web.get('/ws', self.websocket_handler),
        ])
        self._app = app
        self._runner = aiohttp.web.AppRunner(app)
        await self._runner.setup()
        self._site = aiohttp.web.TCPSite(self._runner, self.config.get('server_listen_host', '0.0.0.0'),
                                         self.config.get('server_listen_port', 12321))
        await self._site.start()

    async def async_teardown(self):
        logger.debug("IPC Server closing")
        for wsd in self._active_ws[:]:
            logger.debug(f"Closing {wsd}")
            await wsd.ws.close()
            logger.debug(f"Closed {wsd}")

        await self._site.stop()
        logger.debug("IPC Server closed")

    async def send_wait(self, wsd: WSData, data):
        data['rtoken'] = uuid.uuid4().hex
        event = WaitingEvent()
        self.waiting_events[data['rtoken']] = event
        await self.send(wsd, data)
        await event.wait()
        del self.waiting_events[data['rtoken']]

        return event.response

    async def send(self, wsd: WSData, data):
        logger.debug(f'[{wsd}] !-> {data}')
        await wsd.ws.send_json(data)
