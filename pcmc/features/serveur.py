"""pcmc-bot / features / Gestion du serveur

Communication directe avec le serveur Minecraft

"""

import asyncio
import datetime
import re

import discord
from discord.ext import commands

from pcmc import config
from pcmc.bdd import Joueur
from pcmc.blocs import tools, server


async def _parse_message(raw, joueur):
    name = joueur.mc_name
    if (mtch := re.fullmatch(f"<{name}> !(.*)", raw)):
        # Message global
        await tools.send_blocs(config.Channel.server, mtch.group(1))

    elif (mtch := re.fullmatch(f"{name} left the game", raw)):
        # Déconnexion
        await tools.log(f"Déconnexion : {joueur}")
        await joueur.member.remove_roles(config.Role.en_jeu)
        joueur.en_jeu = False
        joueur.update()
        await update_connection()

    elif (mtch := re.fullmatch(f"{name} joined the game", raw)):
        # Connexion
        await tools.log(f"Connexion : {joueur}")
        await joueur.member.add_roles(config.Role.en_jeu)
        joueur.en_jeu = True
        joueur.update()
        await update_connection()


async def parse_console():
    raw = await server.get_last_messages()
    if raw:
        await tools.log(raw, code=True, prefixe="PARSING:")
    mtchs = re.finditer(
        r"[\d\d:\d\d:\d\d] [Server thread/INFO]: (.*)$", raw, re.M
    )
    for mtch in mtchs:
        for joueur in Joueur.query.all():
            if joueur.mc_name in mtch.group(1):
                await _parse_message(mtch.group(1), joueur)


async def update_connection():
    online = await server.connect()
    if online:
        si = await get_online_players()
        players = si.n_players
        s = "" if players == 1 else "s"
        activity = discord.Game(f"Minecraft 🟢 {players} joueur{s}")
        status = discord.Status.online
    else:
        activity = discord.Game("Minecraft 🔴 OFFLINE")
        status = discord.Status.dnd

    if self.old_activity != activity:
        await tools.log(f"Présence mise à jour : {activity}")
        await config.bot.change_presence(activity=activity, status=status)
        config.bot.old_activity = activity


class _ServerInfo():
    def __init__(self, players, n_players, max_players):
        self.players = players
        self.n_players = n_players
        self.max_players = max_players

async def get_online_players():
    """Récupère les informations sur les joueurs connectés au serveur.

    Exécute et parse la commande Minecraft
    [``/list uuids``](https://minecraft.fandom.com/wiki/Commands/list)

    Renvoie un proxy contenant les champs suivants :
        - ``players`` : liste des tuples ``(nom, UUID)`` des joueurs
          actuellement connectés ;
        - ``n_players`` : le nombre de joueurs actuellement connectés,
          normalement toujours égal à ``len(players)`` ;
        - ``max_players`` : le nombre maximal de joueurs acceptés
          simultanément par le serveur.
    """
    raw = await server.command("list uuids", wait=2)
    mtch = re.search(
        "There are (\d+) of a max of (\d+) players online: (.*)$", raw, re.M
    )
    players = [(mt.group(1), mt.group(2)) for pl in mtch.group(3).split(", ")
               if (mt := re.fullmatch(r"(.*) \(([0-9a-f-]{36})\)", pl))]
    return _ServerInfo(players, int(mtch.group(1)), int(mtch.group(2)))


class GestionServeur(commands.Cog):
    """Commandes de communication directe avec le serveur"""

    @commands.command(aliases=["!"])
    @tools.admins_only
    async def send(self, ctx, *, command):
        """Exécute une commande Minecraft via RCon (commande admin)

        Args:
            command: commande Minecraft à exécuter.
        """
        res = await server.command(command)
        await tools.send_code_blocs(ctx, res)


    @commands.command(aliases=["statut", "statuts"])
    async def status(self, ctx):
        """Récupère l'état du serveur

        Informe sur les joueurs connectés et le nombre de TPS du serveur.
        """
        async with ctx.typing():
            online = await server.connect()
            if online:
                info = await get_online_players()
                s = "" if info.n_players == 1 else "s"
                on_off = f"🟢 ONLINE - {info.n_players} joueur{s} en ligne"
            else:
                on_off = "🔴 OFFLINE"

        embed = discord.Embed(
            title=f"État du serveur :  {on_off}",
            # description=config.bot.description,
            color = discord.Color.green() if online else discord.Color.red()
        ).set_author(
            name="PC Minecraft",
            icon_url=config.bot.user.avatar_url,
        ).set_footer(
            text=("pcmc.bloomenetwork.fr – "
                  + datetime.datetime.now().strftime("%d/%m/%Y %H:%M")),
        )

        if online:
            s = "" if info.n_players == 1 else "s"
            embed.add_field(
                name=f"Joueur{s} connectés :          ",
                value="\n".join(pl[0] for pl in info.players),
                inline=True,
            ).add_field(
                name="TPS (idéal = 20) :",
                value="Calcul en cours... (10s)",
                inline=True,
            )

        embed.add_field(
            name="Vue de la map (s'actualise toutes les 2 heures) :",
            value=("[pcmc.bloomenetwork.fr:8000]"
                   "(http://pcmc.bloomenetwork.fr:8000)"),
            inline=False,
        # ).add_field(
        #     name="Whitelist :",
        #     value="Ping Loïc sur #général",
        #     inline=True,
        )

        mess = await ctx.send(embed=embed)

        if not online:
            return

        async with ctx.typing():
            await server.command("debug start")
            await asyncio.sleep(10)
            res = await server.command("debug stop")

        mtch = re.fullmatch("Stopped tick profiling after \d+\.\d+ seconds "
                            "and \d+ ticks \((\d+\.\d+) ticks per second\)",
                            res)
        tps = mtch.group(1)

        embed.set_field_at(1, name=embed.fields[1].name, value=tps)
        await mess.edit(embed=embed)



    @commands.command()
    @tools.admins_only
    async def reconnect(self, ctx, *, command):
        """Coupe et relance la connexion au serveur (commande admin)

        Peut être utile en cas de non-réponse du serveur.
        """
        await server.reconnect()
