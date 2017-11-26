from sharding.collation import (
    CollationHeader,
    Collation,
)
from eth_utils import is_same_address
from evm.rlp.transactions import BaseTransaction


def test_collation():
    coinbase = '\x35' * 20

    collation_header = CollationHeader(coinbase=coinbase)

    collation = Collation(collation_header)
    collation_header_dict = collation.header.to_dict()

    assert collation.header == collation_header
    assert collation.transactions == []
    assert collation.transaction_count == 0
    assert is_same_address(collation_header_dict['coinbase'], coinbase)

    tx = BaseTransaction(
        nonce=0,
        gas_price=0,
        gas=0,
        to='\xff' * 20,
        value=0,
        data='',
        v=0,
        r=0,
        s=0,
    )
    collation.transactions.append(tx)
    assert collation.transactions == [tx]
    assert collation.transaction_count == 1
