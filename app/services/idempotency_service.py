from typing import Dict, Optional

_store: Dict[str, str] = {}


def remember_request_key(request_key: str, response_key: str) -> bool:
    if request_key in _store:
        return False
    _store[request_key] = response_key
    return True


def clear_idempotency_store() -> None:
    _store.clear()


def get_response_for_key(request_key: str) -> Optional[str]:
    return _store.get(request_key)
