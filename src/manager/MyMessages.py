import random
import sqlite3
import time
from sqlite3 import Connection, Cursor
from typing import Any

from src.model.Message import Message, ReplyMessage
from src.util import sha256


class MyMessages:
    _con:Connection = sqlite3.connect("dbs/myMessages.db")
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
    def postMessage(cls, message: Message | ReplyMessage) -> None:
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
    def _getSqlMessages(cls) -> list[Any]:
        cls._cur.execute("SELECT * FROM myMessages")
        return cls._cur.fetchall()
    @classmethod
    def getRootMessages(cls) -> list[Message]:
        messages:list[Message] = []
        for sqlMes in cls._getSqlMessages():
            if sqlMes[3] and sqlMes[4] and sqlMes[5]:
                continue
            messages.append(Message(sqlMes[1], sqlMes[2]))
        return messages
    @classmethod
    def getReplyMessages(cls) -> list[ReplyMessage]:
        messages:list[ReplyMessage] = []
        for sqlMes in cls._getSqlMessages():
            if not (sqlMes[3] and sqlMes[4] and sqlMes[5]):
                continue
            messages.append(ReplyMessage(sqlMes[1], sqlMes[2], sqlMes[4], sqlMes[5]))
        return messages
    @classmethod
    def getRandomMessage(cls) -> Message | ReplyMessage:
        return random.choice(cls.getRootMessages()+cls.getReplyMessages())