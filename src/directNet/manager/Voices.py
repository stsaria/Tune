from threading import Lock
from typing import Generator

VOICE_GENERATOR = Generator[bytes, None, None]

class Voices:
    _outputVoicesGenerator:VOICE_GENERATOR = None
    _outputVoicesGeneratorLock:Lock = Lock()

    @classmethod
    def recv(cls, gen:VOICE_GENERATOR) -> None:
        for m in gen:
            with cls._outputVoicesGeneratorLock:
                if oG := cls._outputVoicesGenerator:
                    try:
                        oG.send(m)
                    except (GeneratorExit, StopIteration):
                        pass
    @classmethod
    def setOutputVoicesGenerator(cls, gen:VOICE_GENERATOR) -> None:
        with cls._outputVoicesGeneratorLock:
            cls._outputVoicesGenerator = gen