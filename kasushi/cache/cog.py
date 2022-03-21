import inspect
from datetime import timedelta
from typing import Optional
from discord.ext import commands

from kasushi.exceptions import InvalidConfigurationError, InvalidRequirementsError

try:
    import aiomcache
except ImportError:
    raise InvalidRequirementsError("aiomcache is not installed.")


class Cache:
    def __init__(self, bot: commands.Bot, raw_cache: aiomcache.Client):
        self.bot = bot
        self._raw_cache = raw_cache

    async def bget(self, key: bytes, *, default: Optional[bytes] = None) -> bytes:
        return await self._raw_cache.get(key, default=default)

    async def bset(self, key: bytes, value: bytes, *, expire: Optional[timedelta] = None) -> bool:
        """
        Set a key in the cache. If expire is not None, the key will expire after the given time.
        """
        if expire is None:
            exptime = 0
        else:
            exptime = expire.total_seconds()

        return await self._raw_cache.set(key, value, exptime=exptime)

    async def bdelete(self, key: bytes) -> bool:
        """
        Delete a key from the cache.

        Returns True if the key was deleted, False if it was not found.
        """
        return await self._raw_cache.delete(key)

    async def bincr(self, key: bytes, increment: int = 1) -> bool:
        """
        Increment a key in the cache, without fetching it.
        """
        return await self._raw_cache.incr(key, increment)

    async def bdecr(self, key: bytes, decrement: int = 1) -> bool:
        """
        Decrement a key in the cache, without fetching it.
        """
        return await self._raw_cache.decr(key, decrement)

    async def get(self, key: str, *, default: Optional[str] = None) -> str:
        return (await self.bget(key.encode(), default=default.encode())).decode()

    async def set(self, key: str, value: str, *, expire: Optional[timedelta] = None) -> bool:
        return await self.bset(key.encode(), value.encode(), expire=expire)

    async def delete(self, key: str) -> bool:
        return await self.bdelete(key.encode())

    async def incr(self, key: str, increment: int = 1) -> bool:
        return await self.bincr(key.encode(), increment)

    async def decr(self, key: str, decrement: int = 1) -> bool:
        return await self.bdecr(key.encode(), decrement)


class CacheCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.raw_cache: Optional[aiomcache.Client] = None
        self.cache: Optional[Cache] = None

    async def config_check(self) -> None:
        config: dict = self.bot._kasushi_config
        cache_config: Optional[dict] = config.get('cache')
        if not cache_config:
            raise InvalidConfigurationError(
                message="Cache isn't configured. Please set the `cache` in your config."
            )

        cache_server = cache_config.get('server_ip')
        if not cache_server:
            raise InvalidConfigurationError(
                message="Cache isn't configured. Please set the `server_ip` key in your cache config."
            )

        cache_port = cache_config.get('server_port')
        if not cache_port:
            raise InvalidConfigurationError(
                message="Cache isn't configured. Please set the `server_port` key in your cache config."
            )

        return

    async def cog_load(self) -> None:
        await self.config_check()
        mc = aiomcache.Client("127.0.0.1", 11211)
        self.raw_cache = mc
        self.cache = Cache(self.bot, mc)
        self.bot.cache = self.cache

    async def cog_unload(self) -> None:
        pass


async def async_setup(bot: commands.Bot):
    """
    The async setup function defining the jishaku.cog and jishaku extensions.
    """

    await bot.add_cog(CacheCog(bot=bot))


def setup(bot: commands.Bot):
    """
    The setup function defining the jishaku.cog and jishaku extensions.
    """

    if inspect.iscoroutinefunction(bot.add_cog):
        return async_setup(bot)

    bot.add_cog(CacheCog(bot=bot))
