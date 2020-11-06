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

"""ZCBE project."""

import asyncio
import contextlib
import os
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, TextIO

import toml

from .env import expandvars as expand
from .exceptions import BuildError, MappingTOMLError, ProjectTOMLError

if TYPE_CHECKING:
    # pylint false positive
    # pylint: disable=cyclic-import
    from .build import Build


class Project:
    """Represents a project (see concepts).

    Args:
        proj_dir: the directory to the project
        proj_name: the name in mapping toml of the project
        builder: used to resolve dependencies, get warner and settings
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(self,
                 proj_dir: os.PathLike,
                 proj_name: str,
                 builder: "Build"
                 ):
        self._proj_dir = Path(proj_dir)
        if not self._proj_dir.is_dir():
            raise MappingTOMLError(
                f'project "{proj_name}" not found at {proj_dir}')
        self._proj_name = proj_name
        self._builder = builder
        self._warner = builder.get_warner()
        self._dep_manager = builder.get_dep_manager()
        self._settings = builder.get_settings()
        self._parse_conf_toml()

    def locate_conf_toml(self) -> Path:
        """Try to locate conf.toml.

        Possible locations:
            $ZCTOP/zcbe/{name}.zcbe/conf.toml
            ./zcbe/conf.toml
        """
        toplevel_try = Path(os.environ["ZCTOP"]) / \
            "zcbe"/(self._proj_name+".zcbe")/"conf.toml"
        if toplevel_try.exists():
            return toplevel_try
        local_try = self._proj_dir / "zcbe/conf.toml"
        if local_try.exists():
            return local_try
        raise ProjectTOMLError("conf.toml not found")

    async def solve_deps(self, depdict: Dict[str, List[str]]):
        """Solve dependencies.

        Args:
            depdict: dependency dictionary
        """
        message = "Dependency failed to build, stopping."
        # Circular dependency TODO
        # if False:
        #     say = f"Circular dependency found near {proj_name}"
        for table in depdict:
            if table == "build":
                for item in depdict[table]:
                    self._dep_manager.check(table, item)
            elif not await self._builder.build_many(depdict[table]):
                # table != "build"
                raise BuildError(message)
            # table == "build" or build_many returned True

    def _parse_conf_toml(self):
        """Load the conf toml and set envs."""
        # Make sure of conf.toml's presence
        conf_toml = self.locate_conf_toml()
        # TOML decode the file
        cdict = toml.load(conf_toml)
        pkg = cdict["package"]
        try:
            self._package_name = pkg["name"]
            if self._package_name != self._proj_name:
                # conf.toml and mapping.toml specified different project names.
                # those config files could have been copied from elsewhere, so
                # possibly some other adaptations haven't been done
                self._warner.warn(
                    "name-mismatch",
                    f"{self._package_name} mismatches with {self._proj_name}"
                )
            self._version = pkg["ver"]
        except KeyError as err:
            raise ProjectTOMLError(
                f"Expected key `package.{err}' not found") from err
        self._depdict = cdict["deps"] if "deps" in cdict else {}
        self._envdict = cdict["env"] if "env" in cdict else {}

    async def acquire_lock(self):
        """Acquires project build lock."""
        lockfile = self._proj_dir / "zcbe.lock"
        while lockfile.exists():
            self._warner.warn("lock-exists",
                              f"Lock file {lockfile} exists")
            await asyncio.sleep(10)
        lockfile.touch()

    async def release_lock(self):
        """Releases project build lock."""
        lockfile = self._proj_dir / "zcbe.lock"
        if lockfile.exists():
            lockfile.unlink()

    @contextlib.asynccontextmanager
    async def locked(self):
        """With statement for build locks."""
        await self.acquire_lock()
        try:
            yield
        finally:
            await self.release_lock()

    async def _get_stdout(self) -> Optional[TextIO]:
        """Get stdout after expanding {n} to self._proj_name."""
        stdout = self._settings["stdout"]
        return open(stdout.format(n=self._proj_name), "a") if stdout else None

    async def _get_stderr(self) -> Optional[TextIO]:
        """Get stderr after expanding {n} to self._proj_name."""
        stderr = self._settings["stderr"]
        return open(stderr.format(n=self._proj_name), "a") if stderr else None

    async def build(self):
        """Solve dependencies and build the project."""
        # Solve dependencies recursively
        await self.solve_deps(self._depdict)
        # Not infecting the environ of other projects
        # Expand sh-style variable
        environ = {**os.environ, **
                   {k: expand(self._envdict[k]) for k in self._envdict}}
        # Make sure no two build processes run in the same project
        async with self.locked():
            # Check if this project has already been built
            # Skip if if_rebuild is set to True
            if not self._settings["rebuild"] and \
                    self._dep_manager.check("req", self._proj_name):
                print(f"Requirement already satisfied: {self._proj_name}")
                return
            print(f"Entering project {self._proj_name}")
            # START #3 TODO
            buildsh = self.locate_conf_toml().parent / "build.sh"
            shpath = buildsh.as_posix()
            os.chdir(self._proj_dir)
            process = await asyncio.create_subprocess_exec(
                "sh" if not self._settings["dryrun"] else "true",
                "-e",
                shpath,
                stdout=await self._get_stdout(),
                stderr=await self._get_stderr(),
                env=environ,
            )
            # END #3 TODO
            await process.wait()
            print(f"Leaving project {self._proj_name} with status "
                  f"{process.returncode}")
        if process.returncode:
            # Build failed
            # Lock is still released as no one is writing to that directory
            message = (
                f'Command "sh -e {shpath}" returned non-zero exit status'
                f" {process.returncode}."
            )
            raise BuildError(message)
        # process.returncode == 0, succeeded
        if not self._settings["dryrun"]:
            # write recipe
            self._dep_manager.add("req", self._proj_name)
