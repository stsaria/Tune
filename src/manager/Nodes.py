from threading import RLock

from src.model.NodeInfo import NodeInfo
from src.net.Me import Me
from src.net.Node import Node

class Nodes:
    _me = None
    _nodes:list[NodeInfo] = []
    _nodesLock:RLock = RLock()
    @classmethod
    def setMe(cls, me:Me):
        cls._me = me
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
            if cls.getNodeFromIpAndPort(nodeInfo.ip, nodeInfo.port) or cls.getNodeFromPubKey(nodeInfo.pubKey):
                return
    @classmethod
    def getNodes(cls) -> list[Node]:
        nodes = []
        with cls._nodesLock:
            for nI in cls._nodes:
                nodes.append(Node(nI, cls._me))
        return nodes
    @classmethod
    def getNodesFromIp(cls, ip:str) -> list[Node]:
        nodes = []
        with cls._nodesLock:
            for nI in cls._nodes:
                if nI.ip != ip:
                    continue
                nodes.append(Node(nI, cls._me))
        return nodes
    @classmethod
    def getNodeFromIpAndPort(cls, ip:str, port:int) -> Node | None:
        with cls._nodesLock:
            for nI in cls._nodes:
                if nI.ip != ip or nI.port != port:
                    continue
                return Node(nI, cls._me)
        return None
    @classmethod
    def getNodeFromPubKey(cls, pubKey:str) -> Node | None:
        with cls._nodesLock:
            for nI in cls._nodes:
                if nI.pubKey != pubKey:
                    continue
                return Node(nI, cls._me)
        return None


