"""Test for warnings."""

from copy import deepcopy

from .test_zcbe import BS_BASE, base_test_invocator


# This only tests basic warning flags. Write warnings' own ones separatedly
def test_wflag(monkeypatch):
    """Test for -w, -Wall, -Werror flags."""
    # A non-existent warning
    with base_test_invocator(monkeypatch, args=["-Wnothing"]) \
            as (_, _, stderr):
        assert "-Wgeneric" in stderr.getvalue()
    # See if -w works
    with base_test_invocator(monkeypatch, args=["-w", "-Wnothing"]) \
            as (_, _, stderr):
        assert stderr.getvalue() == ""
    # See if -Werror works
    try:
        with base_test_invocator(monkeypatch, args=["-Werror", "-Wnothing"]):
            # `with` to activate the cm
            pass
    except SystemExit as err:
        assert err.__class__ == SystemExit
        return
    assert 0, "This test should exit abnormally"


def test_name_mismatch(monkeypatch):
    """Test for -Wname-mismatch."""
    buildspec = deepcopy(BS_BASE)
    buildspec["projects"][0]["conf_toml"]["package"]["name"] = "blabla"
    with base_test_invocator(monkeypatch, buildspec=buildspec) \
            as (_, _, stderr):
        assert "-Wname-mismatch" in stderr.getvalue()
    with base_test_invocator(monkeypatch, args=["-Wno-name-mismatch"],
                             buildspec=buildspec) \
            as (_, _, stderr):
        assert stderr.getvalue() == ""
