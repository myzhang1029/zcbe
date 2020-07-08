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

from .exceptions import eprint


class ZCBEWarner:
    """A simple warner for ZCBE."""

    def __init__(self):
        self.options = {}
        self.silent = False
        self.all = False

    def setopts(self, options: Dict[str, bool]):
        """Control whether a warning is shown or add warnings."""
        for one in options:
            self.options[one] = options[one]

    def load_default(self, all_warnings: Set[str], enabled_warnings: Set[str]):
        """Load default enable/disable settings.

        Args:
            all_warnings: all warning types
            enabled_warnings: defaultly enabled warnings
        """
        for one in all_warnings:
            self.options[one] = False
        for one in enabled_warnings:
            self.options[one] = True

    def silence(self):
        """Silence all warnings (shell -w)."""
        self.silent = True

    def shouldwarn(self, name: str):
        """Determine whether a warnings should be shown."""
        if (self.options["all"] or self.options[name]) and not self.silent:
            return True
        return False

    def werror(self):
        """Exit if -Werror is supplied."""
        if self.options["error"]:
            eprint("exiting [-Werror]")
            sys.exit(2)

    def warn(self, name: str, string: str):
        """Issue a warning.

        Args:
            name: the registered name of this warning
            string: the warning string
        """
        title = "Warning: "
        if self.options["error"]:
            title = "Error: "
        if self.shouldwarn(name):
            eprint(f"{string} [-W{name}]", title=title)
            self.werror()
