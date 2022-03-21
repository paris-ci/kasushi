[![Python versions](https://img.shields.io/pypi/pyversions/kasushi.svg)](https://pypi.python.org/pypi/kasushi)
[![License](https://img.shields.io/pypi/l/kasushi.svg)](https://github.com/paris-ci/kasushi/blob/master/LICENSE)
[![Status](https://img.shields.io/pypi/status/kasushi.svg)](https://pypi.python.org/pypi/kasushi)
[![Issues](https://img.shields.io/github/issues/paris-ci/kasushi.svg?colorB=3333ff)](https://github.com/paris-ci/kasushi/issues)
[![Commit activity](https://img.shields.io/github/commit-activity/w/paris-ci/kasushi.svg)](https://github.com/paris-ci/kasushi/commits)

***

<h1 align="center">
Kasushi
</h1>
<p align="center">
<sup>
Building blocks and utility extensions for discord.py bots
</sup>
<br>
</p>

***

Kasushi is an extension of the [discord.py](https://github.com/Rapptz/discord.py) library. 
It provides a number of useful features for bots, such as cache, IPC, tortoise models and more.

It is really easy to use, and requires a minimum amount of configuration.

> 1. Download kasushi on the command line using pip:
> ```bash
> pip install -U kasushi
> ```
> 2. Configure the extensions:
> ```python
> import kasushi
> # See below for settings you can pass to configure.
> await kasushi.configure(bot, {}) 
> ```
> 3. Load the extensions in your bot code before it runs:
> ```python
> await bot.load_extension('kasushi.cache')
> ```
> You're done!


## Modules and settings

Many modules are available in kasushi. You should load them in your bot, and pass settings to configure.

Depending on the module(s) you want to use, you can pass different settings to configure.

### Cache

The cache module allows for connecting to a [memcached](https://memcached.org/) server.
It can be used to store cached data between reboots of the bot, like cooldowns and user data.

#### Usage

Once installed and loaded, the cache class is made available in `bot.cache`.
```python
await bot.cache.set("coins", 0)
await bot.cache.set("coins", 10)
await bot.cache.get("coins") # 10
await bot.cache.delete("coins")
await bot.cache.get("coins", default=5) # 5
```

#### Configuration example

You can pass the following dictionary to configure:

```python
{
    "cache": {
        "server_ip": "127.0.0.1",
        "server_port": 11211,
    }
}
```