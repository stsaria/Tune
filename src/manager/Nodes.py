import random
from threading import Lock, RLock

from model.NodeInfo import NodeInfo
from src.Settings import Key, Settings
from src.net.Node import Node
from src.util import nodeTrans

class Nodes:
    _nodesByPubKey:dict[str, Node] = {}
    _nodesByIpPort:dict[tuple[str, int], Node] = {}
    _nodesLock:RLock = RLock()

    _bannedIps:set[str] = set()
    _bannedIpsLock:RLock = RLock()
    
    _bannedNodeIds:set[str] = set()
    _bannedNodeIdsLock:RLock = RLock()

    _trafficByteByIps:dict[str:int] = {}
    _trafficByteByIpsLock:Lock = Lock()
    @classmethod
    def registerNode(cls, node:Node) -> None:
        def rC(): return random.randint(0,255)
        if len(cls.getNodes()) >= Settings.getInt(Key.MAX_NODES):
            return
        key = node.getNodeInfo().pubKey
        ipPort = (node.getNodeInfo().ip, node.getNodeInfo().port)
        with cls._nodesLock:
            if ipPort in cls._nodesByIpPort:
                return
            node.updateUniqueColorRGB(rC(), rC(), rC())
            if key in cls._nodesByPubKey:
                oldNode = cls._nodesByPubKey[key]
                oldIpPort = (oldNode.ip, oldNode.port)
                cls._nodesByIpPort.pop(oldIpPort, None)
            cls._nodesByPubKey[key] = node
            cls._nodesByIpPort[ipPort] = node

    @classmethod
    def unregisterNode(cls, node:Node) -> None:
        nI = node.getNodeInfo()
        with cls._nodesLock:
            cls._nodesByPubKey.pop(nI.pubKey, None)
            cls._nodesByIpPort.pop((nI.ip, nI.port), None)
    @classmethod
    def removeNodeById(cls, nodeId:str) -> bool:
        try:
            ip, port = nodeTrans.separateNodeIAndP(nodeTrans.nodeIAndPFromId(nodeId))
            
            with cls._nodesLock:
                if (ip, port) in cls._nodesByIpPort:
                    cls._nodesByPubKey.pop(cls._nodesByIpPort[(ip, port)].getNodeInfo().pubKey, None)
                    cls._nodesByIpPort.pop((ip, port), None)
                    return True
            return False
        except:
            return False
    @classmethod
    def isBannedIp(cls, ip:str) -> bool:
        with cls._bannedIpsLock:
            return ip in cls._bannedIps
    @classmethod
    def banIp(cls, ip:str) -> None:
        with cls._bannedIpsLock:
            cls._bannedIps.add(ip)

    @classmethod
    def unbanIp(cls, ip:str) -> None:
        with cls._bannedIpsLock:
            cls._bannedIps.discard(ip)

    @classmethod
    def isBannedIp(cls, ip:str) -> bool:
        with cls._bannedIpsLock:
            return ip in cls._bannedIps

    @classmethod
    def banNodeId(cls, nodeId:str) -> None:
        with cls._bannedNodeIdsLock:
            cls._bannedNodeIds.add(nodeId)

    @classmethod
    def unbanNodeId(cls, nodeId:str) -> None:
        with cls._bannedNodeIdsLock:
            cls._bannedNodeIds.discard(nodeId)

    @classmethod
    def isBannedNodeId(cls, nodeId:str) -> bool:
        with cls._bannedNodeIdsLock:
            return nodeId in cls._bannedNodeIds

    @classmethod
    def getBannedNodeIds(cls) -> set[str]:
        with cls._bannedNodeIdsLock:
            return cls._bannedNodeIds.copy()

    @classmethod
    def getNodeFromPubKey(cls, pubKey:str) -> Node | None:
        with cls._nodesLock:
            return cls._nodesByPubKey.get(pubKey)

    @classmethod
    def getNodeFromIpAndPort(cls, ip:str, port:int) -> Node | None:
        with cls._nodesLock:
            return cls._nodesByIpPort.get((ip, port))

    @classmethod
    def getNodeFromId(cls, nodeId:str) -> Node | None:
        try:
            nodeInfo = nodeId.nodeIAndPFromId(nodeId)
            if not nodeInfo:
                return None
            ip, port = nodeInfo.split(':')
            port = int(port)
            return cls.getNodeFromIpAndPort(ip, port)
        except:
            return None

    @classmethod
    def getNodesFromIp(cls, ip:str) -> list[Node]:
        with cls._nodesLock:
            return [
                n for (i, p), n in cls._nodesByIpPort.items()
                if i == ip
            ]

    @classmethod
    def getNodes(cls) -> list[Node]:
        with cls._nodesLock:
            return list(cls._nodesByPubKey.values())

    @classmethod
    def getNodesFromRandom(cls, exclusionIp:str = None, sampleK:int = 1) -> list[Node]:
        with cls._nodesLock:
            candidates = [
                n
                for n in cls._nodesByPubKey.values()
                if (n.getNodeInfo().ip != exclusionIp)
            ]
        if len(candidates) <= sampleK:
            return candidates
        return random.sample(candidates, sampleK)

    @classmethod
    def traffic(cls, ip:str, size:int=None):
        with cls._trafficByteByIpsLock:
            if not size is None: cls._trafficByteByIps[ip] = cls._trafficByteByIps.get(ip, 0)+size
            return cls._trafficByteByIps.get(ip, 0)
    
    @classmethod
    def traffics(cls) -> dict[str, int]:
        with cls._trafficByteByIpsLock:
            return cls._trafficByteByIps.copy()
    
    @staticmethod
    def getNodeOrGenerateFromIAndPOrPubkey(nIAndP:str, pubKey:str) -> Node:
        separatedNIAndP = nodeTrans.separateNodeIAndP(nIAndP)
        return Nodes.getNodeFromIpAndPort(*separatedNIAndP) or Nodes.getNodeFromPubKey(pubKey) or Node(NodeInfo(separatedNIAndP[0], separatedNIAndP[1], "IDK", pubKey))