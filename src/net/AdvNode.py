import traceback
from typing import Generator, Any

from src.manager.Messages import OthersMessages
from src.Settings import Key, Settings
from src.manager.Nodes import Nodes
from src.model.Message import ReplyMessage, RootMessage
from src.net.Node import Node
from src.net.Protocol import CommuType
from src.util import ed25519
from src.typeDefined import MSG, MSGS
from src.util import msg


class AdvNode:
    def __init__(self, node:Node):
        self._node = node
    def getNodes(self) -> Generator["Node", Any, list[Any] | None]:
        resp = self._node.sendToAndRecv({"t":CommuType.GET_NODES, "d":{}})
        if resp.respType != CommuType.RESPONSE:
            return []
        for nIAndP in resp.mainData.get("nodes", __default=[]):
            try:
                n = Node.nodeFromIAndP(nIAndP)
                if not n: raise
                yield n
            except:
                pass
    def getMessage(self, messageHash:str=None, isDelegate:bool=False) -> MSG | None:
        if messageHash:
            req = {"t": CommuType.GET_MESSAGE, "d":{"hash":messageHash}}
        elif messageHash and isDelegate and delegatePub:
            req = {"t": CommuType.GET_DELEGATE_MESSAGE, "d":{"hash":messageHash}}
        else:
            req = {"t": CommuType.GET_RAND_MESSAGE, "d":{}}
        resp = self._node.sendToAndRecv(req)
        if resp.respType != CommuType.RESPONSE:
            print(req, resp.respType, resp.mainData)
            return None
        mData = resp.mainData
        try:
            c = mData["c"]
            ts = int(mData["ts"])
            if "from" in mData.keys():
                if mData["from"] == Settings.get(Key.IMYME_ADDR):
                    fromNode = self._node
                    isFromDelegate = True
                else:
                    fromNode = Nodes.getNodeFromPubKey(mData["fromPub"])
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
                message = ReplyMessage(content=c, timestamp=ts, fromNode=fromNode, fromHash=resp.mainData["fromHash"], author=self._node, isFromDelegate=isFromDelegate)
                pass
            else:
                message = RootMessage(content=c, timestamp=ts, author=self._node)
            if not ed25519.verify(message.hash(), mData["sig"], (mData["dgPub"] if isDelegate else self._node.getNodeInfo().pubKey)):
                return None
            return message
        except:
            print(traceback.format_exc())
            return None
    def getMyIpColonPort(self) -> str | None:
        from src.net.Me import Me
        resp = self._node.sendToAndRecv({"t":CommuType.GET_MY_IP_AND_PORT, "d":{}})
        if resp.respType != CommuType.RESPONSE:
            return None
        ipColonPort = resp.mainData["ipColonPort"]
        if not ed25519.verify(ipColonPort, resp.mainData["sig"], self._node.getNodeInfo().pubKey):
            return None
        return ipColonPort
    def addAndGetMsg(self, h=None, iD=False):
        m = self.getMessage(messageHash=h, isDelegate=iD)
        if not m: return
        elif msg.isNeedDumpMessage(m): return
        OthersMessages.addMessage(m)
        return m
    def syncNode(self) -> bool:
        if not self._node.ping():
            Nodes.unregisterNode(self._node)
        for n in self._node.getNodes():
            Nodes.registerNode(n)
        for _ in range(Settings.getInt(Key.MEESAGES_PER_NODE)):
            m = self.addAndGetMsg()
            if isinstance(m, ReplyMessage):
                if m.isFromDelegate: self.addAndGetMsg(h=m.fromHash, iD=True)
                elif m.fromNode: AdvNode(m.fromNode).addAndGetMsg(h=m.fromHash)
        return True