import logging
from typing import Dict, Any, List, Optional

import aiohttp.web
from aiohttp.web_ws import WebSocketResponse
from discord.ext import commands

from .base import IPC

logger = logging.getLogger(__name__)


class IPCServer(IPC):
    type = 'server'

    def __init__(self, bot: commands.AutoShardedBot, config: dict, *args, **kwargs):
        super().__init__(bot, config)
        self.clients_count = 0
        self._active_ws: List[WebSocketResponse] = []
        self._shard_to_ws_mapping: Dict[int, WebSocketResponse] = {}
        self._guild_to_ws_mapping: Dict[int, WebSocketResponse] = {}

    async def index(self, request):
        return aiohttp.web.Response(text='This is a websocket IPC server for Kasushi IPC')

    async def handle_login(self, ws: WebSocketResponse, data: Dict[str, Any]):
        if not data.get('type') == 'login':
            await ws.send_json({'type': 'login_failed', 'message': 'Invalid method type'})
            return False
        elif data.get('secret') != self.config.get('shared_secret'):
            await ws.send_json({'type': 'login_failed', 'message': 'Invalid secret'})
            return False
        else:
            shards = data.get('shards', [])
            for shard in shards:
                self._shard_to_ws_mapping[shard] = ws

            guilds = data.get('guilds', [])
            for guild in guilds:
                self._guild_to_ws_mapping[guild] = ws

            await ws.send_json({'type': 'login_success'})
            return True

    async def websocket_handler(self, request):
        # Got websocket connection
        ws = aiohttp.web.WebSocketResponse()
        await ws.prepare(request)
        self._active_ws.append(ws)
        self.clients_count += 1
        logged_in = False

        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                json_data = msg.json()

                if logged_in:
                    await self.handle_incoming_message(ws, json_data)
                else:
                    logged_in = await self.handle_login(ws, json_data)

        self.clients_count -= 1
        self._active_ws.remove(ws)
        return ws

    async def handle_incoming_message(self, ws, data):
        logger.debug(f'[{ws}] {data}')
        type = data.get('type')

        if type == 'get_guild_info':
            guild_pk = data.get('guild_pk')


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
        for ws in self._active_ws:
            await ws.close()

        await self._site.stop()
        logger.debug("IPC Server closed")
