# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## 1.1.0 - 2021-07-23

### Added

   - :mod:`.bdd` and :class:`.bdd.Joueur`;
   - ``!whitelist`` and whitelist management;
   - :attr:`config.Role.joueur` and :attr:`config.Role.en_jeu` roles;
   - :attr:`config.Role.en_jeu` automatic grant/ungrant.

### Fixed

   - Uncaught errors when losing connection to RCon.


## 1.0.0 - 2021-07-17

Initial release:
   - Communication with Minecraft server through asynchrone rcon;
   - Automatic bot activity updates;
   - Execution of arbitrary Minecraft commands (``!!``),
   - ``!status`` with TPS measurement;
   - In-game transmission of Discord messages & voice (dis)connections;
   - Bot structure and special commands inherited from loic-simon/lg-rez.
