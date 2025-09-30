from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes, PublicKeyTypes
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption, load_pem_private_key, load_pem_public_key

from src.defined import ENCODE

def _pivKeyByStr(pivKeyS) -> PrivateKeyTypes:
    return load_pem_private_key(bytes.fromhex(pivKeyS), password=None)

def _pubKeyByStr(pubKeyS) -> PublicKeyTypes:
    return load_pem_public_key(pubKeyS)

def _getPadding():
    return padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )

def generate() -> str:
    pivKey = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pivKeyS = pivKey.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()).hex()
    return pivKeyS

def encrypt(data:str | bytes, pubKeyS:str) -> str:
    pubKey = _pubKeyByStr(pubKeyS)
    return pubKey.encrypt(data.encode(ENCODE) if isinstance(data, str) else data.hex(), _getPadding()).hex()

def decrypt(dataHex:str, pivKeyS:str, conversionStr:bool=False) -> bytes | str:
    pivKey = _pivKeyByStr(pivKeyS)
    b = pivKey.decrypt(bytes.decode(dataHex), _getPadding())
    if conversionStr:
        return b.decode(ENCODE)
    return b

def getPubKeyByPivKey(pivKeyS:str) -> str:
    pivKey = _pivKeyByStr(pivKeyS)
    return pivKey.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo).hex()