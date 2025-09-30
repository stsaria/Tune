from threading import Lock

from src.directNet.Node import Node

class CallNode:
    _node:Node = None
    _ipAndPort:tuple[str, int] = None
    _nodeLock:Lock = Lock()

    @classmethod
    def setNodeByNodeInfo(cls, node:Node) -> None:
        with cls._nodeLock:
            cls._node = node
            nI = node.getNodeInfo()
            cls._ipAndPort = (nI.ip, nI.port)
    @classmethod
    def getNode(cls) -> Node | None:
        with cls._nodeLock:
            return cls._node
    @classmethod
    def unsetNode(cls) -> None:
        with cls._nodeLock:
            cls._node = None
            cls._ipAndPort = None
    @classmethod
    def getIpAndPort(cls) -> tuple[str, int] | None:
        with cls._nodeLock:
            return cls._ipAndPort