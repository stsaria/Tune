import random
from typing import Any, Generator, Optional

from src.base.manager.MyInfo import MyInfo
from src.base.ServerAndClient import ServerAndClient
from src.Settings import Settings, Key
from src.base.model.NodeInfo import NodeInfo

from src.base.Protocol import CommuType
from src.base.model.Response import Response
from src.base.util import nodeTrans, timestamp

class Node:
    def __init__(self, serverAndClient:ServerAndClient, nodeInfo:NodeInfo, uniqueColorRGB:tuple[int, int, int]=None, startTime:int=None, expireTime:int=None):
        self._serverAndClient:ServerAndClient = serverAndClient
        self._nodeInfo:NodeInfo = nodeInfo
    @staticmethod
    def nodeFromIAndP(iAndP:str) -> Optional["Node"]:
        try:
            return Node(NodeInfo(*nodeTrans.separateNodeIAndP(iAndP), "", ""))
        except:
            return None
    def getNodeInfo(self) -> NodeInfo:
        return self._nodeInfo
    def sendToAndRecv(self, data:dict) -> Response:
        self._serverAndClient.sendToAndRecv(data, self._nodeInfo.ip, self._nodeInfo.port)
    def hello(self) -> bool:
        resp = self.sendToAndRecv({"t":CommuType.HELLO, "d":{"name":MyInfo.getName(), "pub":MyInfo.getPubKey()}})
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
    def getStartTime(self) -> int:
        return self._startTime
    def getExpireTime(self) -> int:
        return self._expireTime