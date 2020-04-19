# zcbe/builder.py
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

"""ZCBE builds and projects."""

import toml
import os
from pathlib import Path
from typing import Dict, List
from .dep_manager import DepManager
from .warner import ZCBEWarner
from .exceptions import *


class Build:
    """Represents a build (see concepts)."""

    def __init__(self, build_dir: str, warner: ZCBEWarner):
        self.build_dir = Path(build_dir).absolute()
        self.build_toml = self.build_dir / "build.toml"
        self.warner = warner
        if self.build_toml.exists():
            self.parse_build_toml()
        else:
            raise BuildTOMLError("build.toml not found")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return

    def parse_build_toml(self):
        """Load the build toml (i.e. top level conf) and set envs."""
        bdict = toml.load(self.build_toml)
        info = bdict["info"]
        try:
            self.build_name = info["build-name"]
            self.prefix = info["prefix"]
            self.dep_manager = DepManager(self.prefix+"/zcbe.recipe")
            os.environ["ZCPREF"] = self.prefix
            self.host = info["hostname"]
            os.environ["ZCHOST"] = self.host
            os.environ["ZCTOP"] = self.build_dir.as_posix()
        except KeyError as e:
            raise BuildTOMLError(f"Expected key `info.{e}' not found")
        if "env" in info:
            for item in info["env"]:
                os.environ[item[0]] = item[1]

    def get_proj_path(self, proj_name: str):
        """Get a project's root directory by looking up the mapping toml.
        projname: The name of the projet to look up
        """
        self.mapping_toml = self.build_dir / "mapping.toml"
        if not self.mapping_toml.exists():
            raise MappingTOMLError("mapping.toml not found")
        mapping = toml.load(self.mapping_toml)["mapping"]
        try:
            return self.build_dir / mapping[proj_name]
        except KeyError as e:
            raise MappingTOMLError(f"project {proj_name} not found") from e

    def get_proj(self, proj_name: str):
        """Returns a project instance.
        projname: The name of the project
        """
        proj_path = self.get_proj_path(proj_name)
        self.warner.warn("test", "4")
        return Project(proj_path, proj_name, self, self.warner)

    def build(self, proj_name: str):
        """Build a project.
        proj_name: the name of the project
        """
        if self.dep_manager.check("req", proj_name):
            print(f"Requirement already satisfied: {proj_name}")
            return 0
        print(f"Entering project {proj_name}")
        proj = self.get_proj(proj_name)



class Project:
    """Represents a project (see concepts).
    proj_dir is the directory to the project
    proj_name is the name in mapping.toml of the project
    builder is used to resolve dependencies
    warner is the ZCBEWarner to be used
    """

    def __init__(self,
                 proj_dir: str,
                 proj_name: str,
                 builder: Build,
                 warner: ZCBEWarner
                 ):
        self.proj_dir = Path(proj_dir)
        self.proj_name = proj_name
        self.builder = builder
        self.warner = warner
        self.environ = os.environ
        self.conf_toml = self.locate_conf_toml()
        if self.conf_toml.exists():
            self.parse_conf_toml()
        else:
            raise ProjectTOMLError("conf.toml not found")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return

    def locate_conf_toml(self):
        """Try to locate conf.toml.
        Possible locations:
        $ZCTOP/zcbe/{name}.zcbe/conf.toml
        ./zcbe/conf.toml
        """
        toplevel_try = Path(os.environ["ZCTOP"]) / \
            "zcbe"/(self.proj_name+".zcbe")/"conf.toml"
        if toplevel_try.exists():
            return toplevel_try
        local_try = self.proj_dir / "zcbe/conf.toml"
        if local_try.exists():
            return local_try
        raise ProjectTOMLError("conf.toml not found")

    def solve_deps(self, depdict: Dict[str, List[str]]):
        """Solve dependencies."""
        for table in depdict:
            for item in depdict[table]:
                print(table, item)
                if not self.builder.dep_manager.check(table, item):
                    pass # TODO: build this, circular dep. check

    def parse_conf_toml(self):
        """Load the conf toml and set envs."""
        cdict = toml.load(self.conf_toml)
        pkg = cdict["package"]
        try:
            self.package_name = pkg["name"]
            self.version = pkg["ver"]
        except KeyError as e:
            raise ProjectTOMLError(f"Expected key `package.{e}' not found")
        if "deps" in cdict:
            self.solve_deps(cdict["deps"])
        if "env" in cdict:
            for item in cdict["env"]:
                self.environ[item[0]] = item[1]
