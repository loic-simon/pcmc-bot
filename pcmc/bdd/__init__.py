"""pcmc-bot / Gestion des données

Déclaration de toutes les tables, colonnes, méthodes, et connection à la BDD

"""

import sqlalchemy
import psycopg2

from pcmc.bdd import base
from pcmc.bdd.enums import *
from pcmc.bdd.model_joueurs import *
# All tables and enums directly accessible via bdd.<name>


#: __all__ = toutes les classes de données publiques
__all__ = [nom for nom in base.tables if not nom.startswith("_")]


tables = base.tables

connect = base.connect

SQLAlchemyError = sqlalchemy.exc.SQLAlchemyError

DriverOperationalError = psycopg2.OperationalError
