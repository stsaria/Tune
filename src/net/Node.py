from typing import Any, Generator, Optional

from src.model.NodeInfo import NodeInfo

from src.net.Protocol import Response, CommuType
from src.util import nodeTrans

class Node:
    def __init__(self, nodeInfo:NodeInfo):
        self._nodeInfo = nodeInfo
        self._uniqueColorRGB:tuple[int, int, int] = (0, 0, 0)    
    @staticmethod
    def nodeFromIAndP(iAndP:str) -> Optional["Node"]:
        try:
            return Node(NodeInfo(*nodeTrans.separateNodeIAndP(iAndP), "", ""))
        except:
            return None
    def getNodeInfo(self) -> NodeInfo:
        return self._nodeInfo
    def sendToAndRecv(self, data:dict) -> Response:
        from src.net.Me import Me
        return Me.sendToAndRecv(data, self._nodeInfo.ip, self._nodeInfo.port)
    def hello(self) -> bool:
        from src.net.Me import Me
        resp = self.sendToAndRecv({"t":CommuType.HELLO, "d":{"name":Me.getName(), "pub":Me.getPubKey()}})
        if resp.respType != CommuType.RESPONSE:
            return False
        self._nodeInfo.name = resp.mainData["name"]
        self._nodeInfo.pubKey = resp.mainData["pub"]
        return True
    def getNodes(self) -> Generator["Node", Any, list[Any] | None]:
        resp = self.sendToAndRecv({"t":CommuType.GET_NODES, "d":{}})
        if resp.respType != CommuType.RESPONSE:
            return []
        for nIAndP in resp.mainData.get("nodes", []):
            try:
                node = Node.nodeFromIAndP(nIAndP)
                if not node: raise
                yield node
            except:
                pass
    def ping(self) -> bool:
        resp = self.sendToAndRecv({"t":CommuType.PING, "d":{}})
        return True if resp.respType == CommuType.RESPONSE else False
    def updateUniqueColorRGB(self, r:int, g:int, b:int) -> None:
        self._uniqueColorRGB = (int(r), int(g), int(b))
    def getUniqueColorRGB(self) -> tuple[int, int, int]:
        return self._uniqueColorRGB