import os

CONFIG = {}
dburl = os.environ.get("POSTGRES_URL_SQLALCHEMY")
CONFIG['DATABASE_URL'] = dburl
