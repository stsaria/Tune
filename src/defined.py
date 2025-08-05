from typing import Generator

from src.model.Message import ReplyMessage, RootMessage

SQL_MSG_TUPLE = tuple[str, str, int, str, str, str]
MSG_GENE = Generator[ReplyMessage | RootMessage, any, None]
MSG = ReplyMessage | RootMessage