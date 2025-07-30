from src.manager.Nodes import Nodes
from src.model.Message import Message, ReplyMessage
from src.model.NodeInfo import NodeInfo
from src.net.Me import Me

from src.net.Protocol import Response, CommuType
from src.util import ed25519


class Node:
    def __init__(self, nodeInfo:NodeInfo, me:Me):
        self._nodeInfo = nodeInfo
        self._me:Me = me
    @staticmethod
    def _nodeFromIAndP(iAndP:str, me:Me) -> "Node" | None:
        try:
            nIandPL = iAndP.split(":")
            ip = nIandPL[0]
            port = int(nIandPL[1])
            return Node(NodeInfo(ip, port, "", ""), me)
        except:
            return None
    def getNodeInfo(self) -> NodeInfo:
        return self._nodeInfo
    def _sendToAndRecv(self, data:dict) -> Response:
        return self._me.sendToAndRecv(data, self._nodeInfo.ip, self._nodeInfo.port)
    def hello(self) -> bool:
        resp = self._sendToAndRecv({"t":CommuType.HELLO, "d":{"name":self._me.getName(), "pub":self._me.getPubKey()}})
        if resp.respType != CommuType.RESPONSE:
            return False
        self._nodeInfo.name = resp.mainData["name"]
        self._nodeInfo.pubKey = resp.mainData["pub"]
        return True
    def getNodes(self) -> list["Node"]:
        resp = self._sendToAndRecv({"t":CommuType.GET_NODES, "d":{}})
        if resp.respType != CommuType.RESPONSE:
            return []
        nodes = []
        for nIAndP in resp.mainData.get("nodes", __default=[]):
            try:
                node = Node._nodeFromIAndP(nIAndP, self._me)
                if not node: raise
                nodes.append(node)
            except:
                pass
        return nodes
    def getRandomMessage(self) -> Message | ReplyMessage | None:
        resp = self._sendToAndRecv({"t": CommuType.GET_RAND_MESSAGE, "d":{}})
        if resp.respType != CommuType.RESPONSE:
            return None
        mData = resp.mainData
        try:
            c = mData["c"]
            ts = int(mData["ts"])
            if "from" in mData.keys():
                fromNode = Nodes.getNodeFromPubKey(mData["fromPub"])
                replyFromSafe = True
                if not fromNode:
                    node = Node._nodeFromIAndP(mData["from"], self._me)
                    if not node: return None
                    fromNode = node
                    fromNode.hello()
                    if fromNode.getNodeInfo().pubKey != mData["fromPub"]:
                         replyFromSafe = False
                    Nodes.registerNode(node)
                message = ReplyMessage(c, ts, fromNode, resp.mainData["fromHash"], fromSafe=replyFromSafe, author=self)
            else:
                message = Message(c, ts, author=self)
            if not ed25519.verify(message.hash(), mData["sig"], self._nodeInfo.pubKey):
                message = None
            return message
        except:
            return None
    def getMessage(self, messageHash:str=None) -> Message | ReplyMessage | None:
        if messageHash:
            req = {"t": CommuType.GET_MESSAGE, "d":{"hash":messageHash}}
        else:
            req = {"t": CommuType.GET_RAND_MESSAGE, "d":{}}
        resp = self._sendToAndRecv(req)
        if resp.respType != CommuType.RESPONSE:
            return None
        mData = resp.mainData
        try:
            c = mData["c"]
            ts = int(mData["ts"])
            if "from" in mData.keys():
                fromNode = Nodes.getNodeFromPubKey(mData["fromPub"])
                replyFromSafe = True
                if not fromNode:
                    node = Node._nodeFromIAndP(mData["from"], self._me)
                    if not node: return None
                    fromNode = node
                    fromNode.hello()
                    if fromNode.getNodeInfo().pubKey != mData["fromPub"]:
                        replyFromSafe = False
                    Nodes.registerNode(node)
                message = ReplyMessage(c, ts, fromNode, resp.mainData["fromHash"], fromSafe=replyFromSafe, author=self)
            else:
                message = Message(c, ts, author=self)
            if not ed25519.verify(message.hash(), mData["sig"], self._nodeInfo.pubKey):
                return None
            return message
        except:
            return None
    def getMessagesFromHashRecur(self, messageHash:str) -> list[Message | ReplyMessage] | None:
        m = self.getMessage(messageHash=messageHash)
        messages = [m]
        if not m:
            return []
        elif type(m) == ReplyMessage:
            messages += m.fromNode.getMessagesFromHashRecur(m.hash())
        return messages