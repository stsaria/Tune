from threading import Lock
from typing import Generator

from src.directNet.model.Message import Message

MSG_GENERATOR = Generator[Message, None, None]

class Messages:
    _outputMessagesGenerator:MSG_GENERATOR = None
    _outputMessagesGeneratorLock:Lock = Lock()

    @classmethod
    def recv(cls, gen:MSG_GENERATOR) -> None:
        for m in gen:
            with cls._outputMessagesGeneratorLock:
                if oG := cls._outputMessagesGenerator:
                    try:
                        oG.send(m)
                    except (GeneratorExit, StopIteration):
                        pass
    @classmethod
    def setOutputMessagesGenerator(cls, gen:MSG_GENERATOR) -> None:
        with cls._outputMessagesGeneratorLock:
            cls._outputMessagesGenerator = gen
