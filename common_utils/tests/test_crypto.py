from cryptography.fernet import Fernet

from common_utils import decrypt_env_var


def test_decrypt_env_var(monkeypatch):
    key = Fernet.generate_key()
    fernet = Fernet(key)
    secret = "super-secret"
    encrypted = fernet.encrypt(secret.encode()).decode()
    monkeypatch.setenv("FERNET_KEY", key.decode())
    monkeypatch.setenv("SECRET_VAR", encrypted)

    assert decrypt_env_var("SECRET_VAR") == secret


def test_decrypt_env_var_missing(monkeypatch):
    monkeypatch.delenv("FERNET_KEY", raising=False)
    monkeypatch.setenv("SECRET_VAR", "value")
    assert decrypt_env_var("SECRET_VAR") is None