from typing import Optional

from aiohttp.web_ws import WebSocketResponse

from .base import Handler
from .client import IPCClient
from .server import IPCServer


class GuildInfoHandler(Handler):
    name = 'guild_info'

    async def get_request_data(self, guild_id: int):
        self.ipc: 'IPCClient'
        return {"guild_id": guild_id}

    async def server_dispatch(self, sender_ws: WebSocketResponse, data: dict):
        self.ipc: 'IPCServer'
        await self.ipc.guild_to_ws_mapping[data['data']['guild_id']].send_json(data)

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
