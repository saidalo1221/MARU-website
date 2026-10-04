"""Creates the key pair browsers need to trust your server's push notifications (Web Push / VAPID).

    python scripts/generate_vapid.py

Copy the three printed lines into the production .env. Keep the private key secret, and do not change the keys
later: every customer who allowed notifications would have to allow them again.
"""

import base64

from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid


def b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


vapid = Vapid()
vapid.generate_keys()
public = vapid.public_key.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
private = vapid.private_key.private_numbers().private_value.to_bytes(32, "big")
print(f"VAPID_PUBLIC_KEY={b64(public)}")
print(f"VAPID_PRIVATE_KEY={b64(private)}")
print("VAPID_SUBJECT=mailto:you@your-domain.com")
