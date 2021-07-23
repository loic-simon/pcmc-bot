"""pcmc-bot / bdd / Modèle de données

Déclaration de toutes les tables et leurs colonnes

"""

import datetime

import sqlalchemy
from sqlalchemy.ext.hybrid import hybrid_property

from pcmc import config
from pcmc.bdd import base
from pcmc.bdd.base import (autodoc_Column, autodoc_ManyToOne,
                            autodoc_OneToMany, autodoc_DynamicOneToMany)
# from pcmc.bdd.enums import Statut, CandidHaroType, Vote


# Tables de données

class Joueur(base.TableBase):
    """Table de données des joueurs inscrits."""

    discord_id = autodoc_Column(
        sqlalchemy.BigInteger(),
        primary_key=True,
        autoincrement=False,
        doc="ID Discord du joueur",
    )
    nom = autodoc_Column(
        sqlalchemy.String(32),
        nullable=False,
        doc="Nom (réel ou pseudo connu) du joueur",
    )

    pseudo = autodoc_Column(
        sqlalchemy.String(64),
        nullable=False,
        doc="Pseudo Minecraft du joueur",
    )
    uuid = autodoc_Column(
        sqlalchemy.String(36),
        doc="UUID Minecraft du joueur",
    )

    inscription = autodoc_Column(
        sqlalchemy.DateTime(),
        nullable=False,
        doc="Timestamp d'inscription du joueur",
    )
    pseudo = autodoc_Column(
        sqlalchemy.String(64),
        nullable=False,
        doc="Pseudo Minecraft du joueur",
    )
    en_jeu = autodoc_Column(
        sqlalchemy.Boolean(),
        nullable=False,
        default=False,
        doc="Si le joueur est actuellement connecté",
    )

    _webhook_id = autodoc_Column(
        sqlalchemy.BigInteger(),
        doc="ID du webhook pour parler en tant que le joueur",
    )

    def __repr__(self):
        """Return repr(self)."""
        return f"<Joueur #{self.discord_id} ({self.nom})>"

    def __str__(self):
        """Return str(self)."""
        return str(self.nom)

    @property
    def member(self):
        """discord.Member: Membre Discord correspondant à ce Joueur.

        Raises:
            ValueError: pas de membre correspondant
            ~ready_check.NotReadyError: bot non connecté
                (:obj:`.config.guild` vaut ``None``)
        """
        result = config.guild.get_member(self.discord_id)
        if not result:
            raise ValueError(f"Joueur.member : pas de membre pour `{self}` !")

        return result

    @property
    def mc_name(self):
        """str: Nom affiché dans Minecraft.

        Retourne ``{pseudo} – {nom}``.
        """
        return f"{self.pseudo} – {self.nom}"

    @property
    def team(self):
        """str: Nom de l'équipe personnalisée de ce joueur.

        Retourne ``team_`` suivi du début du pseudo du joueur.
        """
        return "team_" + self.pseudo[:10]

    async def get_webhook(self):
        """Récupère le webhook pour parler en tant que le joueur.

        Returns:
            :class:`discord.Webhook`
        """
        return config.bot.fetch_webhook(self._webhook_id)


    @classmethod
    def from_member(cls, member):
        """Récupère le Joueur (instance de BDD) lié à un membre Discord.

        Args:
            member (discord.Member): le membre concerné

        Returns:
            Joueur: Le joueur correspondant.

        Raises:
            ValueError: membre introuvable en base
            ~ready_check.NotReadyError: session non initialisée
                (:obj:`.config.session` vaut ``None``)
        """
        joueur = cls.query.get(member.id)
        if not joueur:
            raise ValueError("Joueur.from_member : "
                             f"pas de joueur en base pour `{member}` !")

        return joueur
