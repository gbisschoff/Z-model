import json
import os
from base64 import b64encode, b64decode
from datetime import date
from pathlib import Path

import rsa
from rsa.pkcs1 import VerificationError

from .cryptography import PublicKey, PrivateKey
from z_model.logging import logging, setup_logging

setup_logging()
HASH_METHOD = 'SHA-1'

try:
    verify_key_path = (Path.cwd() / __file__).with_name('data') / 'verify.key'
    VERIFY_KEY = PublicKey.load(verify_key_path)
except Exception as e:
    logging.error(e)


class License():
    def __init__(self, information: dict, signature: str):
        self.information = information
        self.signature = signature

    def is_valid(self):
        try:
            logging.info(f'Checking user license. {self.information=} {self.signature=}')
            expiration_date_str = self.information.get('expiration_date', None)
            if expiration_date_str:
                expiration_date = date.fromisoformat(expiration_date_str)
                if expiration_date < date.today():
                    raise VerificationError(f'The license expired on the {expiration_date}.')

                time_remaining = (expiration_date - date.today())
                if time_remaining.days <= 30:
                    logging.warning(f'The license expires in {time_remaining.days} days on {expiration_date}.')

            msg = json.dumps(self.information).encode()
            is_valid = rsa.verify(msg, b64decode(self.signature.encode()), VERIFY_KEY) == HASH_METHOD
        except Exception as e:
            logging.error(e)
            is_valid = False

        return is_valid

    @classmethod
    def create_license(cls, information: dict, sign_key: PrivateKey):
        msg = json.dumps(information).encode()
        signature = b64encode(rsa.sign(msg, sign_key, HASH_METHOD)).decode()
        return cls(information, signature)

    def save(self, url: Path):
        with open(url, 'w') as f:
            json.dump({'information': self.information, 'signature': self.signature}, f, indent=4)

        return self

    @classmethod
    def load(cls, url: Path):
        with open(url, 'r') as f:
            obj = json.load(f)

        return cls(**obj)


def create_license(company_name: str, email: str, expiration_date: str, sign_key: PrivateKey) -> License:
    information = {
        'company_name': company_name,
        'email': email,
        'expiration_date': expiration_date,
        'author': os.getlogin()
    }
    return License.create_license(information, sign_key)
