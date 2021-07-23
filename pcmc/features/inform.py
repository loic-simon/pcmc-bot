"""pcmc-bot / features / Information des joueurs

Fonctions d'information en jeu

"""

import json

import discord
from discord.ext import commands

from pcmc import config
from pcmc.blocs import tools, server


async def new_message(message):
    """Transmet un message Discord dans Minecraft

    Args:
        message (discord.Message): message à transmettre

    Utilise ``/tellraw`` pour afficher du texte coloré et cliquable.
    """
    cont = tools.escape_mentions(message.content)
    texts = [
        {
            "text": "[Discord ",
            "color": "gray",
        },
        {
            "text": f"#{message.channel.name}",
            "color": "aqua",
            "clickEvent": {"action": "open_url",
                           "value": message.jump_url},
            "hoverEvent": {"action": "show_text",
                           "contents": "Voir le message"},
        },
        {
            "text": "] ",
            "color": "gray",
        },
        {
            "text": f"<{message.author.display_name}> {cont}",
            "color": "white",
        },
    ]
    for embed in message.embeds:
        texts.append({
            "text": " [embed]",
            "color": "light_purple",
            "italic": True,
            "clickEvent": {"action": "open_url",
                           "value": message.jump_url},
            "hoverEvent": {"action": "show_text",
                           "contents": "Voir le message"},
        })
    for att in message.attachments:
        texts.append({
            "text": f" [{att.filename}]",
            "color": "gold",
            "italic": True,
            "clickEvent": {"action": "open_url",
                           "value": att.url},
            "hoverEvent": {"action": "show_text",
                           "contents": "Voir le fichier"},
        })
    await server.command(f"tellraw @a " + json.dumps(texts))


async def voice_connect(member, channel):
    """Informe d'une connexion à un salon vocal Discord dans Minecraft

    Args:
        member (discord.Member): le membre qui a rejoint le salon
        channel (discord.VoiceChannel): le salon rejoint

    Utilise ``/tellraw`` pour afficher du texte coloré et cliquable.
    """
    texts = [
        {
            "text": "[Discord ",
            "color": "gray",
        },
        {
            "text": f"\u266c {channel.name}",
            "color": "aqua",
        },
        {
            "text": "] ",
            "color": "gray",
        },
        {
            "text": f"{member.display_name} a rejoint le vocal !",
            "color": "white",
            "italic": True,
        },
    ]
    await server.command(f"tellraw @a " + json.dumps(texts))


async def voice_disconnect(member, channel):
    """Informe d'une déconnexion d'un salon vocal Discord dans Minecraft

    Args:
        member (discord.Member): le membre qui a quitté le salon
        channel (discord.VoiceChannel): le salon quitté

    Utilise ``/tellraw`` pour afficher du texte coloré et cliquable.
    """
    texts = [
        {
            "text": "[Discord ",
            "color": "gray",
        },
        {
            "text": f"\u266c {channel.name}",
            "color": "aqua",
        },
        {
            "text": "] ",
            "color": "gray",
        },
        {
            "text": f"{member.display_name} a quitté le vocal.",
            "color": "white",
            "italic": True,
        },
    ]
    await server.command(f"tellraw @a " + json.dumps(texts))
