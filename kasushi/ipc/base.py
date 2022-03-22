import logging
from typing import Union, Optional, TYPE_CHECKING

from aiohttp.web_ws import WebSocketResponse

if TYPE_CHECKING:
    from .client import IPCClient
    from .server import IPCServer, WSData

logger = logging.getLogger(__name__)


class Handler:
    server_reply = False
    name: str = None
    wait = True

    def __init__(self, ipc: Union['IPCClient', 'IPCServer']):
        self.ipc = ipc

    async def finalize_response(self, raw_reponse: dict):
        return raw_reponse

    async def send_request(self, *args, **kwargs):
        self.ipc: 'IPCClient'
        data = {'handler': self.name, 'type': 'request', 'data': await self.get_request_data(*args, **kwargs)}

        if self.wait:
            return await self.finalize_response(await self.ipc.send_wait(data))
        else:
            await self.ipc.send(data)

    async def get_request_data(self, *args, **kwargs):
        self.ipc: 'IPCClient'
        return kwargs

    async def server_dispatch(self, sender_ws: 'WSData', data: dict):
        self.ipc: 'IPCServer'
        pass

    async def get_response(self, data: dict) -> Optional[dict]:
        self.ipc: 'IPCClient'
        pass


class BroadcastHandler(Handler):
    server_reply = True

    async def dispatch_to(self, sender_ws: 'WSData', data: dict):
        return self.ipc._active_ws

    async def aggregate_responses(self, responses: dict):
        ...

    async def server_dispatch(self, sender_ws: 'WSData', data: dict):
        self.ipc: 'IPCServer'
        responses = {}
        for ws in await self.dispatch_to(sender_ws, data['data']):
            bmsg = {'handler': self.name, 'type': 'request', 'data': data['data']}
            responses[ws] = (await self.ipc.send_wait(ws, bmsg))['data']

        ret = {'handler': data['handler'],
               'rtoken': data['rtoken'],
               'type': 'response',
               'data': await self.aggregate_responses(responses)}

        await self.ipc.send(sender_ws, ret)

    async def get_response(self, data: dict) -> Optional[dict]:
        self.ipc: 'IPCClient'
        statuses = {}
        for shard_id, shard in self.ipc.bot.shards.items():
            statuses[shard.id] = {
                'latency': shard.latency,
                'ws_ratelimited': shard.is_ws_ratelimited(),
                'closed': shard.is_closed(),
            }


class LoginHandler(Handler):
    server_reply = True
    name = 'login'

    async def finalize_response(self, raw_reponse: dict):
        self.ipc: 'IPCClient'
        if raw_reponse['success'] is True:
            self.ipc.online.set()

        return await super().finalize_response(raw_reponse)

    async def get_request_data(self):
        self.ipc: 'IPCClient'
        return {"shared_secret": self.ipc.config['shared_secret'],
                'guilds': [g.id for g in self.ipc.bot.guilds],
                'shards': list(self.ipc.bot.shards.keys())}

    async def server_dispatch(self, sender_ws: 'WSData', data: dict):
        self.ipc: 'IPCServer'
        ret = {
            'handler': data['handler'],
            'type': 'response',
            'rtoken': data['rtoken'],
            'data': await self.get_response(data, sender_ws)
        }
        logger.debug(f'Sending logging response {ret}')
        await sender_ws.ws.send_json(ret)
        return ret['data']['success']

    async def get_response(self, data: dict, sender_ws: 'WSData') -> Optional[dict]:
        self.ipc: 'IPCServer'  # Only in this case
        if data['data']['shared_secret'] == self.ipc.config['shared_secret']:
            guilds = data['data']['guilds']
            shards = data['data']['shards']

            for guild_id in guilds:
                self.ipc.guild_to_ws_mapping[guild_id] = sender_ws

            for shard_id in shards:
                self.ipc.shard_to_ws_mapping[shard_id] = sender_ws

            sender_ws.logged_in = True

            logged_in_ws = 0
            for act_wsd in self.ipc._active_ws:
                if act_wsd.logged_in:
                    logged_in_ws += 1
            sender_ws.remote_name = data['data'].get('name', 'Bot ' + str(logged_in_ws))

            return {"success": True, 'message': 'You are now authenticated'}
        else:
            return {"success": False, 'message': 'Invalid secret'}
