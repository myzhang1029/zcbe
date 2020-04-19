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
from pathlib import Path
from .warner import ZCBEWarner
from .exceptions import *

class Project:
    """Represents a project (see concepts)."""
    def __init__(self, proj_dir: str, warner: ZCBEWarner):
        self.proj_dir = Path(proj_dir)
        self.build_toml = self.build_dir / "build.toml"
        if self.build_toml.exists():
            self.parse_build_toml()
        else:
            raise BuildTOMLError("build.toml not found")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return
