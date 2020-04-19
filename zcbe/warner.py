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
        self.all = False

    def setopts(self, options: Dict[str, bool]):
        """Control whether a warning is shown or add warnings."""
        for one in options:
            self.options[one] = options[one]

    def load_default(self, all: Set[str], enabled: Set[str]):
        """Load default enable/disable settings.
        all: all warning types
        enabled: defaultly enabled warnings
        """
        for one in all:
            self.options[one] = False
        for one in enabled:
            self.options[one] = True

    def silence(self):
        """Silence all warnings. (-w)"""
        self.silent = True

    def shouldwarn(self, name: str):
        """Determine whether a warnings should be shown."""
        if (self.options["all"] or self.options[name]) and not self.silent:
            return True
        return False

    def werror(self):
        """Exit if -Werror is supplied."""
        if self.options["error"]:
            print(f"Error: exiting [-Werror]", file=sys.stderr)
            sys.exit(2)

    def warn(self, name: str, s: str):
        """Issue a warning.
        name: the registered name of this warning
        s: the warning string
        """
        title = "Warning"
        if self.options["error"]:
            title = "Error"
        if self.shouldwarn(name):
            print(f"{title}: {s} [-W{name}]", file=sys.stderr)
            self.werror()
