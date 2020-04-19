# zcbe/build.py
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

"""ZCBE builder."""

import toml
from pathlib import Path
from .warner import ZCBEWarner
from .exceptions import *

class Build:
    """Represents a build (see concepts)."""
    def __init__(self, build_dir: str, warner: ZCBEWarner):
        self.build_dir = Path(build_dir)
        self.build_toml = self.build_dir / "build.toml"
        if self.build_toml.exists():
            self.parse_build_toml()
        else:
            raise BuildTOMLError("build.toml not found")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return

    def parse_build_toml(self):
        """Load the build toml (i.e. top level conf)."""
        bdict = toml.load(self.build_toml)
        info = bdict["info"]
        try:
            self.build_name = info["build-name"]
            self.prefix = info["prefix"]
            self.hostname = info["hostname"]
        except KeyError as e:
            raise BuildTOMLError(f"Expected key `info.{e}' not found")
        if info.__contains__("env"):
            for item in info["env"]:
                os.environ[item[0]] = item[1]

    def get_proj_path(self, projname: str):
        """Get a project's root directory by looking up the mapping toml.
        projname: The name of the projet to look up
        """
        self.mapping_toml = self.build_dir / "mapping.toml"
        if not self.mapping_toml.exists():
            raise MappingTOMLError("mapping.toml not found")
        mapping = toml.load(self.mapping_toml)["mapping"]
        try:
            return mapping[projname]
        except KeyError as e:
            raise MappingTOMLError(f"project {projname} not found") from e

    def get_proj(self, projname: str):
        """Returns a project instance.
        projname: The name of the project
        """
        pass

    def build(self, proj: str):
        print(f"Entering project {proj}")
        proj_dir = self.get_proj_path(proj)
