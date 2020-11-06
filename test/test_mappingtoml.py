"""Test for mapping.toml handling."""
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
