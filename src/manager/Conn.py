import sqlite3
from sqlite3 import Connection


class Con:
    _con:Connection = sqlite3.connect("dbs/Tune.db", check_same_thread=False)
    @classmethod
    def getCon(cls) -> Connection:
        return cls._con