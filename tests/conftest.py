"""Load the protocol modules without the package __init__ (which needs
Home Assistant). The protocol layer is deliberately HA-free so it can be
tested — and reused — standalone."""
import importlib.util
import os
import sys
import types

import pytest

_DIR = os.path.join(
    os.path.dirname(__file__), "..", "custom_components", "resol_vbus"
)


def _load(name: str):
    pkg_name = "rv_test_pkg"
    if pkg_name not in sys.modules:
        pkg = types.ModuleType(pkg_name)
        pkg.__path__ = [_DIR]
        sys.modules[pkg_name] = pkg
    full = f"{pkg_name}.{name}"
    if full not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            full, os.path.join(_DIR, f"{name}.py")
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules[full] = mod
        spec.loader.exec_module(mod)
    return sys.modules[full]


@pytest.fixture(scope="session")
def fields_mod():
    return _load("fields")


@pytest.fixture(scope="session")
def vbus_mod():
    _load("fields")
    return _load("vbus")


@pytest.fixture(scope="session")
def live_stream() -> bytes:
    path = os.path.join(os.path.dirname(__file__), "fixtures", "live_stream.hex")
    return bytes.fromhex(open(path).read().strip())
