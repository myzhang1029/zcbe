# zcbe.py - The Z Cross Build Environment
#
# Copyright 2019-2020 Zhang Maiyun
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The Z Cross Build Environment.
Concepts:
    a build contains many projects
    a projects is just a program/package
"""

from pathlib import Path
import subprocess as sp
import sys
import os
import argparse
import toml
from .exceptions import *
from typing import Dict, Set

all_warnings = {
    "name-mismatch": "The project's name specified in conf.toml mismatches with that in mapping.toml",
    "generic": "Warnings about ZCBE itself",
    "error": "Error all warnings",
    "all": "Show all warnings",
}

default_warnings = set((
    "name-mismatch",
    "generic",
)) & set(all_warnings)


class ZCBEWarner:
    def __init__(self):
        self.options = {}
        self.silent = False

    def setopts(self, options: Dict[str, bool]):
        """Control whether a warning is shown."""
        for one in options:
            self.options[one] = options[one]

    def load_default(self, enabled: Set[str]):
        for one in enabled:
            self.options[one] = True

    def silent(self):
        self.silent = True

    def warn(self, name: str, s: str):
        if self.options[name] and not self.silent:
            print(f"Warning: {s} [-W{name}]", file=sys.stderr)


warner = ZCBEWarner()
warner.load_default(default_warnings)


class Project:
    def __init__(self, projdir: str):
        self.projdir = Path(projdir)
        self.buildtoml = self.projdir / "build.toml"
        if self.buildtoml.exists():
            self.parse_build_toml()
        else:
            raise BuildTOMLError("build.toml not found")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return

    def parse_build_toml(self):
        bdict = toml.load(self.buildtoml)
        info = bdict["info"]
        try:
            self.build_name = info["build-name"]
            self.prefix = info["prefix"]
            self.hostname = info["hostname"]
        except KeyError as e:
            raise BuildTOMLError(f"Expected key info.{e} not found")
        if info.__contains__("env"):
            for item in info["env"]:
                os.environ[item[0]] = item[1]

    def get_proj_path(self, projname: str):
        self.mappingtoml = self.projdir / "mapping.toml"
        if not self.mappingtoml.exists():
            raise MappingTOMLError("mapping.toml not found")
        mapping = toml.load(self.mappingtoml)["mapping"]
        try:
            return mapping[projname]
        except KeyError as e:
            raise MappingTOMLError(f"project {projname} not found") from e

    def build(self, proj: str):
        print(self.get_proj_path(proj))


class WarningsAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=1, **kwargs):
        super().__init__(option_strings, dest, nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        reverse = False
        name = values[0]
        if name[0:3] == "no-":
            reverse = True
            name = name[3:]
        if not name in all_warnings:
            warner.warn("generic", f"No such warning `{name}'")
            return
        if reverse:
            warner.setopts({name: False})
        else:
            warner.setopts({name: True})


def start():
    ap = argparse.ArgumentParser(description="The Z Cross Build Environment")
    ap.add_argument("-w", help="Suppress all warnings", action="store_true")
    ap.add_argument(
        "-W", help="Modify warning bahaviour", action=WarningsAction)
    ap.add_argument("-C", "--chdir", type=str, help="Change directory to")
    ap.add_argument("-p", "--project-directory",
                    type=str, help="Specify project root")
    ap.add_argument('projects', metavar='PROJ', nargs='+',
                    help='The projects to build')
    ns = ap.parse_args()
    if ns.chdir:
        os.chdir(ns.chdir)
    main(ns.project_directory or ".", ns.projects)


def main(projdir, to_build):
    with Project(projdir) as proj:
        for one in to_build:
            proj.build(one)
