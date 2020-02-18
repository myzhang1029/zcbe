#!/usr/bin/env python3
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
from .exceptions import BuildTOMLError, MappingTOMLError, ProjectTOMLError

class Project:
    def __init__(self, projdir):
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

    def get_proj_path(self, projname):
        self.mappingtoml = self.projdir / "mapping.toml"
        if not self.mappingtoml.exists():
            raise MappingTOMLError("mapping.toml not found")
        mapping = toml.load(self.mappingtoml)["mapping"]
        try:
            return mapping[projname]
        except KeyError as e:
            raise MappingTOMLError(f"project {projname} not found") from e

    def build(self, proj):
        print(self.get_proj_path(proj))

def main(projdir, to_build):
    with Project(projdir) as proj:
        for one in to_build:
            proj.build(one)

if __name__ == "__main__":
    main(sys.argv[1], ["gcc"])
