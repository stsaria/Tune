import base64
import json
import random
from threading import RLock

from src.model.NodeInfo import NodeInfo
from src.net.Node import Node

class Nodes:
    _me = None
    _nodes:list[NodeInfo] = []
    _nodesLock:RLock = RLock()
    @classmethod
    def registerNode(cls, node:Node | NodeInfo) -> None:
        t = type(node)
        if t == Node:
            nodeInfo = node.getNodeInfo()
        elif t == NodeInfo:
            nodeInfo = node
        else:
            return
        with cls._nodesLock:
            if cls.getNodeFromIpAndPort(nodeInfo.ip, nodeInfo.port):
                return
            n = cls.getNodeFromPubKey(nodeInfo.pubKey)
            if n:
                cls._nodes.remove(n.getNodeInfo())
            cls._nodes.append(nodeInfo)
    @classmethod
    def unregisterNode(cls, node:Node | NodeInfo):
        t = type(node)
        if t == Node:
            nodeInfo = node.getNodeInfo()
        elif t == NodeInfo:
            nodeInfo = node
        else:
            return
        with cls._nodesLock:
            cls._nodes.remove(nodeInfo)
    @classmethod
    def getNodes(cls) -> list[Node]:
        nodes = []
        with cls._nodesLock:
            for nI in cls._nodes:
                nodes.append(Node(nI))
        return nodes
    @classmethod
    def getNodesFromIp(cls, ip:str) -> list[Node]:
        nodes = []
        for n in cls.getNodes():
            nI = n.getNodeInfo()
            if nI.ip != ip:
                continue
            nodes.append(Node(nI))
        return nodes
    @classmethod
    def getNodeFromIpAndPort(cls, ip:str, port:int) -> Node | None:
        for n in cls.getNodes():
            nI = n.getNodeInfo()
            if nI.ip != ip or nI.port != port:
                continue
            return Node(nI)
        return None
    @classmethod
    def getNodeFromPubKey(cls, pubKey:str) -> Node | None:
        for n in cls.getNodes():
            nI = n.getNodeInfo()
            if nI.pubKey != pubKey:
                continue
            return Node(nI)
        return None
    @classmethod
    def getNodesFromRandom(cls, exclusionIp:str=None, sampleK:int=1) -> list[Node]:
        nodes = cls.getNodes()
        for n in nodes:
            if n.getNodeInfo().ip == exclusionIp: nodes.remove(n)
        if len(nodes) < sampleK:
            return nodes
        return random.sample(nodes, sampleK)