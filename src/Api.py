import os
from itertools import chain
from threading import Lock, Thread
import time
from typing import Generator, Iterable

from src.defined import SAVED_PATH, DIRECT_NET_NAME, GLOBAL_NET_NAME
os.makedirs(SAVED_PATH, exist_ok=True)

from src.allNet.util import generatoot
from src.allNet.MyNet import MyNet
from src.allNet.manager.MyNets import MyNets
from src.allNet.manager.MyInfo import MyInfo

from src.globalNet.JobProcessor import JobProcessor as GlJobProcessor
from src.globalNet.manager.Nodes import Nodes as GlNodes
from src.globalNet.model.Message import ReplyMessage as GlReplyMessage, RootMessage as GlRootMessage
from src.globalNet.manager.Messages import MyMessages as GlMyMessages, OthersMessages as GlOthersMessages
from src.globalNet.Me import Me as GlMe
from src.globalNet.Node import Node as GlNode

from src.directNet.JobProcessor import JobProcessor as DiJobProcessor
from src.directNet.Node import Node as DiNode
from src.directNet.manager.CallNode import CallNode as DiCallNode
from src.directNet.model.Message import Message as DiMessage

from src.allNet.util import nodeTrans, timestamp
from src.Settings import Key, Settings

class _GlApi:
    _started:bool = False
    _startedLock:Lock = Lock()

    # Core
    @staticmethod
    def start() -> None:
        """Start Tune client/server of global net."""
        MyInfo.setKey(Settings.get(Key.PRIVATE_KEY))
        with _GlApi._startedLock:
            if _GlApi._started: return
            _GlApi._started = True

            MyNets.registerMyNet(GLOBAL_NET_NAME, MyNet(GlJobProcessor))

            Thread(target=MyNets.getMyNetByName(GLOBAL_NET_NAME).serve, daemon=True).start() 
            Thread(target=GlMe.syncer, daemon=True).start()
    @staticmethod
    def stop() -> None:
        """Stop Tune client/server of global net."""
        with _GlApi._startedLock:
            if not _GlApi._started: return
            _GlApi._started = False

            MyNets.unregisterMyNet(GLOBAL_NET_NAME)
            GlMe.stop()
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
        return GlNodes.registerNode(GlNode.nodeByNetNameAndIAndP(GLOBAL_NET_NAME, nodeTrans.nodeIAndPById(id)))
    @staticmethod
    def getTrafficByNode(node:GlNode) -> int:
        """Get traffic in bytes for a node."""
        return GlNodes.getNodeTraffic(node.getNodeInfo().ip)
    @staticmethod
    def banNodeByIp(ip:str) -> None:
        """Ban a node by IP address."""
        GlNodes.ban(ip)
        GlOthersMessages.deleteMessagesFromIp(ip)
    @staticmethod
    def banNodeById(nodeId:str) -> None:
        """Ban a node by Node ID."""
        try:
            ip = nodeTrans.separateNodeIAndP(nodeTrans.nodeIAndPById(nodeId))[0]
            Api.banNodeByIp(ip)
        except Exception:
            pass
    @staticmethod
    def unbanNodeByIp(ip:str) -> None:
        """Unban a node by IP address."""
        GlNodes.unban(ip)
    @staticmethod
    def unbanNodeById(nodeId:str) -> None:
        """Unban a node by Node ID."""
        try:
            Api.unbanNodeByIp(nodeTrans.separateNodeIAndP(nodeTrans.nodeIAndPById(nodeId))[0])
        except Exception:
            pass
    
    # Messages
    @staticmethod
    def getAllMessages() -> Iterable[GlRootMessage | GlReplyMessage]:
        """Get all messages.(include my messages)"""
        return chain(GlOthersMessages.getMessages(), GlMyMessages.getMessages())
    @staticmethod
    def getAllRootMessages() -> Iterable[GlRootMessage]:
        """Get all root messages.(include my messages)"""
        return chain(GlOthersMessages.getRootMessages(), GlMyMessages.getRootMessages())
    @staticmethod
    def getAllReplyMessages() -> Iterable[GlReplyMessage]:
        """Get all reply messages.(include my messages)"""
        return chain(GlOthersMessages.getReplyMessages(), GlMyMessages.getReplyMessages())
    @staticmethod
    def getReplyMessagesByRootMessage(rootMsg:GlRootMessage) -> list[GlReplyMessage]:
        """Get all reply messages for a root message."""
        return [msg for msg in Api.getAllReplyMessages() if msg.fromHash == rootMsg.hash()]
    # Message
    @staticmethod
    def postRootMessage(content:str) -> None:
        """Post a new root message."""
        GlMyMessages.addMessage(GlRootMessage(content=content, timestamp=timestamp.now()))
    @staticmethod
    def postReplyMessage(rootMsg:GlRootMessage, content:str) -> int:
        """
        Post a new reply message to a root message.

        Return codes:
        0: Success
        1: The original message has no author or the author's public key is missing.
        2: The original message is a reply message, cannot reply to a reply.
        3: The root message does not exist in MyMessages, cannot reply.
        """
        if not rootMsg.author or not rootMsg.author.getNodeInfo().pubKey: return 1
        elif isinstance(rootMsg, GlReplyMessage): return 2
        elif GlMyMessages.getMessageByHash(rootMsg.hash()): return 3
        if "y" in Settings.get(Key.COPY_REPLY_FROM_MSGS).lower():
            GlMyMessages.addDelegateMessage(rootMsg)
            fromNode = GlNodes.getNodeOrGenerateByIAndPOrPubKey(Settings.get(Key.IMYME_ADDR), rootMsg.author.getNodeInfo().pubKey)
        else:
            fromNode = rootMsg.author
        GlMyMessages.addMessage(GlReplyMessage(content=content, timestamp=timestamp.now(), fromHash=rootMsg.hash(), fromNode=fromNode))
        return 0

class _DiApi:
    _started:bool = False
    _startedLock:Lock = Lock()

    # Core
    @staticmethod
    def start() -> None:
        """Start Tune client/server of direct net."""
        MyInfo.setKey(Settings.get(Key.PRIVATE_KEY))
        with _DiApi._startedLock:
            if _DiApi._started: return
            _DiApi._started = True

            MyNets.registerMyNet(DIRECT_NET_NAME, MyNet(DiJobProcessor))

            Thread(target=MyNets.getMyNetByName(DIRECT_NET_NAME).serve, daemon=True).start()
    @staticmethod
    def stop() -> None:
        """Stop Tune client/server of direct net."""
        if n := DiCallNode.getNode():
            n.stopMessages()
            n.stopVc()
        with _DiApi._startedLock:
            if not _DiApi._started: return
            _DiApi._started = False

            MyNets.unregisterMyNet(DIRECT_NET_NAME)

    @staticmethod
    def matchNodeByNodeId(nodeId:str, amISubject:bool=False) -> bool:
        """Send a direct invitation to a node on the global network and connect if it is accepted."""
        if not (glNode := GlNodes.getNodeById(nodeId)):
            return False
        dlNode:DiNode = DiNode.getNodeFromAll(glNode)
        DiCallNode.setNodeByNodeInfo(dlNode.getNodeInfo())
        if not amISubject: dlNode.inviteToGlobalNode()
        d = 0.1
        for _ in range(Settings.getInt(Key.DIRECT_VC_HELLO_TIMEOUT_SEC)/d): 
            if dlNode.canSendAndRecv():
                break
            time.sleep(d)
        if not dlNode.canSendAndRecv():
            return False
        dlNode.hello()
        return True

    @staticmethod
    def stopMessages() -> None:
        """Stop receiving messages."""
        if n := DiCallNode.getNode():
            n.stopMessages()
    
    @staticmethod
    def stopVc() -> None:
        """Stop receiving voices."""
        if n := DiCallNode.getNode():
            n.stopVc()
    
    @staticmethod
    def sendMessage(msg:str) -> bool:
        """Send a message to the connected node."""
        if n := DiCallNode.getNode():
            return n.sendMessage(DiMessage(msg, timestamp.now()))
        return False
    
    @staticmethod
    def recvMessages() -> Generator[DiMessage, None, None]:
        """Receive messages from the connected node using a generator."""
        if n := DiCallNode.getNode():
            return n.recvMessages()
        return generatoot.emptyGenerator()

    @staticmethod
    def sendPCMVoicesByGenerator(pcmGen:Generator[bytes, None, None]) -> None:
        """Send PCM voice data to the connected node using a generator."""
        if n := DiCallNode.getNode():
            n.sendPCMVoicesByGenerator(pcmGen)
    
    @staticmethod
    def recvPCMVoices() -> Generator[bytes, None, None]:
        """Receive PCM voice data from the connected node using a generator."""
        if n := DiCallNode.getNode():
            return n.recvPCMVoices()
        return generatoot.emptyGenerator()

class Api:
    GlobalNet:_GlApi = _GlApi
    DirectNet:_DiApi = _DiApi

    @staticmethod
    def getMyName() -> str:
        return MyInfo.getName()
    @staticmethod
    def setMyName(name:str) -> None:
        MyInfo.setName(name)
    
    @staticmethod
    def getMyPubKey() -> str:
        return MyInfo.getPubKey()

def _init():
    MyInfo.setKey(Settings.get(Key.PRIVATE_KEY))
    MyInfo.setName(Settings.get(Key.MY_NAME))
    MyInfo.setRsaKey(Settings.get(Key.RSA_PRIVATE_KEY))
    MyInfo.setAudioConfig(Settings.getInt(Key.DIRECT_VC_FRAME_AND_BLOCK_SIZE), Settings.getInt(Key.DIRECT_VC_CHANNELS), Settings.getInt(Key.DIRECT_VC_SAMPLING_RATE))

_init()