import random
from typing import Generator, Any

from src.globalNet.manager.Nodes import Nodes
from src.globalNet.manager.Messages import OthersMessages
from src.Settings import Key, Settings
from src.globalNet.model.Message import ReplyMessage, RootMessage
from src.base.Node import Node as OrgNode
from src.base.Protocol import CommuType
from src.util import ed25519
from globalNet.util import msg
from src.util import timestamp


class Node(OrgNode):
    def __init__(self, serverAndClient, nodeInfo, uniqueColorRGB = None, startTime = None, expireTime = None):
        super().__init__(serverAndClient, nodeInfo)
        self._uniqueColorRGB:tuple[int, int, int] = uniqueColorRGB or tuple([random.randint(0,255) for _ in range(3)]*3)
        self._startTime:int = startTime or timestamp.now()
        self._expireTime:int = expireTime or startTime+random.randint(Settings.getInt(Key.NODE_REPLACEMENT_INTERVAL_MIN), Settings.getInt(Key.NODE_REPLACEMENT_INTERVAL_MAX))
    @classmethod
    def fromOrginalNode(cls, node:OrgNode) -> "Node":
        return cls(node.getNodeInfo(), node.getUniqueColorRGB(), node.getStartTime(), node.getExpireTime())
    def getNodes(self, limit:int=5) -> Generator["Node", Any, list[Any] | None]:
        resp = self.sendToAndRecv({"t":CommuType.GET_NODES, "d":{}})
        if resp.respType != CommuType.RESPONSE:
            return []
        for nIAndP in resp.mainData.get("nodes", [])[0:limit]:
            try:
                n = Node.nodeFromIAndP(nIAndP)
                if not n: raise
                yield n
            except:
                pass
    def getMessage(self, messageHash:str=None, isDelegate:bool=False) -> ReplyMessage | RootMessage | None:
        if messageHash:
            req = {"t": CommuType.GET_MESSAGE, "d":{"hash":messageHash}}
        elif messageHash and isDelegate:
            req = {"t": CommuType.GET_DELEGATE_MESSAGE, "d":{"hash":messageHash}}
        else:
            req = {"t": CommuType.GET_RAND_MESSAGE, "d":{}}
        resp = self.sendToAndRecv(req)
        if resp.respType != CommuType.RESPONSE:
            return None
        mData = resp.mainData
        try:
            c = mData["c"]
            ts = int(mData["ts"])
            if "from" in mData.keys():
                if mData["from"] == Settings.get(Key.IMYME_ADDR):
                    fromNode = self
                    isFromDelegate = True
                else:
                    fromNode = Nodes.getNodeByPubKey(mData["fromPub"])
                    isFromDelegate = False
                if mData["from"] == Settings.get(Key.YOUYOURYOU_ADDR):
                    fromNode = None
                elif not fromNode:
                    n = Node.nodeFromIAndP(mData["from"])
                    if not n.hello():
                        return None
                    Nodes.registerNode(n)
                    if n.getNodeInfo().pubKey != mData["fromPub"]: return None
                    fromNode = n
                message = ReplyMessage(content=c, timestamp=ts, fromNode=fromNode, fromHash=resp.mainData["fromHash"], author=self, isFromDelegate=isFromDelegate)
                pass
            else:
                message = RootMessage(content=c, timestamp=ts, author=self)
            if not ed25519.verify(message.hash(), mData["sig"], (mData["dgPub"] if isDelegate else self.getNodeInfo().pubKey)):
                return None
            return message
        except:
            return None
    def getMyIpColonPort(self) -> str | None:
        resp = self.sendToAndRecv({"t":CommuType.GET_MY_IP_AND_PORT, "d":{}})
        if resp.respType != CommuType.RESPONSE:
            return None
        ipColonPort = resp.mainData["ipColonPort"]
        if not ed25519.verify(ipColonPort, resp.mainData["sig"], self.getNodeInfo().pubKey):
            return None
        return ipColonPort
    def addAndGetMsg(self, h=None, iD=False):
        m = self.getMessage(messageHash=h, isDelegate=iD)
        if not m: return
        elif msg.isNeedDumpMessage(m): return
        OthersMessages.addMessage(m)
        return m
    def syncNode(self) -> bool:
        if not self.ping() or (Nodes.getLength() >= Settings.getInt(Key.MIN_COUNT_FOR_NODE_REPLACEMENT_INTERVAL) and self.getExpireTime() >= timestamp.now()):
            Nodes.unregisterNode(self)
        for n in self.getNodes():
            Nodes.registerNode(n)
        for _ in range(Settings.getInt(Key.MEESAGES_PER_NODE)):
            m = self.addAndGetMsg()
            if isinstance(m, ReplyMessage):
                if m.isFromDelegate: self.addAndGetMsg(h=m.fromHash, iD=True)
                elif m.fromNode: Node.fromOrginalNode(m.fromNode).addAndGetMsg(h=m.fromHash)
        return True
    def updateUniqueColorRGB(self, r:int, g:int, b:int) -> None:
        self._uniqueColorRGB = (int(r), int(g), int(b))
    def getUniqueColorRGB(self) -> tuple[int, int, int]:
        return self._uniqueColorRGB
    def getStartTime(self) -> int:
        return self._startTime
    def getExpireTime(self) -> int:
        return self._expireTime