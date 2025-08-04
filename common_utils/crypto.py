import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken


def decrypt_env_var(var_name: str, key_env_var: str = "FERNET_KEY") -> Optional[str]:
    """Decrypt an environment variable using a Fernet key.

    Args:
        var_name: Name of the environment variable containing the encrypted value.
        key_env_var: Name of the env var that stores the base64 encoded Fernet key.

    Returns:
        The decrypted value if both the encrypted value and key are provided and
        the decryption succeeds. Otherwise, ``None`` is returned.
    """
    encrypted_value = os.getenv(var_name)
    key = os.getenv(key_env_var)
    if not encrypted_value or not key:
        return None
    fernet = Fernet(key.encode())
    try:
        return fernet.decrypt(encrypted_value.encode()).decode()
    except InvalidToken:
        return None