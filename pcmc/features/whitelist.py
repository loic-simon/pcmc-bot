"""pcmc-bot / features / Gestion de la whitelist

Autorisations d'accès sur le serveur

"""

import asyncio
import datetime
import re

import discord
from discord.ext import commands

from pcmc import config
from pcmc.bdd import Joueur
from pcmc.blocs import tools, server
from pcmc.features import serveur


async def _add_to_whitelist(pseudo):
    await server.command(f"whitelist add {pseudo}")

async def _remove_from_whitelist(pseudo):
    await server.command(f"whitelist remove {pseudo}")

async def _create_custom_team(joueur):
    await server.command(f"team add {joueur.team}")
    await server.command(f"team join {joueur.team} {joueur.pseudo}")

async def _update_custom_team(joueur):
    await server.command(f"team modify {joueur.team} suffix "
                       f"\" – {joueur.nom}\"")

async def _remove_custom_team(joueur):
    await server.command(f"team remove {joueur.team}")


class Whitelist(commands.Cog):
    """Commandes de communication directe avec le serveur"""

    @commands.command(aliases=["wl"])
    async def whitelist(self, ctx):
        """Lie votre compte Discord à votre pseudo et le whitelist

        Pose quelques questions en MP à cet effet.
        """
        member = ctx.author
        chan = member.dm_channel

        try:
            joueur = Joueur.from_member(member)
        except ValueError:      # Joueur pas encore inscrit en base
            new = True
        else:                   # Joueur dans la bdd = déjà inscrit
            new = False

        if chan is None:
            chan = await member.create_dm()

        # Récupération nom et renommages
        if new:
            await chan.send(
                f"Bienvenue {member.mention} ! Je suis le bot qui gère le "
                "serveur PC Minecraft, je vais juste te whitelist au serveur "
                "et ensuite tu ne devrais plus avoir affaire à moi."
            )

            await tools.sleep(chan, 5)

            await chan.send(
                "Du coup, à toutes fins utiles, je te rappelle que ce serveur "
                "est **réservé aux élèves de l'ESPCI** et apparentés (ce qui "
                "peut aller assez loin, on est pas sectaires). Vu que le "
                "serveur est potentiellement trouvable par n'importe qui, "
                "je vais te poser **une énigme très simple** :"
            )

            await tools.sleep(chan, 5)

            in_message = tools.ital(
                "Partout où l'on va, que nous demandent les gens ?"
            )
            rep_message = "Bah non. Réessaie sans fioritures ?\n\n" + in_message
            reps = ["qui l'on est", "qui on est", "quiii l'on eeest"]
            def qoe_cond(mess):
                return (mess.channel == chan and mess.author != config.bot.user
                        and mess.content and mess.content.lower() in reps)
            await tools.boucle_message(chan, in_message, qoe_cond, rep_message)

            await chan.send(
                "D'OÙÙÙ L'ON VIEEENT...\n\nPardon. Bon parfait, il me faudrait "
                "maintenant ton petit nom, que les gens sachent te reconnaître "
                "(ou ton pseudo, si tu estimes qu'il est suffisament connu) :"
            )

        else:
            await chan.send(
                f"Bonsoir {member.mention} ! C'est pour un renommage ? Un "
                "changement de pseudo ? Bon dans le doute, on va faire les "
                "deux..."
            )


        def check_chan(m):
            # Message de l'utilisateur dans son channel perso
            return m.channel == chan and m.author != config.bot.user

        ok = False
        while not ok:
            await chan.send("Quel est ton nom, donc ?")
            mess = await tools.wait_for_message(check=check_chan, chan=chan)
            nom = mess.content

            message = await chan.send(
                f"Tu me dis donc t'appeller {tools.bold(nom)}. "
                "C'est bon pour toi ? Pas d'erreur, pas de troll ?"
            )
            ok = await tools.yes_no(message)

        if member.top_role < config.Role.admin:
            # Renommage joueur (ne peut pas renommer les admins)
            await member.edit(nick=nom)

        await chan.send(
            "Parfait ! Je t'ai renommé(e) pour que tout le monde te "
            "reconnaisse."
        )


        ok = False
        while not ok:
            await chan.send(
                "Allez, c'est quasi fini, le plus important : "
                "**quel est ton pseudo Minecraft ?**\n\n"
                "*Pseudo exact, attention aux majuscules/minuscules ; "
                "le serveur n'accepte pas les comptes crackés.*"
            )
            mess = await tools.wait_for_message(check=check_chan, chan=chan)
            pseudo = mess.content

            message = await chan.send(
                f"Ton pseudo est donc {tools.bold(pseudo)} ?\n"
                "C'est validé ?"
            )
            ok = await tools.yes_no(message)


        await chan.send("Parfait, je t'inscris en base !")

        async with chan.typing():
            # Enregistrement en base

            if new:
                joueur = Joueur(
                    discord_id=member.id,
                    nom=member.display_name,
                    pseudo=pseudo,
                    inscription=datetime.datetime.now(),
                )
                joueur.add()

            else:
                old_nom = joueur.nom
                old_pseudo = joueur.pseudo
                joueur.nom = member.display_name
                joueur.pseudo = pseudo
                joueur.update()

        await chan.send("Et maintenant, sur la whitelist...")

        async with chan.typing():
            # Ajout à la whitelist

            if new:
                await _add_to_whitelist(joueur.pseudo)
            elif joueur.pseudo != old_pseudo:
                await _remove_from_whitelist(old_pseudo)
                await _remove_custom_team(joueur)
                await _add_to_whitelist(joueur.pseudo)
                await _create_custom_team(joueur)

            if new:
                await _create_custom_team(joueur)
                await _update_custom_team(joueur)
            elif joueur.nom != old_nom:
                await _update_custom_team(joueur)


            # Grant accès aux channels joueurs et information
            if new:
                await member.add_roles(config.Role.joueurs)


        # Conseiller d'ACTIVER TOUTES LES NOTIFS du chan
        # (et mentions only pour le reste, en activant @everyone)
        await chan.send(
            "C'est tout bon (normalement ) ! Si tu veux modifier ton nom "
            "ou ton pseudo, ré-utilise simplement ``!whitelist`` depuis le "
            "serveur."
        )

        # Log
        if new:
            await tools.log(
                f"Inscription de {member.name}#{member.discriminator} "
                f"réussie\n - Nom : {nom}\n - Pseudo : {pseudo}\n"
            )
        else:
            await tools.log(
                f"Changement de nom/pseudo de {member.name}"
                f"#{member.discriminator}\n - Nom : {nom}\n - Pseudo : {pseudo}\n"
            )
