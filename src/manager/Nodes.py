import random
from threading import RLock

from src.model.NodeInfo import NodeInfo
from src.net.Node import Node
from src.util import nodeId

class Nodes:
    _nodesByPubKey: dict[str, NodeInfo] = {}
    _nodesByIpPort: dict[tuple[str, int], NodeInfo] = {}
    _nodesLock: RLock = RLock()

    _bannedIps: set[str] = set()
    _bannedIpsLock: RLock = RLock()
    
    _bannedNodeIds: set[str] = set()
    _bannedNodeIdsLock: RLock = RLock()

    @classmethod
    def registerNode(cls, node: Node | NodeInfo) -> None:
        from src.net.Me import Me
        if len(cls.getNodes()) >= Me.getMaxNodes():
            return
        nodeInfo = node.getNodeInfo() if isinstance(node, Node) else node
        if not isinstance(nodeInfo, NodeInfo):
            return
        key = nodeInfo.pubKey
        ipPort = (nodeInfo.ip, nodeInfo.port)
        with cls._nodesLock:
            if ipPort in cls._nodesByIpPort:
                return
            if key in cls._nodesByPubKey:
                oldNode = cls._nodesByPubKey[key]
                oldIpPort = (oldNode.ip, oldNode.port)
                cls._nodesByIpPort.pop(oldIpPort, None)
            cls._nodesByPubKey[key] = nodeInfo
            cls._nodesByIpPort[ipPort] = nodeInfo

    @classmethod
    def unregisterNode(cls, node: Node | NodeInfo) -> None:
        nodeInfo = node.getNodeInfo() if isinstance(node, Node) else node
        if not isinstance(nodeInfo, NodeInfo):
            return
        key = nodeInfo.pubKey
        ipPort = (nodeInfo.ip, nodeInfo.port)
        with cls._nodesLock:
            cls._nodesByPubKey.pop(key, None)
            cls._nodesByIpPort.pop(ipPort, None)

    @classmethod
    def removeNodeById(cls, nodeId: str) -> bool:
        try:
            nodeInfo = nodeId.nodeIAndPFromId(nodeId)
            if not nodeInfo:
                return False
            
            ip, port = nodeInfo.split(':')
            port = int(port)
            
            with cls._nodesLock:
                if (ip, port) in cls._nodesByIpPort:
                    nodeInfo = cls._nodesByIpPort[(ip, port)]
                    cls._nodesByPubKey.pop(nodeInfo.pubKey, None)
                    cls._nodesByIpPort.pop((ip, port), None)
                    return True
            return False
        except:
            return False

    @classmethod
    def banIp(cls, ip: str) -> None:
        with cls._bannedIpsLock:
            cls._bannedIps.add(ip)

    @classmethod
    def unbanIp(cls, ip: str) -> None:
        with cls._bannedIpsLock:
            cls._bannedIps.discard(ip)

    @classmethod
    def isBannedIp(cls, ip: str) -> bool:
        with cls._bannedIpsLock:
            return ip in cls._bannedIps

    @classmethod
    def banNodeId(cls, nodeId: str) -> None:
        with cls._bannedNodeIdsLock:
            cls._bannedNodeIds.add(nodeId)

    @classmethod
    def unbanNodeId(cls, nodeId: str) -> None:
        with cls._bannedNodeIdsLock:
            cls._bannedNodeIds.discard(nodeId)

    @classmethod
    def isBannedNodeId(cls, nodeId: str) -> bool:
        with cls._bannedNodeIdsLock:
            return nodeId in cls._bannedNodeIds

    @classmethod
    def getBannedNodeIds(cls) -> set[str]:
        with cls._bannedNodeIdsLock:
            return cls._bannedNodeIds.copy()

    @classmethod
    def getNodeFromPubKey(cls, pubKey: str) -> Node | None:
        with cls._nodesLock:
            nodeInfo = cls._nodesByPubKey.get(pubKey)
            return Node(nodeInfo) if nodeInfo else None

    @classmethod
    def getNodeFromIpAndPort(cls, ip: str, port: int) -> Node | None:
        with cls._nodesLock:
            nodeInfo = cls._nodesByIpPort.get((ip, port))
            return Node(nodeInfo) if nodeInfo else None

    @classmethod
    def getNodeFromId(cls, nodeId: str) -> Node | None:
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
    def getNodesFromIp(cls, ip: str) -> list[Node]:
        with cls._nodesLock:
            return [
                Node(nI) for (i, p), nI in cls._nodesByIpPort.items()
                if i == ip
            ]

    @classmethod
    def getNodes(cls) -> list[Node]:
        with cls._nodesLock:
            return [Node(nI) for nI in cls._nodesByPubKey.values()]

    @classmethod
    def getNodeInfos(cls) -> list[NodeInfo]:
        with cls._nodesLock:
            return list(cls._nodesByPubKey.values())

    @classmethod
    def getNodesFromRandom(cls, exclusionIp: str = None, sampleK: int = 1) -> list[Node]:
        with cls._nodesLock:
            candidates = [
                Node(nI)
                for nI in cls._nodesByPubKey.values()
                if nI.ip != exclusionIp
            ]
        if len(candidates) <= sampleK:
            return candidates
        return random.sample(candidates, sampleK)

    @classmethod
    def getMaxNodes(cls) -> int:
        from src.net.Me import Me
        return Me.getMaxNodes()

    @classmethod
    def setMaxNodes(cls, maxNodes: int) -> None:
        from src.net.Me import Me
        Me.setMaxNodes(maxNodes)