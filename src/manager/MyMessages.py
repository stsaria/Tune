import time
from sqlite3 import Connection, Cursor
from typing import Generator

from src.defined import MSG_GENE, MSG
from src.manager.Conn import Con
from src.model.Message import RootMessage, ReplyMessage
from src.util import sha256

MSG_TUPLE = tuple[str, str, int, str, str, str]

class MyMessages:
    _con:Connection = Con.getCon()
    _cur:Cursor = _con.cursor()
    _cur.execute("""
        CREATE TABLE IF NOT EXISTS myMessages (
            hash TEXT PRIMARY KEY,
            c TEXT NOT NULL,
            ts INTEGER NOT NULL,
            fromAddr TEXT,
            fromPub TEXT,
            fromHash TEXT
        )
    """)
    @classmethod
    def postMessage(cls, message:MSG) -> None:
        content = message.content
        ts = int(time.time())
        if type(message) == ReplyMessage:
            fromNodeInfo = message.fromNode.getNodeInfo()
            fromIpColonPort = fromNodeInfo.getIpColonPort()
            fromPubKey = fromNodeInfo.pubKey
            fromHash = message.fromHash
            cls._cur.execute(
                "INSERT INTO myMessages (hash, c, ts, fromAddr, fromPub, fromHash) VALUES (?, ?, ?, ?, ?, ?)",
                (sha256.hash(f"{content}{ts}{fromIpColonPort}{fromPubKey}{fromHash}"), content, ts, fromIpColonPort, fromPubKey, fromHash)
            )
        else:
            cls._cur.execute(
                "INSERT INTO myMessages (hash, c, ts) VALUES (?, ?, ?)",
                (sha256.hash(f"{content}{ts}"), content, ts)
            )
    @classmethod
    def _getLength(cls) -> int:
        cls._cur.execute("SELECT COUNT(*) FROM myMessages")
        return cls._cur.fetchone()[0]
    @classmethod
    def _getSqlMessages(cls) -> list:
        cls._cur.execute("SELECT * FROM myMessages")
        return cls._cur.fetchall()
    @classmethod
    def _getSqlRandMessage(cls) -> MSG_TUPLE:
        cls._cur.execute("SELECT * FROM myMessages ORDER BY RANDOM() LIMIT 1")
        return cls._cur.fetchone()
    @classmethod
    def _sqlMsgToMsg(cls, m:MSG_TUPLE) -> MSG:
        if m[3] and m[4] and m[5]:
            return ReplyMessage(m[1], m[2], m[3], m[4], m[5])
        else:
            return RootMessage(m[1], m[2])
    @classmethod
    def getMessages(cls) -> MSG_GENE:
        for m in cls._getSqlMessages():
            yield cls._sqlMsgToMsg(m)
    @classmethod
    def getRootMessages(cls) -> MSG_GENE:
        for m in cls.getMessages():
            if type(m) != ReplyMessage:
                yield m
    @classmethod
    def getReplyMessages(cls) -> MSG_GENE:
        for m in cls.getMessages():
            if type(m) == ReplyMessage:
                yield m
    @classmethod
    def getRandomMessage(cls) -> MSG:
        return cls._sqlMsgToMsg(cls._getSqlRandMessage())
