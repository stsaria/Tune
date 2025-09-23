import hashlib

from src.defined import ENCODE

def hash(text:str) -> str:
    return hashlib.sha256(text.encode(ENCODE)).hexdigest()