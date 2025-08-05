from threading import RLock

from src.defined import MSG_GENE, MSG
from src.model.Message import RootMessage, ReplyMessage


class Messages:
    _messages:list[MSG] = []
    _messagesLock:RLock = RLock()
    @classmethod
    def addMessage(cls, msg:MSG) -> None:
        if msg.timestamp < 0:
            return
        with cls._messagesLock:
            if cls.getMessageFromHash(msg.hash()):
                return
            cls._messages.append(msg)
    @classmethod
    def deleteMessage(cls, msgHash:str) -> None:
        for m in cls.getMessages():
            if m.hash() != msgHash:
                continue
            with cls._messagesLock:
                cls._messages.remove(m)
    @classmethod
    def getMessages(cls) -> MSG_GENE:
        with cls._messagesLock:
            for m in cls._messages:
                yield m
    @classmethod
    def getMessageFromHash(cls, msgHash:str) -> MSG | None:
        for m in cls.getMessages():
            if m.hash() == msgHash:
                return m
        return None
    @classmethod
    def getRootMessages(cls) -> MSG_GENE:
        msgS = []
        for m in cls.getMessages():
            if type(m) == RootMessage:
                msgS.append(m)
        return msgS
    @classmethod
    def getReplyMessages(cls) -> MSG_GENE:
        for m in cls.getMessages():
            if type(m) == ReplyMessage:
                yield m