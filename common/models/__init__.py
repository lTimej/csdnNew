import pymysql
from .dbConfig.dbconfig import RoutingSQLAlchemy

pymysql.install_as_MySQLdb()

db = RoutingSQLAlchemy()