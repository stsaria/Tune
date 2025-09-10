from itertools import chain
from threading import Lock, Thread
from typing import Iterable

from model.NodeInfo import NodeInfo
from src.Settings import Key, Settings
from src.manager.Nodes import Nodes
from src.model.Message import ReplyMessage, RootMessage
from src.manager.Messages import MyMessages, OthersMessages
from src.net.Me import Me
from src.net.Node import Node
from src.util import nodeTrans, timestamp
from src.typeDefined import MSG

class Api:
    _started:bool = False
    _startedLock:Lock = Lock()
    # Core
    @staticmethod
    def start() -> None:
        """Start Tune Client/Server."""
        with Api._startedLock:
            if Api._started: return
            Api._started = True
            Thread(target=Me.serve, daemon=True).start()
            Thread(target=Me.syncer, daemon=True).start()
    
    # Nodes
    @staticmethod
    def getAllNodes() -> list[Node]:
        """Get all known nodes."""
        return Nodes.getNodes()
    @staticmethod
    def getAllNodeTraffics() -> dict[str:int]:
        """Get traffic in bytes for all known nodes."""
        return Nodes.getNodesTraffics()
    # Node
    @staticmethod
    def registerNodeById(id:str) -> bool:
        """Register a new node and return its success status."""
        return Nodes.registerNode(Node.nodeFromIAndP(nodeTrans.nodeIAndPFromId(id)))
    @staticmethod
    def getTrafficByNode(node:Node) -> int:
        """Get traffic in bytes for a node."""
        return Nodes.getNodeTraffic(node.getNodeInfo().ip)
    @staticmethod
    def banNodeByIp(ip:str) -> None:
        """Ban a node by IP address."""
        Nodes.ban(ip)
        OthersMessages.deleteMessagesFromIp(ip)
    @staticmethod
    def banNodeById(nodeId:str) -> None:
        """Ban a node by Node ID."""
        try:
            ip = nodeTrans.separateNodeIAndP(nodeTrans.nodeIAndPFromId(nodeId))[0]
            Api.banNodeByIp(ip)
        except:
            pass
    @staticmethod
    def unbanNodeByIp(ip:str) -> None:
        """Unban a node by IP address."""
        Nodes.unban(ip)
    @staticmethod
    def unbanNodeById(nodeId:str) -> None:
        """Unban a node by Node ID."""
        try:
            Api.unbanNodeByIp(nodeTrans.separateNodeIAndP(nodeTrans.nodeIAndPFromId(nodeId))[0])
        except:
            pass
    
    # Messages
    @staticmethod
    def getAllMessages() -> Iterable[MSG]:
        """Get all messages.(include my messages)"""
        return chain(OthersMessages.getMessages(), MyMessages.getMessages())
    @staticmethod
    def getAllRootMessages() -> Iterable[RootMessage]:
        """Get all root messages.(include my messages)"""
        return chain(OthersMessages.getRootMessages(), MyMessages.getRootMessages())
    @staticmethod
    def getAllReplyMessages() -> Iterable[ReplyMessage]:
        """Get all reply messages.(include my messages)"""
        return chain(OthersMessages.getReplyMessages(), MyMessages.getReplyMessages())
    @staticmethod
    def getReplyMessagesByRootMessage(rootMsg:RootMessage) -> list[ReplyMessage]:
        """Get all reply messages for a root message."""
        return [msg for msg in Api.getAllReplyMessages() if msg.fromHash == rootMsg.hash()]
    # Message
    @staticmethod
    def postRootMessage(content:str) -> None:
        """Post a new root message."""
        MyMessages.addMessage(RootMessage(content=content, timestamp=timestamp.now()))
    @staticmethod
    def postReplyMessage(rootMsg:RootMessage, content:str) -> int:
        """
        Post a new reply message to a root message.

        Return codes:
        0: Success
        1: The original message has no author or the author's public key is missing.
        2: The original message is a reply message, cannot reply to a reply.
        """
        if not rootMsg.author or not rootMsg.author.getNodeInfo().pubKey: return 1
        elif isinstance(rootMsg, ReplyMessage): return 2
        if "y" in Settings.get(Key.COPY_REPLY_FROM_MSGS).lower():
            MyMessages.addDelegateMessage(rootMsg)
            fromNode = Nodes.getNodeOrGenerateByIAndPOrPubKey(Settings.get(Key.IMYME_ADDR), rootMsg.author.getNodeInfo().pubKey)
        else:
            fromNode = rootMsg.author
        MyMessages.addMessage(ReplyMessage(content=content, timestamp=timestamp.now(), fromHash=rootMsg.hash(), fromNode=fromNode))
        return 0
    