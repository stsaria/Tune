import duckdb
from duckdb import DuckDBPyConnection
from src.defined import SAVED_PATH, DB_FILE_NAME

class Con:
    @classmethod
    def getCon(cls) -> DuckDBPyConnection:
        con = duckdb.connect(f"{SAVED_PATH}{DB_FILE_NAME}")
        return con