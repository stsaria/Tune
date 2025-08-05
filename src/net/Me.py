import json
import time
import traceback
import uuid
from socket import socket as Socket
from socket import AF_INET, SOCK_DGRAM
from threading import Lock, Thread

from src.manager.Messages import Messages
from src.manager.MyMessages import MyMessages
from src.manager.Nodes import Nodes
from src.model.Message import ReplyMessage, RootMessage
from src.model.NodeInfo import NodeInfo
from src.net import Node
from src.net.AdvNode import AdvNode
from src.net.Protocol import Response
from src.net.Protocol import ResponseIdentify, CommuType
from src.util import ed25519, nettet
from src.util import nodeId


class Me:
    _ip:str = "0.0.0.0"
    _port:int = nettet.selectPort(1024, 65535)

    _sock:Socket = Socket(AF_INET, SOCK_DGRAM)
    _sock.bind((_ip, _port))

    _responses:dict[ResponseIdentify: Response] = {}
    _responsesLock:Lock = Lock()

    _buffer:int = 1024*1024

    _name = ""

    hexs = ed25519.generate()
    _pivKey:str = hexs[0]
    _pubKey:str = hexs[1]
    @classmethod
    def getIp(cls) -> str:
        return cls._ip
    @classmethod
    def getPort(cls) -> int:
        return cls._port
    @classmethod
    def getName(cls) -> str:
        return cls._name
    @classmethod
    def setName(cls, name:str):
        cls._name = name
    @classmethod
    def sockClose(cls):
        cls._sock.close()
    @classmethod
    def getPubKey(cls) -> str:
        return cls._pubKey
    @classmethod
    def _getResp(cls, identify:ResponseIdentify) -> Response | None:
        with cls._responsesLock:
            for k, v in cls._responses.items():
                resp:Response = v
                if k == identify.hash():
                    return resp
        return None
    @classmethod
    def _addResp(cls, identify:ResponseIdentify, resp:Response):
        with cls._responsesLock:
            cls._responses[identify.hash()] = resp
    @classmethod
    def sendToAndRecv(cls, data:dict, toIp:str, toPort:int, timeOut:int=4) -> Response:
        try:
            identify:ResponseIdentify = ResponseIdentify(toIp, toPort, uuid.uuid4().hex)
            data["id"] = identify.respId
            if type(data["t"]) == CommuType: data["t"] = data["t"].value
            cls._sock.sendto(json.dumps(data).encode("utf-8"), (toIp, toPort))

            st = time.time()
            while time.time()-st < timeOut:
                resp = cls._getResp(identify)
                if resp:
                    return resp
                time.sleep(0.03)
            return Response(CommuType.LOC_TIME_OUTED, {})
        except:
            return Response(CommuType.LOC_ERROR, {})
    @classmethod
    def __hello(cls, mData:dict, addr:tuple[str, int]) -> dict:
        Nodes.registerNode(NodeInfo(addr[0], addr[1], mData["name"], mData["pub"]))
        return {"name":cls._name, "pub":cls._pubKey}
    @classmethod
    def __getNodes(cls, addr:tuple[str, int]) -> dict:
        nodes = Nodes.getNodesFromRandom(exclusionIp=addr[0], sampleK=13)
        return {"nodes": [n.getNodeInfo().getIPColonPort() for n in nodes]}
    @classmethod
    def __getMessage(cls) -> dict:
        message = MyMessages.getRandomMessage()
        h = message.hash()
        m = {"c":message.content, "ts":message.timestamp, "hash":h, "sig": ed25519.sign(h, cls._pivKey)}
        if type(message) == ReplyMessage:
            fNI = message.fromNode.getNodeInfo()
            m["from"] = fNI.getIpColonPort()
            m["fromPub"] = fNI.pubKey
            m["fromHash"] = message.fromHash
        return m

    @classmethod
    def _allotTaskFromReq(cls, data:dict, addr:tuple[str, int]) -> None:
        r:dict = {"t":CommuType.RESPONSE.value, "d":{}, "id":data["id"]}
        match data["t"]:
            case CommuType.HELLO.value:
                r["d"] = cls.__hello(data["d"], addr)
            case CommuType.GET_NODES.value:
                r["d"] = cls.__getNodes(addr)
            case CommuType.GET_RAND_MESSAGE.value:
                r["d"] = cls.__getMessage()
            case CommuType.RESPONSE.value:
                resType: CommuType | None = None
                for e in CommuType:
                    if e.value == data["t"]: resType = e
                if not resType: return
                cls._addResp(ResponseIdentify(addr[0], addr[1], data["id"]), Response(resType, data["d"]))
                return
            case CommuType.PING.value:
                pass
            case _:
                r["t"] = CommuType.ERR_I_DONT_KNOW_YOUR_REQ_TYPE.value
        cls._sock.sendto(json.dumps(r).encode("utf-8"), addr)
    @classmethod
    def serve(cls) -> None:
        while True:
            try:
                d, a = cls._sock.recvfrom(cls._buffer)
                jS = d.decode("utf-8")
                j:dict = json.loads(jS)
                for k, v in {"t":int, "d":dict, "id":str}.items():
                    if type(j[k]) != v:
                        raise
                cls._allotTaskFromReq(j, a)
            except:
                pass
    @classmethod
    def _syncNewNodeFromNode(cls, node:Node):
        for n in node.getNodes():
            Nodes.registerNode(n)
    @classmethod
    def _syncNode(cls, node:Node) -> bool:
        if not node.ping():
            return False
        aN = AdvNode(node)
        Thread(target=cls._syncNewNodeFromNode, args=(node,)).start()
        for i in range(16):
            m = aN.getMessage()
            if not m: continue
            Messages.addMessage(m)
            if type(m) != ReplyMessage:
                continue
            for rM in aN.getMessagesFromHashRecur(m.fromHash):
                Messages.addMessage(rM)
        return True
    
    @classmethod
    def dumpMessages(cls, maxMsgS:int=1000, maxReplyRatio:float=1/3, minMsgSize:int=10, expirationSecS:int=3*3600):
        sortedMsgS = sorted([m for m in Messages.getMessages()], key=lambda m: m.timestamp)
        def d(m): Messages.deleteMessage(m)
        def dByMax(sMS,maXR,t,maX=None):
            sMS = [m for m in sMS if isinstance(m, t)]
            l = len(sMS)
            maX = maX if maX else l*maXR
            if l > maX:
                for m in sMS[:l-maX]:
                    d(m)
        for m in Messages.getMessages():
            if len(m.content) < minMsgSize or int(time.time()) - m.timestamp > expirationSecS:
                d(m)
        dByMax(sortedMsgS, maxReplyRatio, ReplyMessage)
        dByMax(sortedMsgS, 1, (ReplyMessage | RootMessage), maX=maxMsgS)
    @classmethod
    def syncer(cls, loopDelay:int=40) -> None:
        while True:
            for n in Nodes.getNodes():
                try:
                    r = cls._syncNode(n)
                    if not r: Nodes.unregisterNode(n)
                    cls.dumpMessages()
                except:
                    pass
                    print(traceback.format_exc())
            for m in Messages.getRootMessages():
                print(m.hash())
            print(Nodes.getNodes())
            time.sleep(loopDelay)
    @classmethod
    def _getMyIPColonPort(cls) -> str | None:
        nodes = Nodes.getNodesFromRandom(sampleK=5)
        if len(nodes) == 0:
            return None
        ipColonPorts = [n.getMyIpColonPort() for n in nodes]
        if not all(ipColonPorts) or not ipColonPorts[0]:
            return None
        return ipColonPorts[0]
    @classmethod
    def getMyId(cls) -> str | None:
        ipColonPort = cls._getMyIPColonPort()
        if not ipColonPort:
            return None
        return nodeId.idFromNodeIAndP(ipColonPort)