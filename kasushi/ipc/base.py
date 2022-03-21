from typing import Union, Optional, TYPE_CHECKING

from aiohttp.web_ws import WebSocketResponse

if TYPE_CHECKING:
    from .client import IPCClient
    from .server import IPCServer


class Handler:
    server_reply = False
    name: str = None
    wait = True

    def __init__(self, ipc: Union['IPCClient', 'IPCServer']):
        self.ipc = ipc

    async def send_request(self, *args, **kwargs):
        self.ipc: 'IPCClient'
        data = {'handler': self.name, 'type': 'request', 'data': await self.get_request_data(*args, **kwargs)}

        if self.wait:
            await self.ipc.send_wait(data)
        else:
            await self.ipc.send(data)

    async def get_request_data(self, *args, **kwargs):
        self.ipc: 'IPCClient'
        return {}

    async def server_dispatch(self, sender_ws: WebSocketResponse, data: dict):
        self.ipc: 'IPCServer'
        pass

    async def get_response(self, data: dict) -> Optional[dict]:
        self.ipc: 'IPCClient'
        pass


class LoginHandler(Handler):
    server_reply = True
    name = 'login'

    async def get_request_data(self):
        self.ipc: 'IPCClient'
        return {"shared_secret": self.ipc.config['shared_secret'],
                'guilds': [g.id for g in self.ipc.bot.guilds],
                'shards': list(self.ipc.bot.shards.keys())}

    async def server_dispatch(self, sender_ws: WebSocketResponse, data: dict):
        self.ipc: 'IPCServer'
        ret = {
            'handler': data['handler'],
            'type': 'response',
            'rtoken': data['rtoken'],
            'data': await self.get_response(data, sender_ws)
        }
        await sender_ws.send_json(ret)

    async def get_response(self, data: dict, sender_ws: WebSocketResponse) -> Optional[dict]:
        self.ipc: 'IPCServer'  # Only in this case
        if data['data']['shared_secret'] == self.ipc.config['shared_secret']:
            guilds = data['data']['guilds']
            shards = data['data']['shards']

            for guild_id in guilds:
                self.ipc.guild_to_ws_mapping[guild_id] = sender_ws

            for shard_id in shards:
                self.ipc.shard_to_ws_mapping[shard_id] = sender_ws

            return {"success": True, 'message': 'You are now authenticated'}
        else:
            return {"success": False, 'message': 'Invalid secret'}

