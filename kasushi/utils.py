from discord.ext import commands

import logging
import logging.config

logger = logging.getLogger(__name__)


async def configure(bot: commands.Bot, settings: dict):
    bot._kasushi_settings = settings


DEFAULT_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(message)s'
        },
        'complete': {
            'format': '%(asctime)s - %(levelname)s - %(filename)s - %(message)s',
        },
    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': True
        },
    }
}


def setup_logger():
    logging.config.dictConfig(DEFAULT_LOGGING)
    logging.info('Hello, log')
