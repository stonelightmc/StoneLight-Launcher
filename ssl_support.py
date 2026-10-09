"""TLS/CA bundle helpers for StoneLight Launcher.

PyInstaller builds can run without access to the same certificate bundle as a
normal Python/venv installation. Keep certificate verification enabled, but make
the bundled certifi CA bundle explicit for urllib, requests and libraries that
honor SSL_CERT_FILE / REQUESTS_CA_BUNDLE.
"""

from __future__ import annotations

import os
import ssl
from functools import lru_cache
from pathlib import Path


_CERT_PATH: str | None = None


def configure_ssl_certificates() -> str | None:
    """Configure process-wide CA bundle environment variables.

    Returns the CA bundle path when certifi is available, otherwise None.
    """
    global _CERT_PATH

    if _CERT_PATH and Path(_CERT_PATH).exists():
        return _CERT_PATH

    try:
        import certifi  # type: ignore
        cert_path = str(Path(certifi.where()).resolve())
    except Exception:
        return None

    if not cert_path or not Path(cert_path).exists():
        return None

    _CERT_PATH = cert_path

    # requests honors REQUESTS_CA_BUNDLE. Some stdlib/OpenSSL paths also honor
    # SSL_CERT_FILE. Do not overwrite user-provided values.
    os.environ.setdefault("SSL_CERT_FILE", cert_path)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", cert_path)

    # Make urllib's implicit HTTPS contexts use certifi too. This keeps existing
    # third-party code safer without disabling verification.
    try:
        ssl._create_default_https_context = lambda *args, **kwargs: ssl.create_default_context(cafile=cert_path)
    except Exception:
        pass

    return cert_path


@lru_cache(maxsize=1)
def ssl_context() -> ssl.SSLContext | None:
    cert_path = configure_ssl_certificates()
    if not cert_path:
        return None
    try:
        return ssl.create_default_context(cafile=cert_path)
    except Exception:
        return None
