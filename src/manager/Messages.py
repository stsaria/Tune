from manager.Nodes import Nodes
from src.typeDefined import MSG_GENE, MSG, MSGS
from manager.DB import DB
from src.model.Message import RootMessage, ReplyMessage, DelegateMessaege
from threading import Lock
from abc import ABC, abstractmethod

from src.typeDefined import MSG_GENE, MSG, MSGS
from src.model.Message import RootMessage, ReplyMessage


MSG_TUPLE = tuple[str, str, int, str, str, str]
DELEGATE_MSG_TUPLE = tuple[str, str, int, str, str, str, str, str]

class Messages(ABC):
    @classmethod
    @abstractmethod
    def addMessage(cls, msg: MSG) -> None:
        pass
    @classmethod
    @abstractmethod
    def deleteMessage(cls, msg: str | MSG) -> None:
        pass
    @classmethod
    @abstractmethod
    def getMessageFromHash(cls, msgHash: str) -> MSG | None:
        pass

    @classmethod
    @abstractmethod
    def getMessages(cls) -> MSGS:
        pass
    @classmethod
    @abstractmethod
    def getRootMessages(cls) -> MSG_GENE:
        pass
    @classmethod
    @abstractmethod
    def getReplyMessages(cls) -> MSG_GENE:
        pass


class OthersMessages(Messages):
    _messages:dict[str, MSG] = {}
    _messagesLock:Lock = Lock()

    @classmethod
    def addMessage(cls, msg: MSG) -> None:
        if msg.timestamp < 0: return
        h = msg.hash()
        with cls._messagesLock:
            if h in cls._messages: return
            cls._messages[h] = msg
    @classmethod
    def deleteMessage(cls, msg: str | MSG) -> None:
        msgHash = msg.hash() if isinstance(msg, MSG) else msg
        with cls._messagesLock:
            cls._messages.pop(msgHash, None)
    @classmethod
    def getMessages(cls) -> MSGS:
        with cls._messagesLock:
            return list(cls._messages.values())
    @classmethod
    def getMessageFromHash(cls, msgHash: str) -> MSG | None:
        with cls._messagesLock:
            return cls._messages.get(msgHash)
    @classmethod
    def getRootMessages(cls) -> MSG_GENE:
        return [m for m in cls.getMessages() if isinstance(m, RootMessage)]
    @classmethod
    def getReplyMessages(cls) -> MSG_GENE:
        return [m for m in cls.getMessages() if isinstance(m, ReplyMessage)]

    @classmethod
    def deleteMessagesFromIp(cls, ip: str) -> None:
        with cls._messagesLock:
            for k in [k for k, m in cls._messages.items() if m.author.getNodeInfo().ip == ip]:
                cls._messages.pop(k)

class MyMessages(Messages):
    @classmethod
    def addMessage(cls, message:MSG) -> None:
        content = message.content
        if isinstance(message, ReplyMessage):
            fromNodeInfo = message.fromNode.getNodeInfo()
            fromIpColonPort = fromNodeInfo.getIPColonPort()
            fromPubKey = fromNodeInfo.pubKey
            fromHash = message.fromHash
            DB.execAndCommit(
                "INSERT INTO myMessages (hash, c, ts, fromAddr, fromPub, fromHash) VALUES (?, ?, ?, ?, ?, ?)",
                (message.hash(), content, message.timestamp, fromIpColonPort, fromPubKey, fromHash)
            )
        else:
            DB.execAndCommit(
                "INSERT INTO myMessages (hash, c, ts) VALUES (?, ?, ?)",
                (message.hash(), content, message.timestamp)
            )
    @classmethod
    def deleteMessage(cls, message:MSG):
        DB.execAndCommit("DELETE FROM myMessages WHERE hash=?", (message.hash(),))
    @classmethod
    def getMessages(cls) -> MSGS:
        return [cls._sqlMsgToMsg(m) for m in cls._getSqlMessages()]
    @classmethod
    def getRootMessages(cls) -> MSGS:
        return [m for m in cls.getMessages() if isinstance(m, RootMessage)]
    @classmethod
    def getReplyMessages(cls) -> MSGS:
        return [m for m in cls.getMessages() if isinstance(m, ReplyMessage)]
    @classmethod
    def getRandomMessage(cls) -> MSG:
        return cls._sqlMsgToMsg(cls._getSqlRandMessage())
    @classmethod
    def getMessageFromHash(cls, msgHash:str, isDelegate:bool=False) -> MSG | DelegateMessaege | None:
        m = DB.fetchOne("SELECT * FROM "+("delegateMessages" if isDelegate else "myMessages")+" WHERE hash = ?", (msgHash,))
        return cls._sqlMsgToMsg(m, isDelegate=isDelegate) if m else None

    @classmethod
    def addDelegateMessage(cls, message:MSG) -> None:
        h, c, ts, dgPub, dgSig = message.hash(), message.content, message.timestamp, message.author.getNodeInfo().pubKey, message.sig
        if isinstance(message, ReplyMessage):
            DB.execAndCommit(
                "INSERT INTO delegateMessages (hash, c, ts, dgPub, dgSig, fromAddr, fromPub, fromHash) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (h, c, ts, dgPub, dgSig, message.fromNode.getNodeInfo().getIPColonPort(), message.fromNode.getNodeInfo().pubKey, message.fromHash)
            )
        else:
            DB.execAndCommit(
                "INSERT INTO delegateMessages (hash, c, ts, dgPub, dgSig) VALUES (?, ?, ?, ?, ?)",
                (h, c, ts, dgPub, dgSig)
            )
    @classmethod
    def getLength(cls) -> int:
        return DB.fetchOne("SELECT COUNT(*) FROM myMessages")[0]
    @classmethod
    def _getSqlMessages(cls) -> list[MSG_TUPLE]:
        return DB.fetchAll("SELECT * FROM myMessages")
    @classmethod
    def _getSqlDelegateMessages(cls) -> list[DELEGATE_MSG_TUPLE]:
        return DB.fetchAll("SELECT * FROM delegateMessages")
    @classmethod
    def _getSqlRandMessage(cls) -> MSG_TUPLE:
        return DB.fetchOne("SELECT * FROM myMessages ORDER BY RANDOM() LIMIT 1")
    @classmethod
    def _sqlMsgToMsg(cls, m:MSG_TUPLE | DELEGATE_MSG_TUPLE, isDelegate:bool=False) -> MSG:
        if not m:
            return RootMessage(content="KA", timestamp=-1)
        if isDelegate:
            if m[5] and m[6] and m[7]:
                baseM = ReplyMessage(content=m[1], timestamp=m[2], fromNode=Nodes.getNodeOrGenerateByIAndPOrPubKey(m[5], m[6]), fromHash=m[7])
            else:
                baseM = RootMessage(content=m[1], timestamp=m[2])
            return DelegateMessaege(baseM, delegatePub=m[3])
        else:
            if m[3] and m[4] and m[5]:
                return ReplyMessage(content=m[1], timestamp=m[2], fromNode=Nodes.getNodeOrGenerateByIAndPOrPubKey(m[3], m[4]), fromHash=m[5])
            else:
                return RootMessage(content=m[1], timestamp=m[2])

    DB.execAndCommit("""
            CREATE TABLE IF NOT EXISTS myMessages (
                hash TEXT PRIMARY KEY,
                c TEXT NOT NULL,
                ts INTEGER NOT NULL,
                
                fromAddr TEXT,
                fromPub TEXT,
                fromHash TEXT
            )
        """)
    DB.execAndCommit("""
        CREATE TABLE IF NOT EXISTS delegateMessages (
            hash TEXT PRIMARY KEY,
            c TEXT NOT NULL,
            ts INTEGER NOT NULL,
            dgPub TEXT NOT NULL,
            dgSig TEXT NOT NULL,
            
            fromAddr TEXT,
            fromPub TEXT,
            fromHash TEXT
        )
    """)