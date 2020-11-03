"""Test for build.toml handling."""

import io
from copy import deepcopy

import zcbe

from .test_zcbe import BS_BASE, base_test_invocator


def test_buildtoml_notfound(monkeypatch):
    """Test for non-existent build.toml"""
    buildspec = deepcopy(BS_BASE)
    # build.toml not found
    buildspec["build_toml_filename"] = "none.toml"
    try:
        with base_test_invocator(monkeypatch, buildspec=buildspec):
            # `with` to activate the cm
            pass
    except zcbe.exceptions.BuildTOMLError:
        return
    assert 0, "This test should raise"


def test_buildtoml_error2(monkeypatch):
    """Test for bad build.toml"""
    buildspec = deepcopy(BS_BASE)
    del buildspec["build_toml"]["info"]["prefix"]
    try:
        with base_test_invocator(monkeypatch, buildspec=buildspec):
            # `with` to activate the cm
            pass
    except zcbe.exceptions.BuildTOMLError:
        return
    assert 0, "This test should raise"


def test_global_dep_error(monkeypatch):
    """Test for global build dependencies error on unexpected key"""
    buildspec = deepcopy(BS_BASE)
    buildspec["build_toml"]["deps"] = {
        "req": []
    }
    try:
        with base_test_invocator(monkeypatch, buildspec=buildspec):
            # `with` to activate the cm
            pass
    except zcbe.exceptions.BuildTOMLError:
        return
    assert 0, "This test should raise"


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
