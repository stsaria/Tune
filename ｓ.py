from cryptography.hazmat.primitives.asymmetric import ed25519
from binascii import unhexlify

# 🔐 既存の秘密鍵（32バイトのHex）を復元
priv_hex = "d1fe48e58d83a004deec4e580e82322729a1868431bfaef80f9f52fa5d3a72cf"
private_key = ed25519.Ed25519PrivateKey.from_private_bytes(unhexlify(priv_hex))

# ✉️ メッセージを用意（署名対象）
message = b"6da87714920c94848041c28c535061303659df09991fa2b6cb0e6f7c2ba4a111"

# ✍️ 署名を作成
signature = private_key.sign(message)

# 出力（Hex表示）
print("🖋️ Signature (hex):", signature.hex())
