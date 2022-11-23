import os

import pytest

from reflexsoar_agent.core.vault import Vault


@pytest.fixture
def vault():
    return Vault(vault_path='./tests/sample_data')

def test_vault_setup(vault):
    """Checks to make sure the vault is initialized correctly and that
    when setup() is called the YAML file is created accordingly
    """
    vault.setup()
    assert os.path.exists(vault.vault_path)


def test_secret_cradle_to_grave(vault):
    """Checks to make sure that a secret is created and that it can be
    retrieved from the vault
    """
    vault.setup()
    _id = vault.create_secret('test', 'test')
    assert vault.secrets.get(_id) is not None
    assert vault.get_secret(_id) == {'username': 'test', 'password': 'test'}

    vault.update_secret(_id, 'test2', 'test2')
    assert vault.secrets.get(_id) is not None
    assert vault.get_secret(_id) == {'username':'test2', 'password': 'test2'}

    vault.delete_secret(_id)
    assert vault.secrets.get(_id) is None

def test_secret_from_disk(vault):
    """Checks to make sure that the secret can be decrypted
    from the on-disk vault file
    """

    vault.load_vault()
    secret = vault.get_secret('ff8579b5-bbb3-47e0-948b-1f376aabbbc3')
    assert secret == {'username': 'test', 'password': 'test'}

def test_invalid_token():

    os.environ['REFLEX_AGENT_VAULT_SECRET'] = 'badtoken'
    vault = Vault(vault_path='./tests/sample_data')
    secret = vault.get_secret('ff8579b5-bbb3-47e0-948b-1f376aabbbc3')
    assert secret == {'username': '', 'password': ''}

def test_load_bad_vault_path():

    vault = Vault(vault_path='./tests/sample_data', name='badvault.yml')
    assert os.path.exists(vault.vault_path) is True
    os.remove(vault.vault_path)

def test_bad_secret_uuid(vault):

    secret = vault.get_secret('bad-uuid')
    assert secret == None


def test_save_if_file_deleted(vault):

    os.remove('./tests/sample_data/reflexsoar-agent-vault.yml')
    vault.save()
    assert os.path.exists('./tests/sample_data/reflexsoar-agent-vault.yml') is True

def test_no_path():

    vault = Vault(name='reflexsoar-agent-vault.yml.test')
    assert os.path.exists(vault.vault_path) is True
    os.remove(vault.vault_path)
