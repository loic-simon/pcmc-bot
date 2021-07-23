"""pcmc-bot / blocs / Communication locale avec le serveur Minecraft

Force la communication locale : privilégier pcmc.blocs.server.

"""

import asyncio
import os

import screenutils

from pcmc import config
from pcmc.blocs import env


_LConException = screenutils.errors.ScreenNotFoundError


async def connect():
    """Ouvre la connexion au serveur PC Minecraft.

    Returns:
        ``True`` (la connexion a réussi) ou ``False`` (la connexion a échoué)

    Le *screen* Unix sur lequel tourne le serveur et le chemin d'accès
    (relatif ou abolu) aux logs actuels générés par le serveur sont lus
    par cette fonction depuis les variables d'environnement
    ``PCMC_LCON_SCREEN_NAME`` et ``PCMC_LCON_LOGFILE``.

    Si le bot est déjà connecté, retourne directement ``True``
    (sans vérifier l'état de la connexion).
    """
    if config.online:
        return True

    screen_name = env.load("PCMC_LCON_SCREEN_NAME")
    logfile = os.path.abspath(env.load("PCMC_LCON_LOGFILE"))

    if not os.path.isfile(logfile):
        raise RuntimeError(f"File '{logfile}' does not exist "
                           "(check PCMC_LCON_LOGFILE value).") from None

    config.screen = screenutils.Screen(screen_name)
    if not config.screen.exists:
        return False
    config.logs = screenutils.screen.tailf(logfile)
    config.online = True
    return True


def disconnect():
    """Ferme la connexion au serveur PC Minecraft.

    Si le bot n'est pas connecté, ne fait rien.
    """
    if not config.online:
        pass
    config.screen = None
    config.logs = None
    config.online = False


async def reconnect():
    """Ferme puis ré-ouvre la connexion au serveur PC Minecraft.

    Globalement équivalent à un appel à :func:`.disconnect` puis
    :func:`.connect`.

    Returns:
        bool: La valeur retournée par :func:`.connect`.
    """
    disconnect()
    return await connect()


async def command(cmd, wait=0.5):
    """Exécute une commande Minecraft et retourne le résultat obtenu.

    Args:
        cmd (str): la commande Minecraft a exécuter (avec ou sans ``/``)
        wait (float): le temps à attendre avant de récupérer le résultat

    Returns:
        Optionnal[str]: La réponse du serveur, le cas échéant.

    Raises:
        screenutils.errors.ScreenNotFoundError: Il y a eu un problème de
            communication avec le serveur.

    En cas d'erreur de communication, cette fonction tente d'abord de
    se reconnecter au serveur (:func:`.reconnect`) puis ré-essaie
    d'exécuter la commande avant de lever une erreur.
    """
    escaped = cmd.replace('"', r'\"')

    next(config.logs)
    try:
        config.screen.send_commands(escaped)
    except _LConException:
        ok = await reconnect()
        if not ok:
            raise

        config.screen.send_commands(escaped)

    raw = next(config.logs)
    await asyncio.sleep(wait)
    return raw


async def get_last_messages():
    return next(config.logs)
