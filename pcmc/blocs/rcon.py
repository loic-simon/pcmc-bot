"""pcmc-bot / blocs / Communication distante avec le serveur Minecraft

Force la communication distante : privilégier pcmc.blocs.server.

"""

import asyncio

import asyncrcon

from pcmc import config
from pcmc.blocs import env


_RConException = asyncrcon.MaxRetriesExceedException


async def connect():
    """Ouvre la connexion au serveur PC Minecraft.

    Returns:
        ``True`` (la connexion a réussi) ou ``False`` (la connexion a échoué)

    L'IP et le mot de passe du serveur sont lus par cette fonction depuis
    les variables d'environnement ``PCMC_RCON_IP`` et ``PCMC_RCON_PASSWORD``.

    Si le bot est déjà connecté, retourne directement ``True``
    (sans vérifier l'état de la connexion).
    """
    if config.online:
        return True
    ip = env.load("PCMC_RCON_IP")
    password = env.load("PCMC_RCON_PASSWORD")
    config.mcr = asyncrcon.AsyncRCON(ip, password)
    try:
        await config.mcr.open_connection()
    except (OSError, _RConException):
        config.online = False
        return False

    config.online = True
    return True


def disconnect():
    """Ferme la connexion au serveur PC Minecraft.

    Si le bot n'est pas connecté, ne fait rien.
    """
    if not config.online:
        pass
    config.mcr.close()
    config.mcr = None
    config.online = False


async def reconnect():
    """Ferme puis ré-ouvre la connexion au serveur PC Minecraft.

    Globalement équivalent à un appel à :func:`.disconnect` puis
    :func:`.connect`.

    Returns:
        bool: La valeur retournée par :func:`.connect`.
    """
    disconnect()
    await asyncio.sleep(2)
    return await connect()


async def command(cmd, wait=0.5):
    """Exécute une commande Minecraft et retourne le résultat obtenu.

    Args:
        cmd (str): la commande Minecraft a exécuter (avec ou sans ``/``)
        wait (float): ignoré ici, pour compatibilité avec ``lcon``

    Returns:
        Optionnal[str]: La réponse du serveur, le cas échéant.

    Raises:
        ConnectionError: Il y a eu un problème de communication
            avec le serveur.

    En cas d'erreur de communication, cette fonction tente d'abord de
    se reconnecter au serveur (:func:`.reconnect`) puis ré-essaie
    d'exécuter la commande avant de lever une erreur.
    """
    try:
        return await config.mcr.command(cmd)
    except (OSError, _RConException):
        ok = await reconnect()
        if not ok:
            raise

        return await config.mcr.command(cmd)


async def get_last_messages():
    return ""
