# pcmc-bot

<!-- [![PyPI](https://img.shields.io/pypi/v/pcmc-bot)](https://pypi.org/project/pcmc-bot)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pcmc-bot)](https://pypi.org/project/pcmc-bot)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/pcmc-bot)](https://pypi.org/project/pcmc-bot)
[![Read the Docs](https://img.shields.io/readthedocs/pcmc-bot)](https://pcmc-bot.readthedocs.io) -->

Discord bot for managing and communicating with PC Minecraft server.

*Please not that this project's source code (comments, docstrings) is written
exclusively in French. The bot itself uses only French language; no
internationalization is available at this time.*


## What's New in PCMC-Bot

Only major features are reported here; see [`CHANGELOG.md`](CHANGELOG.md)
or in [the doc](https://pcmc-bot.readthedocs.io/fr/2.1.4/changelog.html) for
details.

### 1.0

* Communication with Minecraft server (status, commands)...
* In-game transmission of Discord messages & voice (dis)connections;


## Installation

<!-- Use the package manager [pip](https://pypi.org/project/pip) to install pcmc-bot:
```bash
pip install pcmc-bot
``` -->
This project is (for now) meant for private usage and therefore not published
on PyPI. Clone this repository to use it:
```bash
git clone https://github.com.loic-simon/pcmc-bot.git
```

We strongly recommand to install this package in a dedicated virtualenv
(`python3 -m venv <yourfolder>`).


### Dependencies

* Python 3.8+
* Packages: see [`requirements.txt`](requirements.txt)



## Configuration

To run correctly, the bot needs to be connected to several external services,
each needing more or less sensitive tokens, stocked as environments variables.
We support and encourage the use of
[`python-dotenv`](https://pypi.org/project/python-dotenv/) to read them from
a `.env` file, but you may prefer exporting them as environment variables.

All necessary variables, prefixed by `PCMC_`, are listed in
[`model.env`](model.env).


<!-- ### Configuration Assistant Tool

We provide a command-line assistant tool to help you set up every services and
generate the `.env` file (which you can later `source` and delete if you wish).

Run it simply with:
```bash
python -m pcmc
```

This tool also creates a `start_bot.py` file containing the minimal code
needed to run the bot (see *Usage* section below). -->


<!-- ### Manual configuration

You may prefer to manually write your environment variables, or just check
instructions regarding a specific one: they can be found in
[`CONFIGURE.md`](CONFIGURE.md).

**Warning**: the Configuration Assistant Tool checks every variable by
running specific tests, which is not the case for manual configuration,
so be sure of what you do! -->



## Usage

This package's external API consists essentially in a
[`discord.ext.commands.Bot`](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#bot)
subclass, **`PCMCBot`**, which implements every features needed.

The minimal code needed to run the bot in a configured folder  is:
```py
from pcmc import PCMCBot

bot = PCMCBot()
bot.run()
```

### Bot usage

Once the bot connected to your Discord server, send `!help` to see every
available commands (note: some commands are only visible by specific roles;
grant yourself the "admin" role to see everything.) \
Use `!help command` to get more information about a command.

<!-- For precisions relative to non-command features (such as "IA" reactions to
messages), look at the corresponding
[documentation](https://pcmc-bot.readthedocs.io/) section. -->


### Customization

Since `PCMCBot` is a subclass of
[`discord.ext.commands.Bot`](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#bot),
you can use every arguments and methods it supports or subclass it to override
existing behavior.

We also provide a direct way to customize some parameters of the game and
of the Discord server through [`config`](pcmc/config.py) module:
roles/channels/emoji names, date of season beginning, inscription
customization... See
[the doc](https://pcmc-bot.readthedocs.io/fr/2.1.4/config.html)
for full API usage information.

See additional attributes and overriden methods on
[the doc](https://pcmc-bot.readthedocs.io/) (mostly in French)

Some useful examples:

#### Change command prefix
```py
from pcmc import PCMCBot

bot = PCMCBot(command_prefix="?")
bot.run()
```

#### Customize some config options
```py
from pcmc import PCMCBot, config

config.Role.admin = "BOSS"

bot = PCMCBot()
bot.run()
```


#### Delete a command or alias
```py
from pcmc import PCMCBot

bot = PCMCBot()
bot.remove_command("command_name")
bot.run()
```

#### Add a command or change the behavior of a command
```py
from discord.ext import commands
from pcmc import PCMCBot

@commands.command()
async def mycommand(ctx, ...):
    ...

bot = PCMCBot()
bot.remove_command("mycommand")     # If replacing an existing command
bot.add_command(mycommand)
bot.run()
```

#### Enhance or replace the reaction to a Discord event
```py
from pcmc import PCMCBot

async def say_hello(bot, member):
    await member.send("Hey!")

class MyBot(PCMCBot):
    """Your customized bot class"""
    async def on_member_join(self, member):
        await say_hello(self, member)
        super().on_member_join(member)      # Invoke the original reaction

bot = MyBot()
bot.run()
```

See [discord.py documentation](https://discordpy.readthedocs.io) for more
ideas.



## Contributing

Community contributions are not welcome for now. Get in touch with the authors
(see below) for any question or suggestion about this project.



## License
This work is shared under [the MIT license](LICENSE).

© 2020 Loïc Simon – GRIs – ESPCI Paris - PSL.

Reach me on Discord:
[LaCarpe#1674](https://discordapp.com/users/264482202966818825) or by mail:
[loic.simon@espci.org](mailto:loic.simon@espci.org)
