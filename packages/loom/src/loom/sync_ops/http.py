from __future__ import annotations

import json
from urllib import error, request


def request_json(method: str, url: str, payload: dict[str, object] | None = None) -> dict[str, object]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    try:
        with request.urlopen(request.Request(url, data=data, method=method, headers=headers)) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exception:
        detail = exception.read().decode("utf-8")
        raise RuntimeError(f"Server request failed ({exception.code}): {detail}") from exception
