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

import os
import asyncio
import contextlib
import textwrap
from pathlib import Path
from typing import Dict, List
import toml
from .env import expandvars as expand
from .dep_manager import DepManager
from .warner import ZCBEWarner
from .exceptions import BuildError, BuildTOMLError, MappingTOMLError, \
    ProjectTOMLError, eprint


class Build:
    """Represents a build (see concepts).

    Args:
        build_dir: Directory of the build root
        warner: ZCBE warner
        if_silent: whether to silence make stdout
        if_rebuild: whether to ignore recipe and force rebuild
        build_toml_filename: override build.toml's file name
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(
            self,
            build_dir: str,
            warner: ZCBEWarner,
            *,
            if_silent: bool = False,
            if_rebuild: bool = False,
            build_toml_filename: str = "build.toml"
    ):
        self._warner = warner
        self._if_silent = if_silent
        self._if_rebuild = if_rebuild
        self._build_dir = Path(build_dir).resolve()
        self._build_toml_filename = build_toml_filename
        # Default value, can be overridden in build.toml
        self._mapping_toml_filename = "mapping.toml"
        self.parse_build_toml()

    def parse_build_toml(self):
        """Load the build toml (i.e. top level conf) and set envs."""
        build_toml = self._build_dir / self._build_toml_filename
        if not build_toml.exists():
            raise BuildTOMLError("build toml not found")
        bdict = toml.load(build_toml)
        info = bdict["info"]
        try:
            # Read configuration parameters
            self._build_name = info["build-name"]
            self._prefix = Path(info["prefix"]).resolve()
            self._host = info["hostname"]
            # Make sure prefix exists and is a directory
            self._prefix.mkdir(parents=True, exist_ok=True)
            # Initialize dependency and built recorder
            self._dep_manager = DepManager(self._prefix/"zcbe.recipe")
            os.environ["ZCPREF"] = self._prefix.as_posix()
            os.environ["ZCHOST"] = self._host
            os.environ["ZCTOP"] = self._build_dir.as_posix()
        except KeyError as err:
            raise BuildTOMLError(f"Expected key `info.{err}' not found")
        # Override default mapping file name
        if "mapping" in info:
            self._mapping_toml_filename = info["mapping"]
        if "env" in bdict:
            edict = bdict["env"]
            # Expand sh-style variable
            os.environ.update({k: expand(edict[k]) for k in edict})

    def get_proj_path(self, proj_name: str) -> Path:
        """Get a project's root directory by looking up mapping toml.

        Args:
            projname: The name of the project to look up
        """
        mapping_toml = self._build_dir / self._mapping_toml_filename
        if not mapping_toml.exists():
            raise MappingTOMLError("mapping toml not found")
        mapping = toml.load(mapping_toml)["mapping"]
        try:
            return self._build_dir / mapping[proj_name]
        except KeyError as err:
            raise MappingTOMLError(f'project "{proj_name}" not found') from err

    def get_proj(self, proj_name: str):
        """Get the Project instance corresponding to proj_name.

        Args:
            projname: The name of the project

        Return:
            Project
        """
        proj_path = self.get_proj_path(proj_name)
        return Project(proj_path, proj_name, self)

    async def build_all(self) -> bool:
        """Build all projects in mapping toml."""
        mapping_toml = self._build_dir / self._mapping_toml_filename
        if not mapping_toml.exists():
            raise MappingTOMLError("mapping toml not found")
        mapping = toml.load(mapping_toml)["mapping"]
        return await self.build_many(list(mapping))

    async def build(self, proj_name: str):
        """Build a project.

        Args:
            proj_name: the name of the project
        """
        proj = self.get_proj(proj_name)
        # Circular dependency TODO
        # if False:
        #     say = f'Circular dependency found near "{proj_name}"'
        await proj.build(if_rebuild=self._if_rebuild)

    async def build_many(self, projs: List[str]) -> bool:
        """Asynchronously build many projects.

        Args:
            projs: List of project names to be built

        Return:
            whether the operations didn't raise anything.
        """
        successful = True
        results = await asyncio.gather(
            *(self.build(item) for item in projs), return_exceptions=True)
        for idx, result in enumerate(results):
            if result is not None:
                successful = False
                eprint(f'Project "{projs[idx]}" raised an exception:')
                eprint(f"{type(result).__name__}: {result}", title=None)
        return successful

    def get_warner(self) -> ZCBEWarner:
        """Return the internal warner used."""
        return self._warner

    def get_dep_manager(self) -> DepManager:
        """Return the dependency manager used."""
        return self._dep_manager


class Project:
    """Represents a project (see concepts).

    Args:
        proj_dir: the directory to the project
        proj_name: the name in mapping toml of the project
        builder: used to resolve dependencies, get warner and if_silent
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(self,
                 proj_dir: os.PathLike,
                 proj_name: str,
                 builder: Build
                 ):
        self._proj_dir = Path(proj_dir)
        if not self._proj_dir.is_dir():
            raise MappingTOMLError(
                f"project {proj_name} not found at {proj_dir}")
        self._proj_name = proj_name
        self._builder = builder
        self._warner = builder.get_warner()
        self._dep_manager = builder.get_dep_manager()
        self._if_silent = builder._if_silent
        self.parse_conf_toml()

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
        """Solve dependencies."""
        for table in depdict:
            if table == "build":
                for item in depdict[table]:
                    self._dep_manager.check(table, item)
            else:
                if not await self._builder.build_many(depdict[table]):
                    raise BuildError("Dependency failed to build, stopping.")

    def parse_conf_toml(self):
        """Load the conf toml and set envs."""
        # Make sure of conf.toml's presence
        conf_toml = self.locate_conf_toml()
        if not conf_toml.exists():
            raise ProjectTOMLError("conf.toml not found")
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
                    f'"{self._package_name}" mismatches with '
                    f'{self._proj_name}"'
                )
            self._version = pkg["ver"]
        except KeyError as err:
            raise ProjectTOMLError(f"Expected key `package.{err}' not found")
        self._depdict = cdict["deps"] if "deps" in cdict else {}
        self._envdict = cdict["env"] if "env" in cdict else {}

    async def acquire_lock(self):
        """Acquires project build lock."""
        lockfile = self._proj_dir / "zcbe.lock"
        while lockfile.exists():
            message = (f"The lockfile for project {self._proj_name} exists. "
                       "This is usually not a worry, as ZCBE builds multiple "
                       "projects simultaneously. If this warning persists "
                       "for a long while, please kill this process and "
                       f'remove the lock file "{lockfile}" '
                       "by yourself, and check if everything is OK.")
            eprint('\n'.join(textwrap.wrap(message, 75)), title="Warning: ")
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

    async def build(self, if_rebuild: bool = False):
        """Solve dependencies and build the project.

        Args:
            if_rebuild: whether to ignore recipe and force rebuild
        """
        # Solve dependencies recursively
        await self.solve_deps(self._depdict)
        # Not infecting the environ of other projects
        # Expand sh-style variable
        environ = {**os.environ, **
                   {k: expand(self._envdict[k]) for k in self._envdict}}
        # Make sure no two zcbes run in the same project
        async with self.locked():
            # Check if this project has already been built
            # Skip if if_rebuild is set to True
            if not if_rebuild and \
                    self._dep_manager.check("req", self._proj_name):
                print(f"Requirement already satisfied: {self._proj_name}")
                return
            print(f"Entering project {self._proj_name}")
            buildsh = self.locate_conf_toml().parent / "build.sh"
            shpath = buildsh.as_posix()
            os.chdir(self._proj_dir)
            process = await asyncio.create_subprocess_exec(
                "sh",
                "-e",
                shpath,
                stdout=asyncio.subprocess.DEVNULL if self._if_silent else None,
                env=environ,
            )
            await process.wait()
            print(f"Leaving project {self._proj_name}")
        if process.returncode:
            # Build failed
            # Lock is still released as no one is writing to that directory
            raise BuildError(
                f"Command 'sh -e {shpath}' returned non-zero exit status"
                f"{process.returncode}."
            )
        # write recipe
        self._dep_manager.add("req", self._proj_name)
