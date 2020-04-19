# zcbe/warner.py
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

"""ZCBE warnings."""

import sys
from typing import Dict, Set

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
