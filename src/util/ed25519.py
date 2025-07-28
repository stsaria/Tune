from cryptography.hazmat.primitives.asymmetric import ed25519

def generate() -> tuple[str, str]:
    pivKey = ed25519.Ed25519PrivateKey.generate()
    pubKey = pivKey.public_key()
    return pivKey.private_bytes_raw().hex(), pubKey.public_bytes_raw().hex()