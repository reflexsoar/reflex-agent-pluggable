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

    os.remove('./tests/sample_data/reflexsoar-agent-vault.yml')
    vault.setup()
    _id = vault.create_secret('test', 'test')
    assert vault.secrets.get(_id) is not None
    assert vault.get_secret(_id) == {'username': 'test', 'password': 'test'}

    vault2 = Vault(vault_path='./tests/sample_data', secret_key=vault.secret_key)
    vault2.load_vault()
    secret = vault2.get_secret(_id)
    assert secret == {'username': 'test', 'password': 'test'}

    vault.update_secret(_id, 'test2', 'test2')
    assert vault.secrets.get(_id) is not None
    assert vault.get_secret(_id) == {'username':'test2', 'password': 'test2'}

    vault.delete_secret(_id)
    assert vault.secrets.get(_id) is None

def test_invalid_token():

    os.environ['REFLEX_AGENT_VAULT_SECRET'] = 'badtoken'
    vault = Vault(vault_path='./tests/sample_data')
    secret = vault.get_secret([s for s in vault.secrets.keys()][0])
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


import time


def worker(vault, _id, ids):
    secret = vault.create_secret(f'test-{_id}', 'test')
    ids.append((secret,_id))

def test_multiprocessing_access_to_vault():

    from multiprocessing import Manager, Process
    from multiprocessing.managers import BaseManager

    vault = Vault(vault_path='./tests/sample_data', name='reflexsoar-agent-vault-multiprocessed.yml', empty_vault=True)
    os.remove(vault.vault_path)
    vault.setup()

    processes = []
    manager = Manager()
    secret_ids = manager.list()
    for i in range(10):
        p = Process(target=worker, args=(vault, i, secret_ids))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    assert len(secret_ids) == 10

    vault.refresh()

    for _id in secret_ids:
        print(f'Checking for secret {_id[0]}')
        assert vault.get_secret(_id[0]) == {'username': f'test-{_id[1]}', 'password': 'test'}
        vault.delete_secret(_id[0], skip_save=True)
    vault.save()
    assert len(vault.secrets) == 0
