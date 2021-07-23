"""pcmc-bot / blocs / Communication avec le serveur Minecraft

Choisit entre contrôle local (screen/logfile) ou distant (RCon)

"""

from pcmc.blocs import env

mode = env.load("PCMC_CONTROL_MODE")

if mode.lower() == "local":
    from pcmc.blocs.lcon import *
elif mode.lower() == "remote":
    from pcmc.blocs.rcon import *
else:
    raise RuntimeError(f"Unknown control mode PCMC_CONTROL_MODE='{mode}' "
                       "(should be 'local' or 'remote')") from None
