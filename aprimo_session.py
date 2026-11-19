import os
import ssl
import tempfile

import requests

import config


def windows_ca_bundle():
    # The corporate proxy re-signs TLS with a root CA only present in the Windows store.
    pems = {
        ssl.DER_cert_to_PEM_cert(cert)
        for store in ("ROOT", "CA")
        for cert, enc, _ in ssl.enum_certificates(store)
        if enc == "x509_asn"
    }
    path = os.path.join(tempfile.gettempdir(), "windows_ca_bundle.pem")
    with open(path, "w") as f:
        f.write("".join(pems))
    return path


def build_session():
    session = requests.Session()
    session.verify = windows_ca_bundle()
    if config.PROXY:
        session.proxies = {"http": config.PROXY, "https": config.PROXY}
    return session
