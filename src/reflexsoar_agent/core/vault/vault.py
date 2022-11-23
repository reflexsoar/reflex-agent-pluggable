import base64
import os
import secrets
from multiprocessing import Lock
from typing import Any, Dict, Optional, Union
from uuid import uuid4

import yaml
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from platformdirs import user_data_dir


class Vault:
    """Creates a Vault object that is used to read and write data to a
    vault file.  The vault file is a YAML file with encrypted secrets
    that are referenced by a UUID. The vault file is stored in the users
    default data directory for the application"""

    def __init__(self, vault_path: Optional[str] = None, **kwargs) -> None:
        """Initialize the Vault object."""

        self.name = kwargs.get('name', 'reflexsoar-agent-vault.yml') or os.getenv(
            'REFLEX_AGENT_VAULT_NAME', 'reflexsoar-agent-vault.yml')
        self.iterations = kwargs.get('iterations', 100_000)

        self.secret_key = kwargs.get('secret_key', self._generate_secret_key()) or os.getenv(
            'REFLEX_AGENT_VAULT_SECRET', self._generate_secret_key())

        self.empty_vault = kwargs.get('empty_vault', False)
        self.lock = Lock()

        if vault_path is None:
            _data_dir = user_data_dir('reflexsoar-agent', 'reflexsoar')
            self.vault_path = os.path.join(_data_dir, self.name)
        else:
            self.vault_path = os.path.join(vault_path, self.name)

        self.secrets: Dict[Any, Any] = {}
        self.load_vault()

    def _generate_secret_key(self):
        """Generate a secret key."""
        return secrets.token_urlsafe(32)

    def _derive_key(self, secret: bytes, salt: bytes, iterations: int = 100_000) -> bytes:
        """Derive a key from a secret and salt."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(secret))

    def _encrypt(self, message: Union[bytes, str]) -> str:
        """Encrypt a message with a secret."""

        if isinstance(message, str):
            message = message.encode()

        salt = secrets.token_bytes(16)
        key = self._derive_key(self.secret_key.encode(), salt, self.iterations)
        big_iters = self.iterations.to_bytes(4, 'big')
        b64_bytes = base64.urlsafe_b64encode(Fernet(key).encrypt(message))
        return base64.urlsafe_b64encode(b'%b%b%b' % (salt, big_iters,
                                                     b64_bytes)).decode()

    def _decrypt(self, ciphertext) -> str:
        """Decrypt a message with a secret."""
        decoded = base64.urlsafe_b64decode(ciphertext)
        salt, iter, token = decoded[:16], decoded[16:20], base64.urlsafe_b64decode(
            decoded[20:])
        iterations = int.from_bytes(iter, 'big')
        key = self._derive_key(self.secret_key.encode(), salt, iterations)
        try:
            return Fernet(key).decrypt(token).decode()
        except InvalidToken:
            return ''

    def setup(self):
        """Initialize the vault."""
        if not os.path.exists(self.vault_path):
            with open(self.vault_path, 'w') as f:
                if not self.empty_vault:
                    if self.secrets == {}:
                        f.close()
                    else:
                        yaml.safe_dump(self.secrets, f, )
                else:
                    self.secrets = {}

    def load_vault(self):
        """Load the vault."""
        if os.path.exists(self.vault_path):
            with open(self.vault_path, 'r') as f:
                data = yaml.safe_load(f)
                if data:
                    self.secrets = data
        else:
            self.setup()

    def refresh(self):
        """Refresh the vault from the vault file."""
        with self.lock:
            self.load_vault()

    def get_secret(self, secret_uuid: str) -> Union[Dict, None]:
        """Get a secret from the vault."""
        _secret = self.secrets.get(secret_uuid, None) or None
        if _secret:
            return {
                "username": self._decrypt(_secret.get('username')),
                "password": self._decrypt(_secret.get('password'))
            }
        return None

    def create_secret(self, username: str, password: str):
        """Set a secret in the vault."""
        secret_uuid = str(uuid4())
        self.secrets[secret_uuid] = {
            "username": self._encrypt(username),
            "password": self._encrypt(password)
        }
        self.save_secret({secret_uuid: self.secrets[secret_uuid]})
        return secret_uuid

    def update_secret(self, secret_uuid: str, username: str, password: str):
        """Update a secret in the vault."""
        self.secrets[secret_uuid] = {
            "username": self._encrypt(username),
            "password": self._encrypt(password)
        }

    def delete_secret(self, secret_uuid: str, skip_save=False):
        """Delete a secret from the vault."""
        with self.lock:
            self.secrets.pop(secret_uuid)
        if not skip_save:
            self.save()

    def save_secret(self, secret):
        """Save a single secret to the vault file"""
        if os.path.exists(self.vault_path):
            with self.lock:
                with open(self.vault_path, 'a') as f:
                    yaml.safe_dump(secret, f)

    def save(self, already_locked=True):
        """Save the vault."""
        if os.path.exists(self.vault_path):
            with self.lock:
                with open(self.vault_path, 'w') as f:
                    if self.secrets == {}:
                        f.close()
                    else:
                        yaml.safe_dump(self.secrets, f)
        else:
            self.setup()
            self.save()
