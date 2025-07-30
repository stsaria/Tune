from threading import RLock

from src.model import Message
from src.model.Message import ReplyMessage


class Messages:
    _messages:list[Message | ReplyMessage] = []
    _messagesLock:RLock = RLock()
    @classmethod
    def addMessage(cls, message:Message | ReplyMessage):
