from typing import Optional

from aiohttp.web_ws import WebSocketResponse

from .base import Handler, BroadcastHandler
from .client import IPCClient
from .server import IPCServer


class GuildInfoHandler(Handler):
    name = 'guild_info'

    async def get_request_data(self, guild_id: int):
        self.ipc: 'IPCClient'
        return {"guild_id": guild_id}

    async def server_dispatch(self, sender_ws: WebSocketResponse, data: dict):
        self.ipc: 'IPCServer'
        await self.ipc.send(self.ipc.guild_to_ws_mapping[data['data']['guild_id']], data)

    async def get_response(self, data: dict) -> Optional[dict]:
        self.ipc: 'IPCClient'
        guild = self.ipc.bot.get_guild(data['guild_id'])
        if guild:
            return {
                'success': True,
                'guild': {
                    'name': guild.name,
                    'id': guild.id,
                    'member_count': guild.member_count,
                }
            }
        else:
            return {
                'success': False,
                'message': 'Guild not found'
            }


class ShardStatusHandler(BroadcastHandler):
    server_reply = True
    name = 'shard_status'

    async def aggregate_responses(self, responses: dict):
        res = {}
        for ws, response in responses.items():
            res.update(response.items())
        return res

    async def get_response(self, data: dict) -> dict:
        self.ipc: 'IPCClient'
        statuses = {}
        for shard_id, shard in self.ipc.bot.shards.items():
            statuses[shard.id] = {
                'latency': shard.latency,
                'ws_ratelimited': shard.is_ws_ratelimited(),
                'closed': shard.is_closed(),
            }

        return statuses
