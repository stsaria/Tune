import json
from threading import Thread
from typing import Generator

from src.directNet.manager.Messages import Messages
from src.directNet.manager.Voices import Voices
from src.allNet.manager.MyInfo import MyInfo
from src.allNet.util import rsa
from src.allNet.model.Response import Response, ResponseIdentify
from src.directNet.model.Message import Message
from src.allNet.ExecOp import ExecOp
from src.allNet.Protocol import CommuType
from src.directNet.manager.CallNode import CallNode
from src.allNet.JobProcessor import JobProcessor as OrgJobProcessor
from src.allNet.util import ed25519

class JobProcessor(OrgJobProcessor):
    _messagesGenerator:Generator[Message, None, None] = None
    _voicesGenerator:Generator[bytes, None, None] = None
    
    @classmethod
    def _dDataByEncrypted(cls, encrypted:str) -> dict | None:
        try:
            return json.loads(rsa.decrypt(encrypted, MyInfo.getRsaPivKey(), conversionStr=True))
        except Exception:
            return

    @classmethod
    def __hello(cls, mData:dict) -> None:
        if not ed25519.verify(mData["pub"], mData["pubSig"], CallNode.getPubKey()):
            return
        n = CallNode.getNode()
        if not n: return
        cNI = n.getCallNodeInfo()
        cNI.setRsaPubKey(mData["pub"])
        cNI.setSamplingRate(mData["fRate"])
        cNI.setChannels(mData["chs"])
        cNI.setFrameSize(mData["fSize"])
    @classmethod
    def __sendMessage(cls, mData:dict) -> None:
        cls._messagesGenerator.send(Message(str(mData["c"]), int(mData["ts"])))
    @classmethod
    def __sendVoice(cls, mData:dict) -> None:
        cls._voicesGenerator.send(bytes.fromhex(mData["c"]))
            
    @classmethod
    def _allotTaskFromReq(cls, data:dict, addr:tuple[str, int]) -> None:
        match data["t"]:
            case CommuType.HELLO.value:
                cls.__hello(data["d"])
            case CommuType.SEND_MESSAGE.value:
                decrypted = cls._dDataByEncrypted(data["d"])
                if not decrypted: return
                cls.__sendMessage(decrypted)
            case CommuType.SEND_VOICE.value:
                decrypted = cls._dDataByEncrypted(data["d"])
                if not decrypted: return
                cls.__sendVoice(decrypted)
            case CommuType.RESPONSE.value:
                resType: CommuType | None = None
                for e in CommuType:
                    if e.value == data["t"]: resType = e
                if not resType: return 
                return (ExecOp.RESP, (ResponseIdentify(addr[0], addr[1], data["id"]), Response(resType, data["d"])))
    @classmethod
    def recved(cls, data, addr) -> tuple[ExecOp, dict] | None:
        if addr == CallNode.getIpAndPort():
            raise
        cls._allotTaskFromReq(data, addr)

    @classmethod
    def startRecver(cls) -> None:
        Thread(target=Messages.recv, args=(cls._messagesGenerator,), daemon=True).start()
        Thread(target=Voices.recv, args=(cls._voicesGenerator,), daemon=True).start()

JobProcessor.startRecver()
