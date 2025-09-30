"""Settings モジュール

自動生成ドキュメント用 docstring。
"""

from configparser import ConfigParser
from enum import Enum
import os
from threading import Lock

from src.defined import ENCODE, SAVED_PATH, SETTINGS_FILE_NAME, SETTINGS_SECTION_NAME
from src.allNet.util import ed25519, rsa

"""Configuration management for the application."""

class Key(Enum):
    """Configuration keys."""
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
    YOUYOURYOU_ADDR = "youYourYouAddr"
    MIN_COUNT_FOR_MAX_REPLY_RATIO = "minCountForMaxReplyRatio"
    NODE_NEW_DURATION_SEC = "nodeNewDurationSec"
    NODE_REPLACEMENT_INTERVAL_MIN = "nodeReplacementIntervalMin"
    NODE_REPLACEMENT_INTERVAL_MAX = "nodeReplacementIntervalMax"
    MIN_COUNT_FOR_NODE_REPLACEMENT_INTERVAL = "minCountForNodeReplacementInterval"
    PRIVATE_KEY = "privateKey"
    DIRECT_VC_FRAME_AND_BLOCK_SIZE = "directVcFrameSize"
    DIRECT_VC_SAMPLING_RATE = "directVcSamplingRate"
    DIRECT_VC_CHANNELS = "directVcChannels"
    RSA_PRIVATE_KEY = "rsaPrivateKey"
    DIRECT_VC_HELLO_TIMEOUT_SEC = "directVcHelloTimeoutSec"
    MY_NAME = "myName"

class Settings:
    _conf:ConfigParser = ConfigParser()
    _confLock:Lock = Lock()
    _f = SAVED_PATH+SETTINGS_FILE_NAME
    @classmethod
    def set(cls, k:Key, v:str) -> None:
        """Set a configuration value and save it to the file."""
        with cls._confLock:
            cls._conf.set(SETTINGS_SECTION_NAME, k.value, str(v))
            with open(cls._f, mode="w", encoding=ENCODE) as f:
                cls._conf.write(f)
    @classmethod
    def get(cls, k:Key) -> str:
        """Get a configuration value."""
        with cls._confLock:
            return cls._conf.get(SETTINGS_SECTION_NAME, k.value)
    @classmethod
    def getInt(cls, k:Key) -> int:
        """Get a configuration value as an integer."""
        return int(cls.get(k))
    @classmethod
    def getFloat(cls, k:Key) -> int:
        """Get a configuration value as a float."""
        return float(cls.get(k))
    getStr = get
    @classmethod
    def init(cls) -> None:
        """Initialize the configuration file with default values if it doesn't exist."""
        isF = os.path.isfile(cls._f)
        if not isF:
            cls._conf.add_section(SETTINGS_SECTION_NAME)
            
            cls.set(Key.MAX_NODES, 75)
            cls.set(Key.MAX_MESSAGES, 1000)
            cls.set(Key.MAX_REPLY_RATIO, 7/10)
            cls.set(Key.MIN_MESSAGE_SIZE, 10)
            cls.set(Key.EXPIRATION_SECONDS, 5*3600)
            cls.set(Key.BUFFER, 1024*1024)
            cls.set(Key.MEESAGES_PER_NODE, 16)
            cls.set(Key.MESSAGES_RECURS, 4)
            cls.set(Key.SOCK_TIME_OUT, 7)
            cls.set(Key.IMYME_ADDR, "IMYME:IMYME:123456")
            cls.set(Key.COPY_REPLY_FROM_MSGS, "yes")
            cls.set(Key.YOUYOURYOU_ADDR, "YOUYOURYOU:YOUYOURYOU:654321")
            cls.set(Key.MIN_COUNT_FOR_MAX_REPLY_RATIO, 50)
            cls.set(Key.NODE_NEW_DURATION_SEC, 10)
            cls.set(Key.NODE_REPLACEMENT_INTERVAL_MIN, 3600)
            cls.set(Key.NODE_REPLACEMENT_INTERVAL_MAX, 5400)
            cls.set(Key.MIN_COUNT_FOR_NODE_REPLACEMENT_INTERVAL, 20)
            cls.set(Key.PRIVATE_KEY, ed25519.generate())
            cls.set(Key.DIRECT_VC_SAMPLING_RATE, 48000)
            cls.set(Key.DIRECT_VC_FRAME_AND_BLOCK_SIZE, 960)
            cls.set(Key.DIRECT_VC_CHANNELS, 1)
            cls.set(Key.RSA_PRIVATE_KEY, rsa.generate())
            cls.set(Key.DIRECT_VC_HELLO_TIMEOUT_SEC, 120)
            cls.set(Key.MY_NAME, "imyme")

Settings.init()