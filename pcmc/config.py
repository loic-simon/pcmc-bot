"""pcmc-bot / Variables globales

Personalisation de différents paramètres et accès global

"""

import discord

from pcmc.blocs import ready_check


#: bool: Si ``True``, le bot appellera :meth:`.PCMCBot.i_am_alive` toutes
#: les 60 secondes. Ce n'est pas activé par défaut.
output_liveness = False


#: list[str]: Mots-clés (en minuscule) utilisables (quelque soit la casse)
#: pour arrêter une commande en cours d'exécution.
stop_keywords = ["stop", "!stop"]


#: bool: Indique si le bot est prêt (:meth:`.PCMCBot.on_ready` appelé)
#: N'est pas concu pour être changé manuellement.
is_ready = False


class Role(ready_check.ReadyCheck, check_type=discord.Role):
    """Rôles Discord nécessaires au fonctionnement du bot

    Cette classe dérive de :class:`.ready_check.ReadyCheck` :
    accéder aux attributs ci-dessous avant que le bot ne soit connecté
    au serveur lève une :exc:`~.ready_check.NotReadyError`.

    Plus précisément, :meth:`.PCMCBot.on_ready` remplace le nom du rôle
    par l'objet :class:`discord.Role` correspondant : si les noms des
    rôles sur Discord ont été modifiés, indiquer leur nom ici
    (``pcmc.config.Role.x = "nouveau nom"``) avant de lancer le bot,
    sans quoi :meth:`.PCMCBot.on_ready` lèvera une erreur.

    **Ne pas instancier cette classe.**

    Rôles utilisés (dans l'ordre hiérarchique conseillé) :

    Attributes:
        admin: Responsable du serveur (peut exécuter des commandes OP).
            Nom par défaut : "admin".
        en_jeu: Joueur actuellement connecté sur le serveur.
            Nom par défaut : "En jeu".
        joueurs: Joueur whitelisté sur le serveur.
            Nom par défaut : "Joueur".
        everyone: Rôle de base. Les membres dont le rôle le plus élevé
            est ce rôle (ou moins) seront ignorés par le bot.
            Nom par défaut : "@everyone" (rôle Discord de base)
    """
    admin = "admin"
    en_jeu = "En jeu"
    joueurs = "Joueurs"
    everyone = "@everyone"


class Channel(ready_check.ReadyCheck, check_type=discord.TextChannel):
    """Salons Discord nécessaires au fonctionnement du bot.

    Cette classe dérive de :class:`.ready_check.ReadyCheck` : accéder
    aux attributs ci-dessous avant que le bot ne soit connecté au
    serveur lève une :exc:`~.ready_check.NotReadyError`.

    Plus précisément, :meth:`.PCMCBot.on_ready` remplace le nom du rôle
    par l'objet :class:`discord.TextChannel` correspondant : si les noms
    des salons sur Discord ont été modifiés, indiquer leur nom ici
    (``pcmc.config.Channel.x = "nouveau nom"``) avant de lancer le bot,
    sans quoi :meth:`.PCMCBot.on_ready` lèvera une erreur.

    **Ne pas instancier cette classe.**

    Salons utilisés (dans l'ordre d'affichage conseillé) :

    Attributes:
        logs: Salon pour les messages techniques.
            Nom par défaut : "logs".
    """
    logs = "logs"


class Emoji(ready_check.ReadyCheck, check_type=discord.Emoji):
    """Emojis Discord nécessaires au fonctionnement du bot.

    Cette classe dérive de :class:`.ready_check.ReadyCheck` : accéder
    aux attributs ci-dessous avant que le bot ne soit connecté au
    serveur lève une :exc:`~.ready_check.NotReadyError`.

    Plus précisément, :meth:`.PCMCBot.on_ready` remplace le nom du rôle
    par l'objet :class:`discord.Emoji` correspondant : si les noms
    des emojis sur Discord ont été modifiés, indiquer leur nom ici
    (``pcmc.config.Emoji.x = "nouveau nom"``) avant de lancer le bot,
    sans quoi :meth:`.PCMCBot.on_ready` lèvera une erreur.

    **Ne pas instancier cette classe.**

    Emojis utilisés (noms par défaut identiques aux noms des attributs) :
    *aucun actuellement*
    """
    pass


class _ModuleGlobals(ready_check.ReadyCheck):
    """Module-level attributes with not-None ReadyCheck

    (attributes accessed by __getattr__, documented directly in config.rst)
    """
    guild = None
    bot = None
    loop = None
    engine = None
    session = None

    online = False
    mcr = None


# Variable interne, pour suivi des objets manquants (ne pas changer)
_missing_objects = 0


# Called when module attribute not found: try to look in _ModuleGlobals
def __getattr__(attr):
    try:
        return getattr(_ModuleGlobals, attr)
    except AttributeError:
        raise AttributeError(
            f"module '{__name__}' has no attribute '{attr}'"
        ) from None
