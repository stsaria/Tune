from dataclasses import dataclass
from src.util import sha256

Node = any

@dataclass
class RootMessage:
    from src.net.Node import Node
    content:str
    timestamp:int
    author:Node=None
    def hash(self):
        hS = f"{self.content}{self.timestamp}"
        if self.author:
            hS += self.author.getNodeInfo().getPubKey()
        return sha256.hash(hS)

@dataclass
class ReplyMessage:
    content:str
    timestamp:int

    fromNode:Node
    fromHash:str

    author:Node=None
    def hash(self):
        hS = f"{self.content}{self.timestamp}{self.fromHash}"
        if self.author:
            hS += self.author.getNodeInfo().getPubKey()
        return sha256.hash(hS)