from threading import Lock

from src.allNet.model.NodeInfo import NodeInfo

from dataclasses import dataclass

@dataclass
class CallNodeInfo:
    rsaPubKey:str = None
    frameSize:int = None
    channels:int = None
    samplingRate:int = None
    def setRsaPubKey(self, rsaPubKey:str) -> None:
        if not self.rsaPubKey:
            self.rsaPubKey = rsaPubKey
    def setFrameSize(self, frameSize:str) -> None:
        if not self.frameSize:
            self.frameSize = frameSize
    def setChannels(self, channels:int) -> None:
        if not self.channels:
            self.channels = channels
    def setSamplingRate(self, samplingRate:int) -> None:
        if not self.samplingRate:
            self.samplingRate = samplingRate