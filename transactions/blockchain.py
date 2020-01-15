import requests
from aeternity.signing import Account
from aeternity.transactions import TxSigner, TxObject, TxBuilder

FAKE = False
            
#URL_BLOCKCHAIN = '192.168.1.74:2709'

URL_BLOCKCHAIN = 'http://116.203.255.59:8000'

#URL_BLOCKCHAIN = 'https://cryptofest.prokapi.com'

def response_ok(response):
    return response.get('status') == 'ok'

def get(endpoint, params):
    url = URL_BLOCKCHAIN + '/blockchain/' + endpoint
    print('GET URL', url)
    print('GET DATA', params)
    response = requests.get(url, params)
    
    # if response.status == 200:
    #     print('ERROR ON BLOCKCHAIN', response)

    return response.json()

def post(endpoint, data):
    url = URL_BLOCKCHAIN + '/blockchain/' + endpoint
    print('POST URL', url)
    print('POST DATA', data)
    response = requests.post(url, data=data)

    # if response.status == 200:
    #     print('ERROR ON BLOCKCHAIN', response)

    return response.json()

def post_no_json(endpoint, data):
    return requests.post(URL_BLOCKCHAIN + '/blockchain/' + endpoint, data=data)

def get_balance(pubkey):
    if FAKE:
        return None

    params = {
        'pubkey': pubkey
    }

    return get('get_balance', params)

def get_nonce(pubkey):
    if FAKE:
        return 0
    
    params = {
        'pubkey': pubkey
    }
    return get('get_nonce', params)

def get_transfer_tx(caller_pubkey, receiver_pubkey, amount):
    if FAKE:
        return 'tx_+P0rAaEBglFyk6D4I2LrT5PQ3nevVyT7pky89VVCMovBc9vhPTMBoQXMeYA4M85xSwjWsqAZf1iH81bkHfky2XQg8LUKGO7PfgGHAZ3pOdZYAAAAgwGGoIQ7msoAuKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIJ+rc64T3HcnmkdEcHfdnzI/ekdqLQ9JiN9AyNt/QzLjAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGBZUbeM9e8EfKtCIY4NWkAgrTSCHKBDwPH+vSeqqH1e1wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD6mmVLZg=='
        
    params = {
        'caller_pubkey': caller_pubkey,
        'receiver_pubkey': receiver_pubkey,
        'amount': amount
    }
    return get('get_transfer_tx', params)

def sign(priv_key, data):
    acc = Account.from_secret_key_string(priv_key)
    tx_signer = TxSigner(acc, 'ae_uat')
    tx_builder = TxBuilder()
    tx = TxObject(tx=data)
    signature = tx_signer.sign_transaction(tx, None)
    signed = tx_builder.tx_signed([signature], tx, metadata=None)
    return signed.tx

def create_wallet():
    acc = Account.generate()
    pub_key = acc.get_address()
    priv_key = acc.get_secret_key()
    return priv_key, pub_key

def broadcast_signed_tx_sync(signed_tx):
    if FAKE:
        return {'status': 'ok'}
        
    payload = {
        'signed_tx': signed_tx,
    }
    resp = post('broadcast_signed_tx', payload)
    return resp

def check_tx(tx_id):
    if FAKE:
        return {'status': 'ok'}
        
    payload = {
        'tx_id': tx_id,
    }
    resp = get('check_broadcasted_tx', payload)
    return resp

def broadcast_signed_tx(signed_tx):
    if FAKE:
        return {'status': 'ok', 'tx_id': 'FAKED_ID'}
        
    payload = {
        'signed_tx': signed_tx,
    }
    print('TX_BEFORE', payload)
    resp = post('broadcast_signed_tx_async', payload)
    print('TX', resp)
    return resp

def mint(receiver_pubkey, amount):
    if FAKE:
        return {'status': 'ok'}
        
    payload = {
        'receiver_pubkey': receiver_pubkey,
        'amount': amount
    }
    return post('mint', payload)

def burn(receiver_pubkey, amount):
    if FAKE:
        return {'status': 'ok'}
        
    payload = {
        'receiver_pubkey': receiver_pubkey,
        'amount': amount
    }
    return post('burn', payload)

def transfer_aeter(receiver_pubkey, amount):
    if FAKE:
        return {'status': 'ok'}

    # default_amount = 0.01*e18
        
    payload = {
        'receiver_pubkey': receiver_pubkey,
        'amount': amount
    }
    return post('transfer_aeter', payload)




