"""Test for various error behaviors.

All build-wide exceptions should result in a quit,
project-wide exceptions should be trapped by asyncio.Task, and
show as an error message to prevent orphaning other build processes.
"""
from copy import deepcopy

import zcbe

from .test_zcbe import BS_BASE, base_test_invocator

# build.toml


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


# mapping.toml

def test_mappingtoml_notfound(monkeypatch):
    """Test for non-existent mapping.toml"""
    buildspec = deepcopy(BS_BASE)
    buildspec["mapping_toml_filename"] = "none.toml"
    try:
        with base_test_invocator(monkeypatch, buildspec=buildspec):
            # `with` to activate the cm
            pass
    except zcbe.exceptions.MappingTOMLError:
        return
    assert 0, "This test should raise"


def test_project_nodir(monkeypatch):
    """Test for non-existent project directory"""
    buildspec = deepcopy(BS_BASE)
    buildspec["mapping_toml"]["mapping"]["pj2"] = "non-existent"
    with base_test_invocator(monkeypatch, buildspec=buildspec) \
            as (_, _, stderr):
        assert "non-existent" in stderr.getvalue()


def test_mappingtoml_keymissing(monkeypatch):
    """Test for non-existent project"""
    buildspec = deepcopy(BS_BASE)
    del buildspec["mapping_toml"]["mapping"]["pj2"]
    with base_test_invocator(monkeypatch, buildspec=buildspec) \
            as (_, _, stderr):
        assert 'project "pj2"' in stderr.getvalue()

# conf.toml


def test_failing_conf_no_crash(monkeypatch):
    """Test to make sure a failing conf.toml doesn't crash zcbe."""
    buildspec = deepcopy(BS_BASE)
    del buildspec["projects"][0]["conf_toml"]["package"]
    with base_test_invocator(monkeypatch, buildspec=buildspec, args=["-sa"]) \
            as (_, _, stderr):
        assert "package" in stderr.getvalue()
