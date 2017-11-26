# -*- coding: utf-8 -*-
import rlp
from rlp.sedes import (
    binary,
    CountableList,
)
from trie.constants import BLANK_NODE_HASH
from evm.rlp.transactions import BaseTransaction
from evm.rlp.sedes import (
    address,
    hash32,
    int256,
    trie_root,
)
from eth_utils import (
    big_endian_to_int,
    decode_hex,
    encode_hex,
    force_bytes,
    keccak,
    to_canonical_address,
    to_checksum_address,
)
from sharding.config import sharding_config


class CollationHeader(rlp.Serializable):

    """A collation header
    [
    shard_id: uint256,
    expected_period_number: uint256,
    period_start_prevhash: bytes32,
    parent_collation_hash: bytes32,
    tx_list_root: bytes32,
    coinbase: address,
    post_state_root: bytes32,
    receipts_root: bytes32,
    number: uint256,
    sig: bytes
    ]
    """

    fields = [
        ('shard_id', int256),
        ('expected_period_number', int256),
        ('period_start_prevhash', hash32),
        ('parent_collation_hash', hash32),
        ('tx_list_root', trie_root),
        ('coinbase', address),
        ('post_state_root', trie_root),
        ('receipts_root', trie_root),
        ('number', int256),
        ('sig', binary)
    ]

    def __init__(self,
                 shard_id=0,
                 expected_period_number=0,
                 period_start_prevhash=keccak(rlp.encode([])),
                 parent_collation_hash=keccak(rlp.encode([])),
                 tx_list_root=BLANK_NODE_HASH,
                 coinbase=sharding_config['GENESIS_COINBASE'],
                 post_state_root=BLANK_NODE_HASH,
                 receipts_root=BLANK_NODE_HASH,
                 number=0,
                 sig=''):
        fields = {k: v for k, v in locals().items() if k != 'self'}
        fields['coinbase'] = to_canonical_address(fields['coinbase'])
        assert len(fields['coinbase']) == 20
        super(CollationHeader, self).__init__(**fields)

    def __getattribute__(self, name):
        try:
            return rlp.Serializable.__getattribute__(self, name)
        except AttributeError:
            return getattr(self.header, name)

    @property
    def hash(self):
        """The binary collation hash"""
        return keccak(rlp.encode(self))

    @property
    def hex_hash(self):
        return encode_hex(self.hash)

    @property
    def signing_hash(self):
        """The hash of the header exluding the signature."""
        return keccak(rlp.encode(self, CollationHeader.exclude(['sig'])))

    def to_dict(self):
        """Serialize the header to a readable dictionary."""
        d = {}

        for field in ('period_start_prevhash', 'parent_collation_hash',
                      'tx_list_root', 'post_state_root', 'receipts_root',
                      'sig'):
            d[field] = encode_hex(getattr(self, field))
        for field in ('shard_id', 'expected_period_number', 'number'):
            d[field] = force_bytes(str(getattr(self, field)))
        for field in ('coinbase',):
            d[field] = to_checksum_address(getattr(self, field))

        assert len(d) == len(CollationHeader.fields)
        return d

    def __repr__(self):
        return '<%s(#%d %s)>' % (self.__class__.__name__, self.number,
                                 encode_hex(self.hash)[:10])

    def __eq__(self, other):
        """Two CollationHeader are equal iff they have the same hash."""
        return isinstance(other, CollationHeader) and self.hash == other.hash

    def __hash__(self):
        return big_endian_to_int(self.hash)

    def __ne__(self, other):
        return not self.__eq__(other)


class Collation(rlp.Serializable):
    """A collation.

    :param header: the collation header
    :param transactions: a list of transactions which are replayed if the
                         state given by the header is not known. If the
                         state is known, `None` can be used instead of the
                         empty list.
    """

    fields = [
        ('header', CollationHeader),
        ('transactions', CountableList(BaseTransaction))
    ]

    def __init__(self, header, transactions=None):
        self.header = header
        self.transactions = transactions or []

    def __getattribute__(self, name):
        try:
            return rlp.Serializable.__getattribute__(self, name)
        except AttributeError:
            return getattr(self.header, name)

    @property
    def transaction_count(self):
        return len(self.transactions)
