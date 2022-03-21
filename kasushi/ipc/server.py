import logging
from typing import Dict, Any, List, Optional, Type

import aiohttp.web
from aiohttp.web_ws import WebSocketResponse
from discord.ext import commands

from .base import Handler, LoginHandler

logger = logging.getLogger(__name__)


class IPCServer:
    def __init__(self, config: dict, *args, **kwargs):
        self.config = config

        self._active_ws: List[WebSocketResponse] = []

        self.return_paths: Dict[str, WebSocketResponse] = {}

        self.handlers: Dict[str, Handler] = {}

        self.shard_to_ws_mapping: Dict[int, WebSocketResponse] = {}
        self.guild_to_ws_mapping: Dict[int, WebSocketResponse] = {}
        self.add_handler(LoginHandler)

    def add_handler(self, handler: Type[Handler]):
        self.handlers[handler.name] = handler(self)

    async def index(self, request):
        return aiohttp.web.Response(text='This is a websocket IPC server for Kasushi IPC')

    async def websocket_handler(self, request):
        # Got websocket connection
        ws = aiohttp.web.WebSocketResponse()
        await ws.prepare(request)
        self._active_ws.append(ws)
        logged_in = False

        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                json_data = msg.json()

                if logged_in:
                    await self.handle_incoming_message(ws, json_data)
                else:
                    await self.handle_login_message(ws, json_data)

        self._active_ws.remove(ws)
        return ws

    async def handle_incoming_message(self, ws, data):
        logger.debug(f'[{ws}] {data}')
        type = data.get('type')
        handler = data.get('handler')
        rtoken = data.get('rtoken')
        if type == 'request':
            handler_class = self.handlers.get(handler)
            if handler_class:
                if rtoken and not handler_class.server_reply:
                    self.return_paths[rtoken] = ws
                await handler_class.server_dispatch(ws, data)
            else:
                logger.warning(f'[{ws}] Handler {handler} not found, cannot forward')
        else:
            if rtoken:
                try:
                    await self.return_paths[rtoken].send_json(data)
                except KeyError:
                    logger.warning(f'[{ws}] No return path for {rtoken}')
                    return

    async def handle_login_message(self, ws, data):
        data['handler'] = 'login'
        data['type'] = 'request'
        await self.handle_incoming_message(ws, data)

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
        for ws in self._active_ws[:]:
            logger.debug(f"Closing {ws}")
            await ws.close()
            logger.debug(f"Closed {ws}")

        await self._site.stop()
        logger.debug("IPC Server closed")
