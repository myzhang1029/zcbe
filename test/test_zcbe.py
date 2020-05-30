"""Test for zcbe."""

import tempfile
import contextlib
import subprocess
from pathlib import Path
import toml


@contextlib.contextmanager
def skel():
    """Create ZCBE directory structure for tests."""
    with tempfile.TemporaryDirectory() as dirname:
        tempdir = Path(dirname)
        build_toml = {'info': {'build-name': 'name',
                               'prefix': 'prefix',
                               'hostname': 'i486-linux-gnu',
                               'mapping': 'm.toml'},
                      'env': {'CC': 'zcbecc',
                              'CFLAGS': '-W -Wall',
                              'LDFLAGS': '-lm',
                              'env_name': 'env-val'}}
        toml.dump(build_toml, (tempdir/"build.toml").open("w"))
        # To test built_toml_filename option
        toml.dump(build_toml, (tempdir/"b.toml").open("w"))
        # 2 projects to test
        mapping_toml = {'mapping': {'pj': '.', 'pj2': '.'}}
        toml.dump(mapping_toml, (tempdir/"m.toml").open("w"))
        (tempdir/"zcbe").mkdir()
        # Mainly for testing minor features
        (tempdir/"zcbe"/"pj.zcbe").mkdir()
        with (tempdir/"zcbe"/"pj.zcbe"/"build.sh").open("w") as fil:
            fil.writelines((
                "#!/bin/sh\n",
                "echo $I >> pj.f\n",
                "echo $CC >> pj.f\n",
                "echo $CFLAGS >> pj.f\n",
                "echo $LDFLAGS >> pj.f\n",
                "echo $env_name >> pj.f\n",
            ))
        with (tempdir/"zcbe"/"pj.zcbe"/"conf.toml").open("w") as fil:
            conf_toml = {
                'package': {
                    'name': 'pkg-nm',
                    'ver': 'pkg-ver'
                },
                'deps': {
                    'build': ['bud1', 'bud2'],
                    'req': []
                },
                'env': {
                    'I': '1'
                }
            }
            toml.dump(conf_toml, fil)
        # Mainly for testing serious features
        (tempdir/"zcbe"/"pj2.zcbe").mkdir()
        with (tempdir/"zcbe"/"pj2.zcbe"/"build.sh").open("w") as fil:
            fil.writelines((
                "#!/bin/sh\n",
                "echo $ZCPREF > pj2.f\n",
                "echo $ZCHOST >> pj2.f\n",
            ))
        with (tempdir/"zcbe"/"pj2.zcbe"/"conf.toml").open("w") as fil:
            conf_toml = {'package': {'name': 'pj2', 'ver': '1.0.0'},
                         'deps': {'build': ['bud1', 'bud2'], 'req': ['pj']},
                         'env': {'POSIXLY_CORRECT': '1'}}
            toml.dump(conf_toml, fil)
        yield tempdir


def test_zcbe():
    """Main test routine."""
    with skel() as skeleton:
        p = subprocess.Popen(["zcbe", "-sC", skeleton.as_posix(), "pj2"],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate(b"y\ny\n")
        pjf1 = (skeleton/"pj.f").open().read()
        pjf2 = (skeleton/"pj2.f").open().read()
        pjf1_intended = "1\nzcbecc\n-W -Wall\n-lm\nenv-val\n"
        pjf2_intended = skeleton.resolve().as_posix()
        pjf2_intended += "/prefix\ni486-linux-gnu\n"
        assert pjf1 == pjf1_intended
        assert pjf2 == pjf2_intended
