"""Message モジュール

自動生成ドキュメント用 docstring。
"""

from dataclasses import dataclass

from abc import ABC, abstractmethod
from src.allNet.util import sha256
from src.globalNet.Node import Node

"""
Message data classes.

NOTE for API users:
    - Do NOT construct RootMessage / ReplyMessage directly.
    - Use Api.postRootMessage / Api.postReplyMessage instead.
    - Direct construction is allowed for advanced use cases,
      but no guarantees are provided (self-responsibility).
"""

@dataclass(kw_only=True)
class Message(ABC):
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
            from globalNet.Me import Me
            hS += Me.getPubKey()
        return sha256.hash(hS)

@dataclass
class ReplyMessage(Message):
    fromNode:Node
    fromHash:str
    isFromDelegate:bool = False
    def hash(self):
        hS = f"{self.content}{self.timestamp}{self.fromHash}"
        if self.author:
            hS += self.author.getNodeInfo().pubKey
        else:
            from globalNet.Me import Me
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
            from globalNet.Me import Me
            hS += Me.getPubKey()
        return sha256.hash(hS)