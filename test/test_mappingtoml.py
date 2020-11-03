"""Test for mappiing.toml handling."""
from copy import deepcopy

import zcbe

from .test_zcbe import BS_BASE, base_test_invocator


def test_mapping(monkeypatch):
    """Test for mapping.toml override."""
    buildspec = deepcopy(BS_BASE)
    buildspec["mapping_toml_filename"] = "m.toml"
    buildspec["build_toml"]["info"]["mapping"] = "m.toml"
    with base_test_invocator(monkeypatch, buildspec=buildspec) \
            as (_, _, stderr):
        assert stderr.getvalue() == ""


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
    try:
        with base_test_invocator(monkeypatch, buildspec=buildspec):
            # `with` to activate the cm
            pass
    except zcbe.exceptions.MappingTOMLError:
        return
    assert 0, "This test should raise"


def test_mappingtoml_keymissing(monkeypatch):
    """Test for non-existent project"""
    buildspec = deepcopy(BS_BASE)
    del buildspec["mapping_toml"]["mapping"]["pj2"]
    try:
        with base_test_invocator(monkeypatch, buildspec=buildspec):
            # `with` to activate the cm
            pass
    except zcbe.exceptions.MappingTOMLError:
        return
    assert 0, "This test should raise"
