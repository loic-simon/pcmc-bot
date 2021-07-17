"""pcmc-bot / Commandes et autres fonctionnalités

Chaque module de ``pcmc.features`` implémente une fonctionnalité
spécifique des PCMCBots. La majorité implémentent un *Cog*
(:class:`discord.ext.commands.Cog`) contenant une ou plusieurs
commandes Discord, mais peuvent aussi définir des fonctions pour
un usage public.

.. note ::

    Les Cogs et leurs commandes peuvent être vus en envoyant ``!help``
    à un PCMCBot fonctionnel (en possédant le rôles :attr:`.config.Role.admin`)

"""

import os

dir = os.path.dirname(os.path.realpath(__file__))

__all__ = []
for file in os.listdir(dir):
    if not file.endswith(".py"):
        # Not a Python file
        continue

    name = file[:-3]
    if name.startswith("_"):
        # Private / magic module
        continue

    # Public submodule: add to __all__
    __all__.append(name)
