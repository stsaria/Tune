import time
from duckdb import DuckDBPyConnection
from typing import Generator

from src.Settings import Settings
from src.net.Node import Node
from src.manager.Nodes import Nodes
from src.typeDefined import MSG_GENE, MSG, MSGS
from src.manager.Conn import Con
from src.model.Message import RootMessage, ReplyMessage, DelegateMessaege
from src.util import nodeTrans

MSG_TUPLE = tuple[str, str, int, str, str, str]
DELEGATE_MSG_TUPLE = tuple[str, str, int, str, str, str, str, str]

class MyMessages:
    @classmethod
    def _execAndCommit(cls, sql:str, params:tuple=()) -> None:
        con = Con.getCon()
        con.execute(sql, params)
        con.commit()
        con.close()
    _execAndCommit("""
        CREATE TABLE IF NOT EXISTS myMessages (
            hash TEXT PRIMARY KEY,
            c TEXT NOT NULL,
            ts INTEGER NOT NULL,
            
            fromAddr TEXT,
            fromPub TEXT,
            fromHash TEXT
        )
        CREATE TABLE IF NOT EXISTS delegateMessages (
            hash TEXT PRIMARY KEY,
            c TEXT NOT NULL,
            ts INTEGER NOT NULL,
            dgPub TEXT NOT NULL,
            dgSig TEXT NOT NULL
            
            fromAddr TEXT,
            fromPub TEXT,
            fromHash TEXT
        )
    """)
    @classmethod
    def addMessage(cls, message:MSG) -> None:
        content = message.content
        ts = int(time.time())
        if isinstance(message, ReplyMessage):
            fromNodeInfo = message.fromNode.getNodeInfo()
            fromIpColonPort = fromNodeInfo.getIPColonPort()
            fromPubKey = fromNodeInfo.pubKey
            fromHash = message.fromHash
            cls._execAndCommit(
                "INSERT INTO myMessages (hash, c, ts, fromAddr, fromPub, fromHash) VALUES (?, ?, ?, ?, ?, ?)",
                (message.hash(), content, ts, fromIpColonPort, fromPubKey, fromHash)
            )
        else:
            cls._execAndCommit(
                "INSERT INTO myMessages (hash, c, ts) VALUES (?, ?, ?)",
                (message.hash(), content, ts)
            )
    @classmethod
    def deleteMessage(cls, message:MSG):
        cls._execAndCommit("DELETE FROM myMessages WHERE ts = ?", (message.timestamp,))
    @classmethod
    def addDelegateMessage(cls, message:MSG) -> None:
        h, c, ts, dgPub, dgSig = message.hash(), message.content, message.timestamp, message.author.getNodeInfo().pubKey, message.sig
        if isinstance(message, ReplyMessage):
            cls._execAndCommit(
                "INSERT INTO delegateMessages (hash, c, ts, dgPub, dgSig, fromAddr, fromPub, fromHash) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (h, c, ts, dgPub, dgSig, message.fromNode.getNodeInfo().getIPColonPort(), message.fromNode.getNodeInfo().pubKey, message.fromHash)
            )
        else:
            cls._execAndCommit(
                "INSERT INTO delegateMessages (hash, c, ts, dgPub, dgSig) VALUES (?, ?, ?, ?, ?)",
                (h, c, ts, dgPub, dgSig)
            )
    @classmethod
    def _fetchOne(cls, sql:str, params:tuple=()) -> tuple:
        con = Con.getCon()
        con.execute(sql, params)
        r = con.fetchone()
        con.close()
        return r
    @classmethod
    def _fetchAll(cls, sql:str, params:tuple=()) -> tuple:
        con = Con.getCon()
        con.execute(sql, params)
        r = con.fetchall()
        con.close()
        return r
    @classmethod
    def _getLength(cls) -> int:
        return cls._fetchOne("SELECT COUNT(*) FROM myMessages")[0]
    @classmethod
    def _getSqlMessages(cls) -> list[MSG_TUPLE]:
        return cls._fetchAll("SELECT * FROM myMessages")
    @classmethod
    def _getSqlDelegateMessages(cls) -> list[DELEGATE_MSG_TUPLE]:
        return cls._fetchAll("SELECT * FROM delegateMessages")
    @classmethod
    def _getSqlRandMessage(cls) -> MSG_TUPLE:
        return cls._fetchOne("SELECT * FROM myMessages ORDER BY RANDOM() LIMIT 1")
    @classmethod
    def _sqlMsgToMsg(cls, m:MSG_TUPLE | DELEGATE_MSG_TUPLE) -> MSG:
        if not m:
            return RootMessage("KA", -1)
        if isinstance(m, DELEGATE_MSG_TUPLE):
            if m[5] and m[6] and m[7]:
                baseM = ReplyMessage(content=m[1], timestamp=m[2], fromNode=Nodes.getNodeOrGenerateFromIAndPOrPubkey(m[5], m[6]), fromHash=m[7])
            else:
                baseM = RootMessage(content=m[1], timestamp=m[2])
            return DelegateMessaege(baseM, delegatePub=m[3])
        else:
            if m[3] and m[4] and m[5]:
                return ReplyMessage(content=m[1], ts=m[2], fromNode=Nodes.getNodeOrGenerateFromIAndPOrPubkey(m[3], m[4]), fromHash=m[5])
            else:
                return RootMessage(m[1], m[2])
    @classmethod
    def getMessages(cls) -> MSGS:
        return [cls._sqlMsgToMsg(m) for m in cls._getSqlMessages()]
    @classmethod
    def getRootMessages(cls) -> MSGS:
        return [m for m in cls._getMessages() if isinstance(m, RootMessage)]
    @classmethod
    def getReplyMessages(cls) -> MSGS:
        return [m for m in cls._getMessages() if isinstance(m, ReplyMessage)]
    @classmethod
    def getRandomMessage(cls) -> MSG:
        return cls._sqlMsgToMsg(cls._getSqlRandMessage())
    @classmethod
    def getMessageFromHash(cls, msgHash:str, isDelegate:bool=False) -> MSG | DelegateMessaege | None:
        m = cls._fetchOne("SELECT * FROM "+("delegateMessages" if isDelegate else "myMessages")+" WHERE hash = ?", (msgHash,))
        return cls._sqlMsgToMsg(m) if m else None
    