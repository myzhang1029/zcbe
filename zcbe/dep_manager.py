# zcbe/dep_manager.py
#
# Copyright 2020-2025 Zhang Maiyun
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

import asyncio
import json
import sys
from os import PathLike
from pathlib import Path
from typing import Any, Dict


class DepManager:
    """Dependency Tracker.

    Args:
        depfile_path: Path to the dependency tracking file
        assume_yes: Whether to assume yes for all questions

    Dependency types:
        req: things that need to be built
        build: build tools that should be present on the computer
    """

    def __init__(self, depfile_path: PathLike[Any], assume_yes: bool = False):
        self.depfile_path = depfile_path
        if not Path(depfile_path).exists():
            with open(depfile_path, "w", encoding="utf-8") as depfile:
                json.dump({}, depfile)
        self._assume_yes = assume_yes

    def add(self, deptype: str, depname: str, succeeded: bool = True) -> None:
        """Mark a dependency as "built"."""
        with open(self.depfile_path, encoding="utf-8") as depfile:
            dep: Dict[str, Dict[str, bool]] = json.load(depfile)
        try:
            dep[deptype][depname] = succeeded
        except KeyError:
            dep[deptype] = {}
            dep[deptype][depname] = succeeded
        with open(self.depfile_path, "w", encoding="utf-8") as depfile:
            json.dump(dep, depfile)

    @staticmethod
    async def ask_build(depname: str) -> bool:
        """Ask the user if a build tool has been installed."""
        while True:
            print(f"Is {depname} installed on your system? [y/n] ", end="")
            sys.stdout.flush()
            resp = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            resp = resp.rstrip('\n').lower()
            if resp == "y":
                return True
            if resp == "n":
                print(f"Please install {depname}.")
            else:
                print("Unknown reply.")

    async def check(self, deptype: str, depname: str) -> bool:
        """Check if a dependency has been marked as "built"."""
        with open(self.depfile_path, encoding="utf-8") as depfile:
            dep: Dict[str, Dict[str, bool]] = json.load(depfile)
        try:
            return dep[deptype][depname]
        except KeyError:
            if deptype == "build" \
                    and (self._assume_yes or (await self.ask_build(depname))):
                self.add("build", depname)
                return True
            return False
