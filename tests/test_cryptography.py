import pytest
from pathlib import Path
from z_model.cryptography import newkeys, PublicKey, PrivateKey


def test_license(tmp_path):
    d = tmp_path / 'data'
    d.mkdir()

    pub, pvt = newkeys(512)
    assert isinstance(pub, PublicKey)
    assert isinstance(pvt, PrivateKey)

    pub.save(d / 'pub.key')
    assert (d / 'pub.key').exists()
    pub2 = PublicKey.load(d / 'pub.key')
    assert isinstance(pub2, PublicKey)
    assert pub == pub2

    pvt.save(d / 'pvt.key')
    assert (d / 'pvt.key').exists()
    pvt2 = PrivateKey.load(d / 'pvt.key')
    assert isinstance(pvt2, PrivateKey)
    assert pvt == pvt2
