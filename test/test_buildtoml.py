"""Test for build.toml handling."""

import io
from copy import deepcopy

import zcbe

from .test_zcbe import BS_BASE, base_test_invocator


def test_global_dep(monkeypatch):
    """Test for global build dependency."""
    stdin = io.StringIO("y\n")
    buildspec = deepcopy(BS_BASE)
    buildspec["build_toml"]["deps"] = {
        "build": [
            "cmake"
        ]
    }
    with base_test_invocator(monkeypatch, stdin=stdin, buildspec=buildspec) \
            as (_, stdout, stderr):
        assert stderr.getvalue() == ""
        assert "cmake" in stdout.getvalue()
