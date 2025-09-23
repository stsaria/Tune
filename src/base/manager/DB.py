import duckdb
from duckdb import DuckDBPyConnection
from src.defined import SAVED_PATH, DB_FILE_NAME

class DB:
    @staticmethod
    def getCon() -> DuckDBPyConnection:
        return duckdb.connect(f"{SAVED_PATH}{DB_FILE_NAME}")
    @staticmethod
    def execAndCommit(sql:str, params:tuple=()) -> None:
        con = DB.getCon()
        con.execute(sql, params)
        con.commit()
        con.close()
    @staticmethod
    def fetchOne(sql:str, params:tuple=()) -> tuple:
        con = DB.getCon()
        con.execute(sql, params)
        r = con.fetchone()
        con.close()
        return r
    @staticmethod
    def fetchAll(sql:str, params:tuple=()) -> tuple:
        con = DB.getCon()
        con.execute(sql, params)
        r = con.fetchall()
        con.close()
        return r