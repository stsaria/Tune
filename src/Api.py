import os
from itertools import chain
from threading import Lock, Thread
from typing import Iterable

from src.defined import SAVED_PATH
os.makedirs(SAVED_PATH, exist_ok=True)

from src.globalNet.manager.Nodes import Nodes as GlNodes
from src.globalNet.model.Message import ReplyMessage, RootMessage
from src.globalNet.manager.Messages import MyMessages, OthersMessages
from src.globalNet.Me import Me as GlMe
from src.globalNet.Node import Node as GlNode
from src.base.util import nodeTrans, timestamp
from src.Settings import Key, Settings

class _GlApi:
    _started:bool = False
    _startedLock:Lock = Lock()
    # Core
    @staticmethod
    def start() -> None:
        """Start Tune Client/Server."""
        with Api._startedLock:
            if Api._started: return
            Api._started = True
            Thread(target=GlMe.serve, daemon=True).start()
            Thread(target=GlMe.syncer, daemon=True).start()
    
    # Nodes
    @staticmethod
    def getAllNodes() -> list[GlNode]:
        """Get all known nodes."""
        return GlNodes.getNodes()
    @staticmethod
    def getAllNodeTraffics() -> dict[str:int]:
        """Get traffic in bytes for all known nodes."""
        return GlNodes.getNodesTraffics()
    # Node
    @staticmethod
    def registerNodeById(id:str) -> bool:
        """Register a new node and return its success status."""
        return GlNodes.registerNode(GlNode.nodeFromIAndP(nodeTrans.nodeIAndPFromId(id)))
    @staticmethod
    def getTrafficByNode(node:GlNode) -> int:
        """Get traffic in bytes for a node."""
        return GlNodes.getNodeTraffic(node.getNodeInfo().ip)
    @staticmethod
    def banNodeByIp(ip:str) -> None:
        """Ban a node by IP address."""
        GlNodes.ban(ip)
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
        GlNodes.unban(ip)
    @staticmethod
    def unbanNodeById(nodeId:str) -> None:
        """Unban a node by Node ID."""
        try:
            Api.unbanNodeByIp(nodeTrans.separateNodeIAndP(nodeTrans.nodeIAndPFromId(nodeId))[0])
        except:
            pass
    
    # Messages
    @staticmethod
    def getAllMessages() -> Iterable[RootMessage | ReplyMessage]:
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
        3: The root message does not exist in MyMessages, cannot reply.
        """
        if not rootMsg.author or not rootMsg.author.getNodeInfo().pubKey: return 1
        elif isinstance(rootMsg, ReplyMessage): return 2
        elif MyMessages.getMessageByHash(rootMsg.hash()): return 3
        if "y" in Settings.get(Key.COPY_REPLY_FROM_MSGS).lower():
            MyMessages.addDelegateMessage(rootMsg)
            fromNode = GlNodes.getNodeOrGenerateByIAndPOrPubKey(Settings.get(Key.IMYME_ADDR), rootMsg.author.getNodeInfo().pubKey)
        else:
            fromNode = rootMsg.author
        MyMessages.addMessage(ReplyMessage(content=content, timestamp=timestamp.now(), fromHash=rootMsg.hash(), fromNode=fromNode))
        return 0

class _DiApi:
    pass

class Api(_GlApi, _DiApi):
    GlobalNet = _GlApi
    DirectNet = _DiApi