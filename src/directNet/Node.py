import json
from threading import Lock, Thread
import time
from typing import Generator
from numpy import empty
from opuslib import APPLICATION_AUDIO as OPUS_APPLICATION_AUDIO, Encoder as OpusEncoder, Decoder as OpusDecoder

from src.allNet.util import generatoot
from src.directNet.manager.Messages import Messages
from src.directNet.manager.Voices import Voices
from src.Settings import Settings, Key
from src.directNet.manager.CallNodeInfo import CallNodeInfo
from src.allNet.manager.MyInfo import MyInfo
from src.allNet.Protocol import CommuType
from src.allNet.model.NodeInfo import NodeInfo
from src.allNet.Node import Node as OrgNode
from src.allNet.util import ed25519, rsa
from src.directNet.model.Message import Message

VOICE, MESSAGE = 1, 0

class Node(OrgNode):
    def __init__(self, netName:str, nodeInfo:NodeInfo, frameAndBlockSize:int=Settings.getInt(Key.DIRECT_VC_FRAME_AND_BLOCK_SIZE), channels:int=Settings.getInt(Key.DIRECT_VC_CHANNELS), samplingRate:int=Settings.getInt(Key.DIRECT_VC_SAMPLING_RATE)):
        super().__init__(netName, nodeInfo)
        self._isStopedVc:bool = False
        self._isStopedVcLock:Lock = Lock()

        self._isStopedMessages:bool = False
        self._isStopedMessagesLock:Lock = Lock()

        self._callNodeInfo:CallNodeInfo = CallNodeInfo()

    def getCallNodeInfo(self) -> CallNodeInfo:
        return self._callNodeInfo

    def inviteToGlobalNode(self) -> None:
        self.sendToAndRecv(CommuType.INVITE_TO_DIRECT_NET, {})

    def hello(self) -> None:
        self.sendTo(CommuType.HELLO, {
            "pub":rsa.getPubKeyByPivKey(MyInfo.getRsaPivKey),
            "pubSig":ed25519.sign(MyInfo.getRsaPubKey(), MyInfo.getPubKey()),
            "fSize":MyInfo.getFrameAndBlockSize(),
            "chs":MyInfo.getChannels(),
            "fRate":MyInfo.getSamplingRate()
        })

    def canSendAndRecv(self) -> bool:
        return self._callNodeInfo.rsaPubKey and self._callNodeInfo.frameSize and self._callNodeInfo.channels

    def sendToEncrypted(self, commuType:CommuType, dData:dict) -> bool:
        pubKey = self._callNodeInfo.rsaPubKey
        if not pubKey: return False
        self.sendTo(commuType, rsa.encrypt(json.dumps(dData), pubKey))
        return True
    
    def stopMessages(self) -> None:
        with self._isStopedMessagesLock:
            self._isStopedMessages = True

    def stopVc(self) -> None:
        with self._isStopedVcLock:
            self._isStopedVc = True

    def _generatorStoper(self, t:int, gen:Generator):
        while True:
            with (self._isStopedVcLock if t else self._isStopedMessagesLock):
                if (self._isStopedVc if t else self._isStopedMessages):
                    try:
                        gen.close()
                    except RuntimeError:
                        pass
                    break
            time.sleep(0.02)

    def sendMessage(self, msg:Message) -> bool:
        if not self.canSendAndRecv():
            return False
        return self.sendToEncrypted(CommuType.SEND_MESSAGE, {"c": msg.content, "ts":msg.timestamp})
    def recvMessages(self) -> Generator[Message, None, None]:
        if not self.canSendAndRecv():
            return generatoot.emptyGenerator()
        with self._isStopedVcLock:
            self._isStopedVc = False
        gen:Generator[bytes, None, None] = generatoot.emptyGenerator()
        Thread(target=self._generatorStoper, args=(MESSAGE, gen,), daemon=True).start()
        Messages.setOutputMessagesGenerator(gen)
        for m in gen:
            yield m

    def sendPCMVoicesByGenerator(self, pcmGen:Generator[bytes, None, None]) -> None:
        with self._isStopedVcLock:
            self._isStopedVc = False
        encoder = OpusEncoder(self._callNodeInfo.samplingRate, self._callNodeInfo.channels, OPUS_APPLICATION_AUDIO)
        Thread(target=self._generatorStoper, args=(1, pcmGen,), daemon=True).start()
        fSize = MyInfo.getFrameAndBlockSize()
        for f in pcmGen:
            ed = encoder.encode(f, fSize)
            self.sendToEncrypted(CommuType.SEND_MESSAGE, {"c":ed.hex()})
    def recvPCMVoices(self) -> Generator[bytes, None, None]:
        if not self.canSendAndRecv():
            return generatoot.emptyGenerator()
        with self._isStopedVcLock:
            self._isStopedVc = False
        decoder = OpusDecoder(self._callNodeInfo.samplingRate, self._callNodeInfo.channels)
        gen:Generator[bytes, None, None] = generatoot.emptyGenerator()
        Thread(target=self._generatorStoper, args=(VOICE, gen,), daemon=True).start()
        Voices.setOutputVoicesGenerator(gen)
        for oF in gen:
            yield decoder.decode(oF, self._callNodeInfo.frameSize)