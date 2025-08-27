from configparser import ConfigParser
from enum import Enum
import os
from threading import Lock

from src.defined import ENCODE, SAVED_PATH, SETTINGS_FILE_NAME, SETTINGS_SECTION_NAME

class Key(Enum):
    MAX_NODES = "maxNodes"
    MAX_MESSAGES = "maxMessages"
    MAX_REPLY_RATIO = "maxReplyRatio"
    MIN_MESSAGE_SIZE = "minMessageSize"
    EXPIRATION_SECONDS = "expirationSeconds"
    BUFFER = "buffer"
    MEESAGES_PER_NODE = "messagesPerNode"
    MESSAGES_RECURS = "messagesRecurs"
    SOCK_TIME_OUT = "sockTimeOut"
    IMYME_ADDR = "iMyMeAddr"
    COPY_REPLY_FROM_MSGS = "copyReplyFromMessages"

class Settings:
    _conf:ConfigParser = ConfigParser()
    _confLock:Lock = Lock()
    _f = SAVED_PATH+SETTINGS_FILE_NAME
    @classmethod
    def set(cls, k:Key, v:str) -> str:
        cls._conf.set(SETTINGS_SECTION_NAME, k.value, str(v))
        with cls._confLock:
            with open(cls._f, mode="w", encoding=ENCODE) as f:
                cls._conf.write(f)
    @classmethod
    def get(cls, k:Key) -> str:
        return cls._conf.get(SETTINGS_SECTION_NAME, k.value)
    @classmethod
    def getInt(cls, k:Key) -> int:
        return int(cls.get(k))
    @classmethod
    def getFloat(cls, k:Key) -> int:
        return float(cls.get(k))
    @classmethod
    def init(cls) -> None:
        isF = os.path.isfile(cls._f)
        cls._conf.read(cls._f, encoding=ENCODE)
        if not isF:
            cls._conf.add_section(SETTINGS_SECTION_NAME)
            
            cls.set(Key.MAX_NODES, 75)
            cls.set(Key.MAX_MESSAGES, 1000)
            cls.set(Key.MAX_REPLY_RATIO, 1/3)
            cls.set(Key.MIN_MESSAGE_SIZE, 10)
            cls.set(Key.EXPIRATION_SECONDS, 5*3600)
            cls.set(Key.BUFFER, 1024*1024)
            cls.set(Key.MEESAGES_PER_NODE, 16)
            cls.set(Key.MESSAGES_RECURS, 4)
            cls.set(Key.SOCK_TIME_OUT, 7)
            cls.set(Key.IMYME_ADDR, "IMYME:IMYME:654321")
            cls.set(Key.COPY_REPLY_FROM_MSGS, "yes")
Settings.init()