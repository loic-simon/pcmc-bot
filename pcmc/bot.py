"""pcmc-bot / PCMCBot

Classe principale

"""

import logging
import sys
import time
import traceback

import discord
from discord.ext import commands

from pcmc import __version__, config, bdd
from pcmc.bdd import *
from pcmc.blocs import env, tools, one_command, ready_check, server
from pcmc.features import *        # Tous les sous-modules


#: str: Description par défaut du bot
default_descr = "PCMC-bot – Gestion et communication avec le serveur Minecraft"


async def _check_and_prepare_objects(bot):
    errors = []

    def prepare_attributes(rc_class, discord_type, converter):
        """Rend prêt les attributs d'une classe ReadyCheck"""
        for attr in rc_class:
            raw = rc_class.get_raw(attr)
            # Si déjà prêt, on actualise quand même (reconnexion)
            name = raw.name if isinstance(raw, discord_type) else raw
            try:
                ready = converter(name)
            except ValueError:
                qualname = f"config.{rc_class.__name__}.{attr}"
                errors.append(f"{discord_type.__name__} {qualname} = "
                              f"\"{name}\" non trouvé !")
            else:
                setattr(rc_class, attr, ready)

    prepare_attributes(config.Role, discord.Role, tools.role)
    prepare_attributes(config.Channel, discord.TextChannel, tools.channel)
    prepare_attributes(config.Emoji, discord.Emoji, tools.emoji)

    if len(errors) > config._missing_objects:
        # Nouvelles erreurs
        msg = (f"PCMCBot.on_ready: {len(errors)} errors:\n - "
               + "\n - ".join(errors))
        logging.error(msg)

        try:
            atadmin = config.Role.admin.mention
        except ready_check.NotReadyError:
            atadmin = "@everyone"

        try:
            await tools.log(msg, code=True, prefixe=f"{atadmin} ERREURS :")
        except ready_check.NotReadyError:
            config.Channel.logs = config.guild.text_channels[0]
            msg += "\n-- Routing logs to this channel."
            await tools.log(msg, code=True, prefixe=f"{atadmin} ERREURS :")

    elif len(errors) < config._missing_objects:
        if errors:
            # Erreurs résolues, il en reste
            msg = f"{len(errors)} errors:\n - " + "\n - ".join(errors)
            logging.error(msg)
            await tools.log(msg, code=True, prefixe=f"Erreurs restantes :")
        else:
            # Toutes erreurs résolues
            await tools.log("Configuration rôles/chans/emojis OK.")

    config._missing_objects = len(errors)


# ---- Réactions aux différents évènements

# Au démarrage du bot
async def _on_ready(bot):
    if config.is_ready:
        await tools.log("[`on_ready` called but bot already ready, ignored]")
        return

    config.loop = bot.loop          # Enregistrement loop

    guild = bot.get_guild(bot.GUILD_ID)
    if not guild:
        raise RuntimeError(f"on_ready : Serveur d'ID {bot.GUILD_ID} "
                           "(``PCMC_SERVER_ID``) introuvable")

    print(f"      Connected to '{guild.name}'! "
          f"({len(guild.channels)} channels, {len(guild.members)} members)")

    if config.output_liveness:
        bot.i_am_alive()            # Start liveness regular output

    print("[2/3] Initialization (bot.on_ready)...")

    # Préparations des objects globaux
    config.guild = guild
    await bot.check_and_prepare_objects()

    bot.update_connection()
    await tools.log("Just rebooted!")

    # # Tâches planifiées
    # taches = bdd.Tache.query.all()
    # for tache in taches:
    #     # Si action manquée, l'exécute immédiatement, sinon l'enregistre
    #     tache.register()
    #
    # if taches:
    #     await tools.log(f"{len(taches)} tâches planifiées récupérées "
    #                     "en base et reprogrammées.")

    config.is_ready = True
    print("      Initialization complete.")
    print("\nListening for events.")


# À l'arrivée d'un membre sur le serveur
# async def _on_member_join(bot, member):
#     if member.guild != config.guild:        # Mauvais serveur
#         return

    # await tools.log(f"Arrivée de {member.name}#{member.discriminator} "
    #                 "sur le serveur")
    # await inscription.main(member)


# Au départ d'un membre du serveur
# async def _on_member_remove(bot, member):
#     if member.guild != config.guild:        # Mauvais serveur
#         return

    # await tools.log(
    #     f"{tools.mention_admin(member)} ALERTE : départ du serveur de "
    #     f"{member.display_name} ({member.name}#{member.discriminator}) !")


# À chaque message
async def _on_message(bot, message):
    if message.author == bot.user:          # Pas de boucles infinies
        return

    if not message.guild:                   # Message privé
        # await message.channel.send(
        #     "Je n'accepte pas les messages privés, désolé !"
        # )
        return

    if message.guild != config.guild:       # Mauvais serveur
        return

    # if (not message.webhook_id              # Pas un webhook
    #     and message.author.top_role == config.Role.everyone):
    #     # Pas de rôle affecté : le bot te calcule même pas
    #     return

    if message.content.startswith(bot.command_prefix + " "):
        message.content = bot.command_prefix + message.content[2:]
    elif message.content.startswith(bot.command_prefix * 2):
        message.content = bot.command_prefix*2 + " " + message.content[2:]

    # On trigger toutes les commandes
    # (ne PAS remplacer par bot.process_commands(message), en théorie
    # c'est la même chose mais ça détecte pas les webhooks...)
    ctx = await bot.get_context(message)
    await bot.invoke(ctx)

    if (not message.content.startswith(bot.command_prefix)):
        # Conditions d'IA respectées (voir doc) : on trigger
        if not config.online:
            return

        await inform.new_message(message)


# Au changement d'état vocal d'un membre
async def _on_voice_state_update(bot, member, before, after):
    if member == bot.user:              # Pas de boucles infinies
        return

    if not before.channel and after.channel:
        # Connexion
        await inform.voice_connect(member, after.channel)

    elif before.channel and not after.channel:
        # Déconnexion
        await inform.voice_disconnect(member, before.channel)


# À chaque réaction ajoutée
# async def _on_raw_reaction_add(bot, payload):
#     reactor = payload.member
#     if reactor == bot.user:                         # Boucle infinie
#         return
#
#     if payload.guild_id != config.guild.id:         # Mauvais serveur
#         return


# ---- Gestion des erreurs

def _showexc(exc):
    return f"{type(exc).__name__}: {exc}"


# Gestion des erreurs dans les commandes
async def _on_command_error(bot, ctx, exc):
    if ctx.guild != config.guild:               # Mauvais serveur
        return

    if isinstance(exc, commands.CommandInvokeError):
        if isinstance(exc.original, tools.CommandExit):     # STOP envoyé
            await ctx.send(str(exc.original) or "Mission aborted.")
            return

        # if isinstance(exc.original,                         # Erreur BDD
        #               (bdd.SQLAlchemyError, bdd.DriverOperationalError)):
        #     try:
        #         config.session.rollback()           # On rollback la session
        #         await tools.log("Rollback session")
        #     except ready_check.NotReadyError:
        #         pass

        # Dans tous les cas (sauf STOP), si erreur à l'exécution
        prefixe = ("Oups ! Un problème est survenu à l'exécution de "
                   "la commande  :grimacing: :")

        if ctx.message.webhook_id or ctx.author.top_role >= config.Role.admin:
            # admin / webhook : affiche le traceback complet
            e = traceback.format_exception(type(exc.original), exc.original,
                                           exc.original.__traceback__)
            await tools.send_code_blocs(ctx, "".join(e), prefixe=prefixe)
        else:
            # Pas admin : exception seulement
            await ctx.send(f"{prefixe}\n{tools.mention_admin(ctx)} ALED – "
                           + tools.ital(_showexc(exc.original)))

    elif isinstance(exc, commands.CommandNotFound):
        await ctx.send(
            f"Hum, je ne connais pas cette commande  :thinking:\n"
            f"Utilise {tools.code('!help')} pour voir la liste des commandes."
        )

    elif isinstance(exc, commands.DisabledCommand):
        await ctx.send("Cette commande est désactivée. Pas de chance !")

    elif isinstance(exc, (commands.ConversionError, commands.UserInputError)):
        await ctx.send(
            f"Hmm, ce n'est pas comme ça qu'on utilise cette commande ! "
            f"({tools.code(_showexc(exc))})\n*Tape "
            f"`!help {ctx.invoked_with}` pour plus d'informations.*"
        )

    elif isinstance(exc, one_command.AlreadyInCommand):
        await ctx.send(
            f"Impossible d'utiliser une commande pendant "
            "un processus ! (vote...)\n"
            f"Envoie {tools.code(config.stop_keywords[0])} "
            "pour arrêter le processus."
        )

    elif isinstance(exc, commands.CheckFailure):
        # Autre check non vérifié
        await ctx.send(
            f"Tiens, il semblerait que cette commande ne puisse "
            f"pas être exécutée ! {tools.mention_admin(ctx)} ?\n"
            f"({tools.ital(_showexc(exc))})")

    else:
        await ctx.send(
            f"Oups ! Une erreur inattendue est survenue  :grimacing:\n"
            f"{tools.mention_admin(ctx)} ALED – {tools.ital(_showexc(exc))}"
        )


# Erreurs non gérées par le code précédent (hors cadre d'une commande)
async def _on_error(bot, event, *args, **kwargs):
    etype, exc, tb = sys.exc_info()     # Exception ayant causé l'appel

    # if isinstance(exc, (bdd.SQLAlchemyError,            # Erreur SQL
    #                     bdd.DriverOperationalError)):
    #     try:
    #         config.session.rollback()       # On rollback la session
    #         await tools.log("Rollback session")
    #     except ready_check.NotReadyError:
    #         pass

    await tools.log(
        traceback.format_exc(),
        code=True,
        prefixe=f"{config.Role.admin.mention} ALED : Exception Python !"
    )

    # On remonte l'exception à Python (pour log, ne casse pas la loop)
    raise


# ---- Définition classe principale

class PCMCBot(commands.Bot):
    """Bot Discord pour communication avec le serveur PC Minecraft.

    Classe fille de :class:`discord.ext.commands.Bot`, implémentant les
    commandes et fonctionnalités de PCMC.

    Args:
        command_prefix (str): passé à :class:`discord.ext.commands.Bot`
        case_insensitive (bool): passé à
            :class:`discord.ext.commands.Bot`
        description (str): idem, défaut \:
            :attr:`pcmc.bot.default_descr`
        intents (discord.Intents): idem, défaut \:
            :meth:`~discord.Intents.all()`. *Certaines commandes et
            fonctionnalités risquent de ne pas fonctionner avec une
            autre valeur.*
        member_cache_flags (discord.MemberCacheFlags): idem, défaut \:
            :meth:`~discord.MemberCacheFlags.all()`. *Certaines
            commandes et fonctionnalités risquent de ne pas fonctionner
            avec une autre valeur.*
        \*\*kwargs: autres options de :class:`~discord.ext.commands.Bot`

    Warning:
        PCMCBot n'est **pas** thread-safe : seule une instance du bot
        peut tourner en parallèle dans un interpréteur.

        (Ceci est du aux objets de :mod:`.config`, contenant directement
        le bot, le serveur Discord, le contrôle du server... ;
        cette limitation résulte d'une orientation volontaire pour simplifier
        et optimiser la manipulation des objects et fonctions).

    Attributes:
        bot (int): L'ID du serveur sur lequel tourne le bot (normalement
            toujours :attr:`config.guild` ``.id``).  Vaut ``None`` avant
            l'appel à :meth:`run`, puis la valeur de la variable
            d'environnement ``PCMC_SERVER_ID``.
        in_command (list[int]): IDs des salons dans lequels une
            commande est en cours d'exécution.
        old_activity (Optionnal[discord.BaseActivity]): La dernière
            activité connue du bot.

    """
    def __init__(self, command_prefix="!", case_insensitive=True,
                 description=None, intents=None, member_cache_flags=None,
                 **kwargs):
        """Initialize self"""
        # Paramètres par défaut
        if description is None:
            description = default_descr
        if intents is None:
            intents = discord.Intents.all()
        if member_cache_flags is None:
            member_cache_flags = discord.MemberCacheFlags.all()

        # Construction du bot Discord.py
        super().__init__(
            command_prefix=command_prefix,
            description=description,
            case_insensitive=case_insensitive,
            intents=intents,
            member_cache_flags=member_cache_flags,
            **kwargs
        )

        # Définition attribus personnalisés
        self.GUILD_ID = None
        # self.tasks = {}
        self.old_activity = None

        # Système de limitation à une commande à la fois
        self.in_command = []
        self.add_check(one_command.not_in_command)
        self.before_invoke(one_command.add_to_in_command)
        self.after_invoke(one_command.remove_from_in_command)

        self.add_cog(serveur.GestionServeur(self))
        self.add_cog(whitelist.Whitelist(self))
        # Commandes spéciales, méta-commandes...
        self.remove_command("help")
        self.add_cog(special.Special(self))

    # Réactions aux différents évènements
    async def on_ready(self):
        """Méthode appellée par Discord au démarrage du bot.

        Vérifie le serveur (appelle :meth:`check_and_prepare_objects`),
        log et actualise l'activité du bot.

        Si :attr:`config.output_liveness` vaut ``True``, lance
        :attr:`bot.i_am_alive <.PCMCBot.i_am_alive>`
        (écriture chaque minute sur un fichier disque)

        Voir :func:`discord.on_ready` pour plus d'informations.
        """
        await _on_ready(self)

    # async def on_member_join(self, member):
    #     """Méthode appellée par l'API à l'arrivée d'un nouveau membre.
    #
    #     Log et lance le processus d'inscription.
    #
    #     Ne fait rien si l'arrivée n'est pas sur le serveur
    #     :attr:`config.guild`.
    #
    #     Args:
    #         member (discord.Member): Le membre qui vient d'arriver.
    #
    #     Voir :func:`discord.on_member_join` pour plus d'informations.
    #     """
    #     await _on_member_join(self, member)
    #
    # async def on_member_remove(self, member):
    #     """Méthode appellée par l'API au départ d'un membre du serveur.
    #
    #     Log en mentionnant les admins.
    #
    #     Ne fait rien si le départ n'est pas du serveur
    #     :attr:`config.guild`.
    #
    #     Args:
    #         member (discord.Member): Le joueur qui vient de partir.
    #
    #     Voir :func:`discord.on_member_remove` pour plus d'informations.
    #     """
    #     await _on_member_remove(self, member)

    async def on_message(self, message):
        """Méthode appellée par l'API à la réception d'un message.

        Transmet le message sur le serveur Minecraft
        (voir :func:`features.inform.new_message`).

        Ne fait rien si le message n'est pas sur le serveur
        :attr:`config.guild` ou si il est envoyé par le bot lui-même.

        Args:
            member (discord.Member): Le joueur qui vient d'arriver.

        Voir :func:`discord.on_message` pour plus d'informations.
        """
        await _on_message(self, message)

    async def on_voice_state_update(self, member, before, after):
        """Méthode appellée par l'API au changement d'un statut vocal.

        En cas de connexion / déconnexion d'un salon vocal,transmet
        l'information sur le serveur Minecraft (voir
        :func:`features.inform.voice_connect` et
        :func:`features.inform.voice_disconnect`).

        Args:
            member (discord.Member): Le membre dont le statut vient de
                changer.
            before (discord.VoiceState): L'ancien statut vocal.
            after (discord.VoiceState): Le nouveau statut vocal.

        Voir :func:`discord.on_voice_state_update` pour plus d'informations.
        """
        await _on_voice_state_update(self, member, before, after)

    # async def on_raw_reaction_add(self, payload):
    #     """Méthode appellée par l'API à l'ajout d'une réaction.
    #
    #     Appelle la fonction adéquate si le membre est un joueur
    #     inscrit, est sur un chan de conversation bot et a cliqué sur
    #     :attr:`config.Emoji.bucher`, :attr:`~config.Emoji.maire`,
    #     :attr:`~config.Emoji.lune` ou :attr:`~config.Emoji.action`.
    #
    #     Ne fait rien si la réaction n'est pas sur le serveur
    #     :attr:`config.guild`.
    #
    #     Args:
    #         payload (discord.RawReactionActionEvent): Paramètre
    #             limité (car le message n'est pas forcément dans le
    #             cache du bot, par exemple si il a été reboot depuis).
    #
    #     Quelques attributs utiles :
    #       - ``payload.member`` (:class:`discord.Member`) : Membre
    #         ayant posé la réaction
    #       - ``payload.emoji`` (:class:`discord.PartialEmoji`) :
    #         PartialEmoji envoyé
    #       - ``payload.message_id`` (:class:`int`) : ID du message réacté
    #
    #     Voir :func:`discord.on_raw_reaction_add` pour plus
    #     d'informations.
    #     """
    #     await _on_raw_reaction_add(self, payload)

    # Gestion des erreurs
    async def on_command_error(self, ctx, exc):
        """Méthode appellée par l'API à un exception dans une commande.

        Analyse l'erreur survenue et informe le joueur de manière
        adéquate en fonction, en mentionnant les admins si besoin.

        Ne fait rien si l'exception n'a pas eu lieu sur le serveur
        :attr:`config.guild`.

        Args:
            ctx (discord.ext.commands.Context): Contexte dans lequel
                l'exception a été levée
            exc (discord.ext.commands.CommandError): Exception levée

        Voir :func:`discord.on_command_error` pour plus d'informations.
        """
        await _on_command_error(self, ctx, exc)

    async def on_error(self, event, *args, **kwargs):
        """Méthode appellée par l'API à une exception hors commande.

        Log en mentionnant les admins. Cette méthode permet de gérer les
        exceptions sans briser la loop du bot (i.e. il reste en ligne).

        Args:
            event (str): Nom de l'évènement ayant généré une erreur
                (``"member_join"``, ``"message"``...)
            *args, \**kwargs: Arguments passés à la fonction traitant
                l'évènement : ``member``, ``message``...

        Voir :func:`discord.on_error` pour plus d'informations.
        """
        await _on_error(self, event, *args, **kwargs)

    # Checks en temps réels des modifs des objets nécessaires au bot
    async def check_and_prepare_objects(self):
        """Vérifie et prépare les objets Discord nécessaires au bot.

        Remplit :class:`.config.Role`, :class:`.config.Channel`,
        :class:`.config.Emoji`, :attr:`config.private_chan_category_name`,
        :attr:`config.boudoirs_category_name` et :attr:`config.webhook`
        avec les objets Discord correspondants, et avertit les admins en
        cas d'éléments manquants.
        """
        await _check_and_prepare_objects(self)

    async def on_guild_channel_delete(self, channel):
        if channel.guild == config.guild:
            await self.check_and_prepare_objects()

    async def on_guild_channel_update(self, before, after):
        if before.guild == config.guild and config._missing_objects:
            await self.check_and_prepare_objects()

    async def on_guild_channel_create(self, channel):
        if channel.guild == config.guild and config._missing_objects:
            await self.check_and_prepare_objects()

    async def on_guild_role_delete(self, role):
        if role.guild == config.guild:
            await self.check_and_prepare_objects()

    async def on_guild_role_update(self, before, after):
        if before.guild == config.guild and config._missing_objects:
            await self.check_and_prepare_objects()

    async def on_guild_role_create(self, role):
        if role.guild == config.guild and config._missing_objects:
            await self.check_and_prepare_objects()

    async def on_guild_emojis_update(self, guild, before, after):
        if guild == config.guild:
            await self.check_and_prepare_objects()

    async def on_webhooks_update(self, channel):
        if channel == config.Channel.logs:
            await self.check_and_prepare_objects()

    # Système de vérification de vie
    def i_am_alive(self, filename="alive.log"):
        """Témoigne que le bot est en vie et non bloqué.

        Exporte le temps actuel (UTC) et planifie un nouvel appel
        dans 60s. Ce processus n'est lancé que si
        :attr:`config.output_liveness` est mis à ``True``.

        Args:
            filename (:class:`str`): fichier où exporter le temps
                actuel (écrase le contenu).
        """
        with open(filename, "w") as f:
            f.write(str(time.time()))
        self.loop.call_later(60, self.i_am_alive, filename)

    async def _update_connection(self):
        # self.loop.call_later(60, self.update_connection)

        online = await server.connect()
        if online:
            si = await serveur.get_online_players()
            players = si.n_players
            s = "" if players == 1 else "s"
            activity = discord.Game(f"Minecraft 🟢 {players} joueur{s}")
            status = discord.Status.online
        else:
            activity = discord.Game("Minecraft 🔴 OFFLINE")
            status = discord.Status.dnd

        if self.old_activity != activity:
            await tools.log(f"Présence mise à jour : {activity}")
            await self.change_presence(activity=activity, status=status)
            self.old_activity = activity


    def update_connection(self):
        """Met à jour l'activité du bot selon le statut du serveur.

        Cette méthode est appelée toutes les minutes pour actualiser
        le nombre de joueurs sur le serveur.
        """
        self.loop.create_task(self._update_connection())

    async def close(self):
        server.disconnect()
        await super().close()

    # Lancement du bot
    def run(self, **kwargs):
        """Prépare puis lance le bot (bloquant).

        Récupère les informations de connexion, établit la connexion
        à la base de données puis lance le bot.

        Args:
            \**kwargs: Passés à :meth:`discord.ext.commands.Bot.run`.
        """
        print(f"--- PCMCBot v{__version__} ---")

        # Récupération du token du bot et de l'ID du serveur
        PCMC_DISCORD_TOKEN = env.load("PCMC_DISCORD_TOKEN")
        self.GUILD_ID = int(env.load("PCMC_SERVER_ID"))

        # Connexion BDD
        print("[1/3] Connecting to database...")
        bdd.connect()
        url = config.engine.url
        print(f"      Connected to {url.host}/{url.database}!")

        # Enregistrement
        config.bot = self

        # Lancement du bot (bloquant)
        print("[2/3] Connecting to Discord...")
        super().run(PCMC_DISCORD_TOKEN, **kwargs)

        print("\nDisconnected.")
