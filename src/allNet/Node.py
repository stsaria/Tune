import random
from typing import Any, Generator, Optional

from src.allNet.MyNet import MyNet
from src.allNet.manager.MyNets import MyNets
from src.allNet.manager.MyInfo import MyInfo
from src.allNet.ServerAndClient import ServerAndClient
from src.Settings import Settings, Key
from src.allNet.model.NodeInfo import NodeInfo

from src.allNet.Protocol import CommuType
from src.allNet.model.Response import Response
from src.allNet.util import nodeTrans, timestamp

class Node:
    def __init__(self, netName:str, nodeInfo:NodeInfo):
        self._netName:str = netName
        self._net:MyNet = MyNets.getMyNetByName(netName)
        self._nodeInfo:NodeInfo = nodeInfo
    @staticmethod
    def nodeByNetNameAndIAndP(netName:str, iAndP:str) -> Optional["Node"]:
        try:
            return Node(netName, NodeInfo(*nodeTrans.separateNodeIAndP(iAndP), "", ""))
        except Exception:
            return None
    @classmethod
    def getNodeFromAll(cls, node:"Node") -> "Node":
        return cls(node.getNetName(), node.getNodeInfo())
    def getNetName(self) -> str:
        return self._netName
    def getNodeInfo(self) -> NodeInfo:
        return self._nodeInfo
    def sendToAndRecvDirect(self, data:dict) -> Response:
        return self._net.sendToAndRecv(data, self._nodeInfo.ip, self._nodeInfo.port)
    def sendToAndRecv(self, commuType:CommuType, mainData:dict | list | str | int) -> Response:
        return self.sendToAndRecvDirect({"t":commuType.value, "d":mainData})
    def sendToDirect(self, data:dict) -> None:
        self._net.sendTo(data, self._nodeInfo.ip, self._nodeInfo.port)
    def sendTo(self, commuType:CommuType, mainData:dict | list | str | int) -> None:
        self.sendTo({"t":commuType.value, "d":mainData})
    def hello(self, pubKey:str=None) -> bool:
        resp = self.sendToAndRecv(CommuType.HELLO, {"name":MyInfo.getName(), "pub":pubKey or MyInfo.getPubKey()})
        if resp.respType != CommuType.RESPONSE:
            return False
        try:
            self._nodeInfo.name = resp.mainData["name"]
            self._nodeInfo.pubKey = resp.mainData["pub"]
            return True
        except Exception:
            return False
    def ping(self) -> bool:
        resp = self.sendToAndRecv(CommuType.PING, {})
        return True if resp.respType == CommuType.RESPONSE else False