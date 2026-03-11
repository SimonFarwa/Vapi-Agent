"""Vapi REST API Client."""

import httpx

from src.config import VAPI_API_KEY, VAPI_ASSISTANT_ID, VAPI_BASE_URL

TIMEOUT = 30.0


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json",
    }


def get_assistant(assistant_id: str | None = None) -> dict:
    """GET aktuellen Assistant-Stand von Vapi."""
    aid = assistant_id or VAPI_ASSISTANT_ID
    url = f"{VAPI_BASE_URL}/assistant/{aid}"
    resp = httpx.get(url, headers=_headers(), timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def update_assistant(payload: dict, assistant_id: str | None = None) -> dict:
    """PATCH Assistant mit neuem Payload."""
    aid = assistant_id or VAPI_ASSISTANT_ID
    url = f"{VAPI_BASE_URL}/assistant/{aid}"
    resp = httpx.patch(url, headers=_headers(), json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def list_assistants() -> list[dict]:
    """GET alle Assistants im Account."""
    url = f"{VAPI_BASE_URL}/assistant"
    resp = httpx.get(url, headers=_headers(), timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def list_phone_numbers() -> list[dict]:
    """GET alle Phone Numbers im Account."""
    url = f"{VAPI_BASE_URL}/phone-number"
    resp = httpx.get(url, headers=_headers(), timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def list_tools() -> list[dict]:
    """GET alle Tools im Account."""
    url = f"{VAPI_BASE_URL}/tool"
    resp = httpx.get(url, headers=_headers(), timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_calls(limit: int = 10) -> list[dict]:
    """GET letzte Calls."""
    url = f"{VAPI_BASE_URL}/call"
    resp = httpx.get(
        url, headers=_headers(), params={"limit": limit}, timeout=TIMEOUT
    )
    resp.raise_for_status()
    return resp.json()
