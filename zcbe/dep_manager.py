# zcbe/dep_manager.py
#
# Copyright 2020 Zhang Maiyun
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

"""ZCBE dependency tracker with persistence."""

import json
from pathlib import Path


class DepManager:
    """Dependency Tracker.

    Args:
        depfile: Path to the dependency tracking file

    Dependency types:
        req: things that need to be built
        build: build tools that should be present on the computer
    """

    def __init__(self, depfile):
        self.depfile = depfile
        if not Path(depfile).exists():
            json.dump({}, open(depfile, "w"))

    def add(self, deptype, depname):
        """Mark a dependency as "built"."""
        depfile = json.load(open(self.depfile))
        try:
            depfile[deptype][depname] = True
        except KeyError:
            depfile[deptype] = {}
            depfile[deptype][depname] = True
        json.dump(depfile, open(self.depfile, "w"))

    @staticmethod
    def ask_build(depname):
        """Ask the user if a build tool has been installed."""
        while True:
            resp = input(f"Is {depname} installed on your system? [y/n] ")
            resp = resp.lower()
            if resp == "y":
                return True
            if resp == "n":
                input(f"Please install {depname} and press enter.")
                return True
            print("Unknown reply.")

    def check(self, deptype, depname):
        """Check if a dependency has been marked as "built"."""
        depfile = json.load(open(self.depfile))
        try:
            return depfile[deptype][depname]
        except KeyError:
            if deptype == "build" and self.ask_build(depname):
                self.add("build", depname)
                return True
            return False
