from urllib.parse import urljoin

import config
from aprimo_auth import TokenProvider
from aprimo_session import build_session


class AprimoClient:
    def __init__(self):
        self.session = build_session()
        self.tokens = TokenProvider(self.session)

    def request(self, method, path, headers=None, **kwargs):
        all_headers = {
            "Authorization": f"Bearer {self.tokens.get_token()}",
            "API-VERSION": "1",
            "Accept": "application/json",
            **(headers or {}),
        }
        resp = self.session.request(
            method, urljoin(config.API_BASE, path), headers=all_headers, timeout=60, **kwargs
        )
        resp.raise_for_status()
        return resp.json() if resp.content else None

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)
