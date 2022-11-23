import base64
import os
import secrets
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

        self.name = kwargs.get('name', 'reflexsoar-agent-vault.yml')
        self.iterations = kwargs.get('iterations', 100_000)
        self.secret_key = os.getenv('REFLEX_AGENT_VAULT_SECRET', '1234567890')

        if vault_path is None:
            _data_dir = user_data_dir('reflexsoar-agent', 'reflexsoar')
            self.vault_path = os.path.join(_data_dir, self.name)
        else:
            self.vault_path = os.path.join(vault_path, self.name)

        self.secrets: Dict[Any, Any] = {}
        self.load_vault()

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
                yaml.dump(self.secrets, f)

    def load_vault(self):
        """Load the vault."""
        if os.path.exists(self.vault_path):
            with open(self.vault_path, 'r') as f:
                self.secrets = yaml.safe_load(f)
        else:
            self.setup()

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
        self.save()
        return secret_uuid

    def update_secret(self, secret_uuid: str, username: str, password: str):
        """Update a secret in the vault."""
        self.secrets[secret_uuid] = {
            "username": self._encrypt(username),
            "password": self._encrypt(password)
        }

    def delete_secret(self, secret_uuid: str):
        """Delete a secret from the vault."""
        self.secrets.pop(secret_uuid)

    def save(self):
        """Save the vault."""
        if os.path.exists(self.vault_path):
            with open(self.vault_path, 'w') as f:
                yaml.dump(self.secrets, f)
        else:
            self.setup()
            self.save()
