"""Test for zcbe."""

import contextlib
import io
import json
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import List

import toml

import zcbe

# Put into the with stmt if debug
# __import__("subprocess").run(["cp", "-r", skeleton.as_posix(),
# Path('~').expanduser()])

# Default build specification
BS_BASE = {
    # To test Build's built_toml_filename option
    "build_toml_filename": "build.toml",
    "build_toml": {
        'info': {'build-name': 'name',
                 'prefix': 'prefix',
                 'hostname': 'i486-linux-gnu'},
        'env': {'CC': 'zcbecc',
                'CFLAGS': '-W -Wall',
                'LDFLAGS': '-lm'}
    },
    "mapping_toml_filename": "mapping.toml",
    # 2 projects to test
    "mapping_toml": {'mapping': {'pj': '.', 'pj2': '.'}},
    "projects": [
        {
            "name": "pj",
            "build_sh": (
                "#!/bin/sh\n"
            ),
            "conf_toml": {
                'package': {
                    'name': 'pj',
                    'ver': '1.0'
                },
                'deps': {
                    'build': [],
                    'req': []
                }
            }
        },
        {
            "name": "pj2",
            "build_sh": (
                "#!/bin/sh\n"
            ),
            "conf_toml": {
                'package': {'name': 'pj2', 'ver': '1.0.0'},
                'deps': {'build': [], 'req': ['pj']}
            }
        }
    ]
}


@contextlib.contextmanager
def skel(buildspec: dict = None):
    """Create ZCBE directory structure according to buildspec."""
    if buildspec is None:
        buildspec = deepcopy(BS_BASE)
    with tempfile.TemporaryDirectory() as dirname:
        tempdir = Path(dirname)
        build_toml = buildspec["build_toml"]
        build_toml_filename = buildspec["build_toml_filename"]
        toml.dump(build_toml, (tempdir/build_toml_filename).open("w"))
        mapping_toml = buildspec["mapping_toml"]
        mapping_toml_filename = buildspec["mapping_toml_filename"]
        toml.dump(mapping_toml, (tempdir/mapping_toml_filename).open("w"))
        (tempdir/"zcbe").mkdir()
        for proj in buildspec["projects"]:
            proj_path = tempdir/"zcbe"/(proj["name"]+".zcbe")
            proj_path.mkdir()
            with (proj_path/"build.sh").open("w") as fil:
                fil.write(proj["build_sh"])
            with (proj_path/"conf.toml").open("w") as fil:
                conf_toml = proj["conf_toml"]
                toml.dump(conf_toml, fil)
        yield tempdir


@contextlib.contextmanager
def base_test_invocator(monkeypatch, *, args: List[str] = [],
                        stdin: io.StringIO = None,
                        buildspec: dict = None):
    """Run zcbe with test buildspec."""
    with skel(buildspec) as skeleton:
        stdout = io.StringIO()
        stderr = io.StringIO()
        monkeypatch.setattr(
            "sys.argv", ["zcbe"] + args + ["-C", skeleton.as_posix(), "pj2"])
        monkeypatch.setattr("sys.stdin", stdin or io.StringIO(""))
        monkeypatch.setattr("sys.stdout", stdout)
        monkeypatch.setattr("sys.stderr", stderr)
        zcbe.start()
        yield skeleton, stdout, stderr


def test_simple(monkeypatch):
    """Test for logic and syntax errors."""
    with base_test_invocator(monkeypatch, args=["-s"]) \
            as (_, _, stderr):
        assert stderr.getvalue() == ""


def test_env(monkeypatch):
    """Test for environment handling."""
    buildspec = deepcopy(BS_BASE)
    buildspec["build_toml"]["env"]["ENV1"] = "$ZCHOST"
    buildspec["projects"][0]["build_sh"] += "echo $ENV1 >> pj.f\n"
    buildspec["projects"][1]["conf_toml"]["env"] = {
        "ENV2": "${ZCPREF}",
        # A non-existent environ
        "ENV3": "${NOTHING}"
    }
    buildspec["projects"][1]["build_sh"] += "echo $ZCHOST >> pj2.f\n"
    buildspec["projects"][1]["build_sh"] += "echo $ENV2 >> pj2.f\n"
    buildspec["projects"][1]["build_sh"] += "echo $ENV3 >> pj2.f\n"
    with base_test_invocator(monkeypatch, buildspec=buildspec) \
            as (skeleton, _, stderr):
        prefix = (skeleton/"prefix").resolve().as_posix()
        assert stderr.getvalue() == ""
        assert (skeleton/"pj.f").open().read() == "i486-linux-gnu\n"
        assert (skeleton/"pj2.f").open().read() \
            == "i486-linux-gnu\n" + prefix + "\n\n"


def test_builddep_prompt(monkeypatch):
    """Test for build dependency prompt."""
    stdin = io.StringIO("y\nt\nn\n\n")
    buildspec = deepcopy(BS_BASE)
    buildspec["projects"][0]["conf_toml"]["deps"]["build"].append("bud0")
    buildspec["projects"][1]["conf_toml"]["deps"]["build"].append("bud1")
    with base_test_invocator(monkeypatch, stdin=stdin, buildspec=buildspec) \
            as (_, _, stderr):
        assert stderr.getvalue() == ""


def test_recipe(monkeypatch):
    """Test for writing recipe upon success and failure."""
    buildspec = deepcopy(BS_BASE)
    # Let pj2 fail
    buildspec["projects"][1]["build_sh"] = "#!/bin/sh\nexit 1"
    with base_test_invocator(monkeypatch, buildspec=buildspec, args=["-s"]) \
            as (skeleton, _, _):
        recipe = json.load((skeleton/"prefix/zcbe.recipe").open())
        # No pj2 but has pj
        assert recipe["req"] == {"pj": True}
