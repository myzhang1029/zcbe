# zcbe/project.py
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

"""ZCBE projects."""

import toml
import os
from pathlib import Path
from .warner import ZCBEWarner
from .exceptions import *


class Project:
    """Represents a project (see concepts)."""

    def __init__(self, proj_dir: str, proj_name: str, warner: ZCBEWarner):
        self.proj_dir = Path(proj_dir)
        self.proj_name = proj_name
        self.warner = warner
        self.conf_toml = self.locate_conf_toml()
        if self.conf_toml.exists():
            self.parse_conf_toml()
        else:
            raise BuildTOMLError("conf.toml not found")

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

    def parse_conf_toml(self):
        """Load the conf toml and set envs."""
        pass
