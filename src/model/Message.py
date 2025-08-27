from dataclasses import dataclass
from abc import ABC, abstractmethod
from src.util import sha256

@dataclass(kw_only=True)
class Message(ABC):
    from src.net.Node import Node
    content: str
    timestamp: int
    author:Node = None
    sig:str = None
    @abstractmethod
    def hash(self) -> str:
        pass

@dataclass
class RootMessage(Message):
    def hash(self):
        hS = f"{self.content}{self.timestamp}"
        if self.author:
            hS += self.author.getNodeInfo().pubKey
        else:
            from src.net.Me import Me
            hS += Me.getPubKey()
        return sha256.hash(hS)

@dataclass
class ReplyMessage(Message):
    from src.net.Node import Node
    fromNode:Node
    fromHash:str
    isFromDelegate:bool = False
    def hash(self):
        hS = f"{self.content}{self.timestamp}{self.fromHash}"
        if self.author:
            hS += self.author.getNodeInfo().pubKey
        else:
            from src.net.Me import Me
            hS += Me.getPubKey()
        return sha256.hash(hS)

@dataclass
class DelegateMessaege:
    baseMessage:Message
    delegatePub:str
    def hash(self) -> str:
        hS = f"{self.baseMessage.hash()}{self.delegatePub}"
        if self.author:
            hS += self.delegatePub
        else:
            from src.net.Me import Me
            hS += Me.getPubKey()
        return sha256.hash(hS)