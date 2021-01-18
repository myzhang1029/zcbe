"""Test for various command line options."""

import io
from copy import deepcopy
from pathlib import Path

import zcbe

from .test_zcbe import BS_BASE, base_test_invocator


def test_build_all(monkeypatch):
    """Test for -a option."""
    buildspec = deepcopy(BS_BASE)
    buildspec["build_toml"]["env"]["ENV1"] = "$ZCHOST"
    buildspec["projects"][0]["build_sh"] += "touch pj.f\n"
    buildspec["projects"][1]["build_sh"] += "touch pj2.f\n"
    with base_test_invocator(monkeypatch, buildspec=buildspec, args=["-a"]) \
            as (skeleton, _, _):
        assert (skeleton/"pj.f").exists()
        assert (skeleton/"pj2.f").exists()


def test_help_topics(monkeypatch):
    """Test for help topics."""
    try:
        with base_test_invocator(monkeypatch, args=["-H", "warnings"]) \
                as (_, stdout, stderr):
            assert stdout.getvalue() == ""
            assert "name-mismatch" in stderr.getvalue()
    except SystemExit:
        pass
    else:
        assert 0, "This test should exit"
    try:
        with base_test_invocator(monkeypatch, args=["-H", "nothing"]) \
                as (_, stdout, stderr):
            assert stdout.getvalue() == ""
            assert "topics" in stderr.getvalue()
    except SystemExit:
        pass
    else:
        assert 0, "This test should exit"


def test_dry_run(monkeypatch):
    """Test for --dry-run."""
    buildspec = deepcopy(BS_BASE)
    buildspec["projects"][0]["build_sh"] += "echo $ENV1 >> pj.f\n"
    with base_test_invocator(monkeypatch, buildspec=buildspec, args=["-n"]) \
            as (skeleton, _, stderr):
        assert stderr.getvalue() == ""
        assert not (skeleton/"pj.f").exists()


def test_show_unbuilt(monkeypatch):
    """Test for --show-unbuilt."""
    with base_test_invocator(monkeypatch, args=["-u"]) \
            as (_, stdout, stderr):
        assert stderr.getvalue() == ""
        assert "pj" in stdout.getvalue()
        assert "pj2" in stdout.getvalue()
    with base_test_invocator(monkeypatch, args=["-s"]):
        monkeypatch.setattr(
            "sys.argv", ["zcbe", "-u"])
        monkeypatch.setattr("sys.stdout", stdout)
        stdout = io.StringIO()
        zcbe.start()
        assert stdout.getvalue() == ""


def test_prompt_yes(monkeypatch):
    """Test for --yes."""
    buildspec = deepcopy(BS_BASE)
    buildspec["projects"][0]["conf_toml"]["deps"]["build"].append("bud0")
    with base_test_invocator(monkeypatch, buildspec=buildspec, args=["-y"]) \
            as (_, stdout, stderr):
        assert "bud0" not in stdout.getvalue()
        assert stderr.getvalue() == ""


def test_override_prefix(monkeypatch):
    """Test for prefix oveerriding."""
    with base_test_invocator(monkeypatch, args=["-p", "prefiix"]) \
            as (skeleton, _, _):
        assert Path(skeleton/"prefiix/zcbe.recipe").exists()


def test_override_triplet(monkeypatch):
    """Test for triplet overriding."""
    buildspec = deepcopy(BS_BASE)
    # Let pj2 fail
    buildspec["projects"][1]["build_sh"] = \
        "#!/bin/sh\necho \"${ZCHOST}\" > \"${ZCPREF}\"/a"
    with base_test_invocator(monkeypatch, buildspec=buildspec, args=["-t", "arm"]) \
            as (skeleton, _, _):
        assert (skeleton/"prefix/a").open().read() == "arm\n"
