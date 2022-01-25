import pytest
from pathlib import Path
from datetime import date
import rsa
from z_model.license import create_license, License
from z_model.cryptography import PrivateKey


def test_license(tmp_path):
    d = tmp_path / 'data'
    d.mkdir()

    pvt = PrivateKey.load(Path('./.secrets/private.key'))

    l = create_license(company_name='Company Name', email='Email', expiration_date=str(date.today()), sign_key=pvt)
    assert l.is_valid()
    l.save(d / '.license')
    assert (d / '.license').exists()
    l = License.load(d / '.license')
    assert isinstance(l, License)

    with pytest.raises(ValueError):
        l.information['expiration_date'] = '1900-01-01'
        l.is_valid()

    with pytest.raises(rsa.pkcs1.VerificationError):
        l.information['expiration_date'] = '2999-12-31'
        l.is_valid()
