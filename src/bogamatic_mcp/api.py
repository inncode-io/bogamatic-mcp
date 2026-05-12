"""Thin HTTP client for the Bogamatic API."""

from __future__ import annotations

import os

import requests

API_BASE_URL = os.getenv("BOGAMATIC_API_URL", "https://bogamatic-api.inncode.io")


def _creds() -> dict[str, str]:
    username = os.getenv("SAC_USERNAME", "")
    password = os.getenv("SAC_PASSWORD", "")
    if not username or not password:
        raise ValueError("SAC_USERNAME and SAC_PASSWORD environment variables must be set.")
    return {"matricula": username, "password": password}


def post(path: str, data: dict | None = None, timeout: int = 30) -> dict:
    body = {**_creds(), **(data or {})}
    resp = requests.post(f"{API_BASE_URL}{path}", json=body, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def download(path: str, data: dict | None = None, timeout: int = 60) -> tuple[bytes, str, str]:
    """POST and return (content_bytes, content_type, filename)."""
    body = {**_creds(), **(data or {})}
    resp = requests.post(f"{API_BASE_URL}{path}", json=body, timeout=timeout)
    resp.raise_for_status()
    content_type = resp.headers.get("content-type", "application/octet-stream")
    disposition = resp.headers.get("content-disposition", "")
    filename = "adjunto"
    if 'filename="' in disposition:
        filename = disposition.split('filename="')[1].rstrip('"')
    return resp.content, content_type, filename
