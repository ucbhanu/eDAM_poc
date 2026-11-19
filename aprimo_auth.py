import time

import config


class TokenProvider:
    def __init__(self, session):
        self.session = session
        self._token = None
        self._expires_at = 0

    def get_token(self):
        if not self._token or time.time() >= self._expires_at:
            self._fetch()
        return self._token

    def _fetch(self):
        resp = self.session.post(
            config.AUTH_URL,
            auth=(config.CLIENT_ID, config.CLIENT_SECRET),
            data={"grant_type": "client_credentials"},
            headers={"Accept": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._expires_at = time.time() + data.get("expires_in", 600) - 60
