"""
Regression test for the config <-> env-template contract (Finding #7).

``Settings`` (``src/config.py``), ``env.example`` and the ``docker-compose.yml``
environment blocks restate the same keys by hand. Because ``Settings`` uses
``extra="ignore"``, an ``env.example`` key that no consumer reads is silently
dropped, and a new ``Settings`` field absent from ``env.example`` is silently
undocumented (it falls back to its default).

This test pins both directions:

* every ``Settings`` field must be documented in ``env.example``; and
* every ``env.example`` key must be consumed by *some* reader — either a
  ``Settings`` field (the Flask app) or a ``${VAR}`` reference in
  ``docker-compose.yml`` (the container stack).

A new setting without an env example, or an orphaned env key no one reads, now
fails this test. See ``drift-risk-map.md`` Finding #7.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config import Settings

_ROOT = os.path.join(os.path.dirname(__file__), "..")
_ENV_EXAMPLE = os.path.join(_ROOT, "env.example")
_COMPOSE = os.path.join(_ROOT, "docker-compose.yml")

_ENV_KEY_RE = re.compile(r"^([A-Z][A-Z0-9_]*)=", re.MULTILINE)
_COMPOSE_VAR_RE = re.compile(r"\$\{([A-Z][A-Z0-9_]*)")


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _settings_keys() -> set[str]:
    return {name.upper() for name in Settings.model_fields}


def _env_example_keys() -> set[str]:
    return set(_ENV_KEY_RE.findall(_read(_ENV_EXAMPLE)))


def _compose_referenced_keys() -> set[str]:
    return set(_COMPOSE_VAR_RE.findall(_read(_COMPOSE)))


def test_every_setting_is_in_env_example() -> None:
    """Every Settings field must be documented in env.example."""
    missing = sorted(_settings_keys() - _env_example_keys())
    assert not missing, (
        "Settings fields not documented in env.example: "
        + ", ".join(missing)
        + ". Add them so deployments know the key exists."
    )


def test_no_orphan_keys_in_env_example() -> None:
    """Every env.example key must be read by Settings or docker-compose."""
    consumed = _settings_keys() | _compose_referenced_keys()
    orphans = sorted(_env_example_keys() - consumed)
    assert not orphans, (
        "env.example keys that no consumer reads (silently ignored): "
        + ", ".join(orphans)
        + ". Either wire them up or remove them from the template."
    )
