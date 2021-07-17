"""Loup-Garou de la Rez (pcmc-bot)

Discord bot for organizing boisterous Werewolf RP games ESPCI-style.

See github.com/loic-simon/pcmc-bot for informations.
"""

__title__ = "pcmc-bot"
__author__ = "Loïc Simon"
__license__ = "MIT"
__copyright__ = ("Copyright 2021 Loïc Simon - "
                 "GRIs – ESPCI Paris - PSL")
__version__ = "1.0.0"
__all__ = ["PCMCBot"]


from pcmc import bot
PCMCBot = bot.PCMCBot                # Accès direct à pcmc.PCMCBot
