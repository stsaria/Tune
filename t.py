from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

# 鍵ペアを生成
private_key = ed25519.Ed25519PrivateKey.generate()
public_key = private_key.public_key()

pivKey = private_key.private_bytes_raw().hex()
pubKey = public_key.public_bytes_raw().hex()

# 出力
print("🔑 Public key:\n", pubKey)
print("🔐 Private key:\n", pivKey)
