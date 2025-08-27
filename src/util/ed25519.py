from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ed25519

from src.defined import ENCODE

def generate() -> tuple[str, str]:
    pivKey = ed25519.Ed25519PrivateKey.generate()
    pubKey = pivKey.public_key()
    return pivKey.private_bytes_raw().hex(), pubKey.public_bytes_raw().hex()

def sign(text:str, pivKeyS:str) -> str:
    pivKey = ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex(pivKeyS))
    return pivKey.sign(text.encode(ENCODE)).hex()

def verify(text:str, sig:str, pubKeyS:str) -> bool:
    pubKey = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(pubKeyS))
    try:
        pubKey.verify(bytes.fromhex(sig), text.encode(ENCODE))
        return True
    except InvalidSignature:
        return False