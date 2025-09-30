from threading import Lock

from src.allNet.util import rsa
from src.allNet.util import ed25519


class MyInfo:
    _name:str = None
    _pivKey:str = None
    _pubKey:str = None
    _rsaPivKey:str = None
    _rsaPubKey:str = None
    _frameAndBlockSize:int = None
    _channels:int = None
    _samplingRate:int = None
    
    @classmethod
    def setName(cls, name:str) -> None:
        cls._name = name
    @classmethod
    def getName(cls) -> str | None:
        return cls._name
    @classmethod
    def setKey(cls, pivKey:str) -> None:
        cls._pivKey = pivKey
        cls._pubKey = ed25519.getPubKeyByPivKey(pivKey)
    @classmethod
    def getPivKey(cls) -> str | None:
        return cls._pivKey
    @classmethod
    def getPubKey(cls) -> str | None:
        return cls._pubKey
    @classmethod
    def setRsaKey(cls, rsaPivKey:str) -> None:
        cls._rsaPivKey = rsaPivKey
        cls._rsaPubKey = rsa.getPubKeyByPivKey(rsaPivKey)
    @classmethod
    def getRsaPivKey(cls) -> str | None:
        return cls._rsaPivKey
    @classmethod
    def getRsaPubKey(cls) -> str | None:
        return cls._rsaPubKey
    @classmethod
    def setAudioConfig(cls, frameAndBlockSize:int, channels:int, samplingRate:int) -> None:
        cls._frameAndBlockSize = frameAndBlockSize
        cls._channels = channels
        cls._samplingRate = samplingRate
    @classmethod
    def getFrameAndBlockSize(cls) -> int | None:
        return cls._frameAndBlockSize
    @classmethod
    def getChannels(cls) -> int | None:
        return cls._channels
    @classmethod
    def getSamplingRate(cls) -> int | None:
        return cls._samplingRate