from threading import RLock
from src.defined import MSG_GENE, MSG
from src.model.Message import RootMessage, ReplyMessage

class Messages:
    _messages: dict[str, MSG] = {}
    _messagesLock: RLock = RLock()

    @classmethod
    def addMessage(cls, msg: MSG) -> None:
        if msg.timestamp < 0:
            return
        key = msg.hash()
        with cls._messagesLock:
            if key in cls._messages:
                return
            cls._messages[key] = msg
    @classmethod
    def deleteMessage(cls, msgHash: str) -> None:
        with cls._messagesLock:
            cls._messages.pop(msgHash, None)
    @classmethod
    def deleteMessagesFromIp(cls, ip: str) -> None:
        with cls._messagesLock:
            keys_to_delete = [k for k, m in cls._messages.items() if m.ip == ip]
            for k in keys_to_delete:
                del cls._messages[k]
    @classmethod
    def getMessages(cls) -> MSG_GENE:
        with cls._messagesLock:
            yield from cls._messages.values()
    @classmethod
    def getMessageFromHash(cls, msgHash: str) -> MSG | None:
        with cls._messagesLock:
            return cls._messages.get(msgHash)
    @classmethod
    def getRootMessages(cls) -> MSG_GENE:
        with cls._messagesLock:
            for m in cls._messages.values():
                if isinstance(m, RootMessage):
                    yield m
    @classmethod
    def getReplyMessages(cls) -> MSG_GENE:
        with cls._messagesLock:
            for m in cls._messages.values():
                if isinstance(m, ReplyMessage):
                    yield m