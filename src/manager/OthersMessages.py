from threading import Lock

from src.typeDefined import MSG_GENE, MSG, MSGS
from src.model.Message import RootMessage, ReplyMessage

class OthersMessages:
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
    def deleteMessagesFromIp(cls, ip: str) -> None:
        with cls._messagesLock:
            for k in [k for k, m in cls._messages.items() if m.author.getNodeInfo().ip == ip]:
                cls._messages.pop(k)
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