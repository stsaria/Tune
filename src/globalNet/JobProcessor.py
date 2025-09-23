import json

from src.base.ExecOp import ExecOp
from src.base.model import Response
from src.base.model.Response import ResponseIdentify
from src.base.Protocol import CommuType
from src.Settings import Key, Settings
from src.globalNet.model.Message import ReplyMessage
from src.globalNet.manager.Messages import MyMessages
from src.base.model.NodeInfo import NodeInfo
from src.defined import ENCODE
from src.globalNet.manager.Nodes import Nodes
from src.globalNet.Node import Node
from src.base.manager.MyInfo import MyInfo
from src.base.JobProcessor import JobProcessor as OrgJobProcessor
from src.util import ed25519


class JobProcessor(OrgJobProcessor):
    @classmethod
    def __hello(self, mData:dict, addr:tuple[str, int]) -> dict:
        Nodes.registerNode(Node(NodeInfo(addr[0], addr[1], mData["name"], mData["pub"])))
        return {"name":MyInfo.getName(), "pub":MyInfo.getPubKey()}
    @classmethod
    def __getNodes(self, addr:tuple[str, int]) -> dict:
        nodes = Nodes.getNodesByRandom(exclusionIp=addr[0], limit=13)
        return {"nodes": [n.getNodeInfo().getIPColonPort() for n in nodes]}
    @classmethod
    def __getMessage(self, addr:tuple[str, int], msgHash:str=None) -> dict:
        message = MyMessages.getMessageByHash(msgHash) if msgHash else MyMessages.getRandomMessage()
        h = message.hash()
        m = {"c":message.content, "ts":message.timestamp, "hash":h, "sig": ed25519.sign(h, MyInfo.getPivKey())}
        if isinstance(message, ReplyMessage):
            fNI = message.fromNode.getNodeInfo()
            if message.isFromDelegate: m["from"] = Settings.get(Key.IMYME_ADDR)
            else: m["from"] = Settings.get(Key.YOUYOURYOU_ADDR) if addr[0] == fNI.ip else fNI.getIPColonPort()
            m["fromPub"] = fNI.pubKey
            m["fromHash"] = message.fromHash
        return m
    @classmethod
    def __getDelegateMessage(self, msgHash:str) -> dict:
        dgMessage = MyMessages.getMessageByHash(msgHash, isDelegate=True)
        return {"c":dgMessage.content, "ts":dgMessage.timestamp, "hash":dgMessage.hash(), "sig": dgMessage.sig, "dgPub": dgMessage.delegatePub}
    @classmethod
    def _allotTaskFromReq(self, data:dict, addr:tuple[str, int]) -> tuple[ExecOp, any] | None:
        r:dict = {"t":CommuType.RESPONSE.value, "d":{}, "id":data["id"]}
        match data["t"]:
            case CommuType.HELLO.value:
                r["d"] = self.__hello(data["d"], addr)
            case CommuType.GET_NODES.value:
                r["d"] = self.__getNodes(addr)
            case CommuType.GET_RAND_MESSAGE.value:
                r["d"] = self.__getMessage(addr)
            case CommuType.RESPONSE.value:
                resType: CommuType | None = None
                for e in CommuType:
                    if e.value == data["t"]: resType = e
                if not resType: return 
                return (ExecOp.RESP, (ResponseIdentify(addr[0], addr[1], data["id"]), Response(resType, data["d"])))
            case CommuType.PING.value:
                pass
            case CommuType.GET_MY_IP_AND_PORT.value:
                r["d"] = {"ipColonPort":f"{addr[0]}:{addr[1]}", "sig":ed25519.sign(f"{addr[0]}:{addr[1]}", self._pivKey)}
            case CommuType.GET_MESSAGE.value:
                r["d"] = self.__getMessage(addr, data["d"]["hash"])
            case CommuType.GET_DELEGATE_MESSAGE.value:
                r["d"] = self.__getDelegateMessage(data["d"]["hash"])
            case _:
                r["t"] = CommuType.ERR_I_DONT_KNOW_YOUR_REQ_TYPE.value
        return ExecOp.SEND, r
    def recved(self, addr:tuple[int, int], data:bytes) -> ExecOp | dict:
        if Nodes.isBanned(addr[0]):
            raise
        Nodes.updateNodeTraffic(addr[0], data.__sizeof__())
        jS = data.decode(ENCODE)
        j:dict = json.loads(jS)
        for k, v in {"t":int, "d":dict, "id":str}.items():
            if not isinstance(j[k], v):
                raise
        r = self._allotTaskFromReq(j, addr)
        if not r: raise
        op, c = r
        return op, c