"""Генерация Ed25519 keypair для dev."""

from license_core.validator import generate_keypair

if __name__ == "__main__":
    priv, pub = generate_keypair()
    print("LICENSE_SIGNING_PRIVATE_KEY=" + priv)
    print("LICENSE_PUBLIC_KEY=" + pub)
