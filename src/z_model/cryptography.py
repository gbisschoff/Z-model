from pathlib import Path

import rsa


class FileKey:
    def save(self, url: Path, format:str='PEM'):
        with open(url, 'wb') as f:
            f.write(self.save_pkcs1(format))
        return self

    @classmethod
    def load(cls, url: Path, format:str='PEM'):
        with open(url, 'rb') as f:
            key = cls.load_pkcs1(f.read(),format)
        return key


class PublicKey(rsa.PublicKey, FileKey):
    pass


class PrivateKey(rsa.PrivateKey, FileKey):
    pass


def newkeys(*args, **kwargs):
    pub, pvt = rsa.newkeys(*args, **kwargs)
    return PublicKey(pub.n, pub.e), PrivateKey(pvt.n, pvt.e, pvt.d, pvt.p, pvt.q)

