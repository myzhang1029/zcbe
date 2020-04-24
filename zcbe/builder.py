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

import toml
import os
import asyncio
import contextlib
import textwrap
from pathlib import Path
from typing import Dict, List
from .dep_manager import DepManager
from .warner import ZCBEWarner
from .exceptions import *


class Build:
    """Represents a build (see concepts).
    build_dir: Directory of the build root
    warner: ZCBE warner
    if_silent: whether to silence make stdout
    if_rebuild: whether to ignore recipe and force rebuild
    build_toml_filename: override build.toml's file name
    """

    def __init__(
        self,
        build_dir: str,
        warner: ZCBEWarner,
        if_silent: bool = False,
        if_rebuild: bool = False,
        build_toml_filename: str = "build.toml"
    ):
        self.build_dir = Path(build_dir).absolute()
        self.build_toml = self.build_dir / build_toml_filename
        self.warner = warner
        self.if_silent = if_silent
        self.if_rebuild = if_rebuild
        # Default value, can be overridden in build.toml
        self.mapping_toml_filename = "mapping.toml"
        if self.build_toml.exists():
            self.parse_build_toml()
        else:
            raise BuildTOMLError("build toml not found")

    def parse_build_toml(self):
        """Load the build toml (i.e. top level conf) and set envs."""
        bdict = toml.load(self.build_toml)
        info = bdict["info"]
        try:
            # Read configuration parameters
            self.build_name = info["build-name"]
            self.prefix = info["prefix"]
            self.host = info["hostname"]
            # Make sure prefix exists and is a directory
            Path(self.prefix).mkdir(parents=True, exist_ok=True)
            # Initialize dependency and built recorder
            self.dep_manager = DepManager(self.prefix+"/zcbe.recipe")
            os.environ["ZCPREF"] = self.prefix
            os.environ["ZCHOST"] = self.host
            os.environ["ZCTOP"] = self.build_dir.as_posix()
        except KeyError as e:
            raise BuildTOMLError(f"Expected key `info.{e}' not found")
        # Override default mapping file name
        if "mapping" in info:
            self.mapping_toml_filename = info["mapping"]
        if "env" in bdict:
            os.environ = {**os.environ, **bdict["env"]}

    def get_proj_path(self, proj_name: str) -> Path:
        """Get a project's root directory by looking up the mapping toml.
        projname: The name of the project to look up
        """
        self.mapping_toml = self.build_dir / self.mapping_toml_filename
        if not self.mapping_toml.exists():
            raise MappingTOMLError("mapping toml not found")
        mapping = toml.load(self.mapping_toml)["mapping"]
        try:
            return self.build_dir / mapping[proj_name]
        except KeyError as e:
            raise MappingTOMLError(f'project "{proj_name}" not found') from e

    def get_proj(self, proj_name: str):
        """Returns a project instance.
        projname: The name of the project
        """
        proj_path = self.get_proj_path(proj_name)
        return Project(proj_path, proj_name, self)

    async def build_all(self):
        """Build all projects in mapping toml."""
        self.mapping_toml = self.build_dir / self.mapping_toml_filename
        if not self.mapping_toml.exists():
            raise MappingTOMLError("mapping toml not found")
        mapping = toml.load(self.mapping_toml)["mapping"]
        return await self.build_many([p for p in mapping])

    async def build(self, proj_name: str):
        """Build a project.
        proj_name: the name of the project
        """
        proj = self.get_proj(proj_name)
        # Circular dependency TODO
        if False:
            say = f'Circular dependency found near "{proj_name}"'
        await proj.build(if_rebuild=self.if_rebuild)

    async def build_many(self, projs: List[str]) -> bool:
        """Asynchronously build many projects.
        projs: List of project names to be built
        Returns whether the operations didn't raise anything.
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


class Project:
    """Represents a project (see concepts).
    proj_dir is the directory to the project
    proj_name is the name in mapping toml of the project
    builder is used to resolve dependencies, get warner and get if_silent
    """

    def __init__(self,
                 proj_dir: os.PathLike,
                 proj_name: str,
                 builder: Build
                 ):
        self.proj_dir = Path(proj_dir)
        if not self.proj_dir.is_dir():
            raise MappingTOMLError(
                f"project {proj_name} not found at {proj_dir}")
        self.proj_name = proj_name
        self.builder = builder
        self.warner = builder.warner
        self.if_silent = builder.if_silent
        self.environ = os.environ
        self.conf_toml = self.locate_conf_toml()
        if self.conf_toml.exists():
            self.parse_conf_toml()
        else:
            raise ProjectTOMLError("conf.toml not found")

    def locate_conf_toml(self) -> Path:
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

    async def solve_deps(self, depdict: Dict[str, List[str]]):
        """Solve dependencies."""
        for table in depdict:
            if table == "build":
                for item in depdict[table]:
                    self.builder.dep_manager.check(table, item)
            else:
                if not await self.builder.build_many(depdict[table]):
                    raise BuildError("Dependency failed to build, stopping.")

    def parse_conf_toml(self):
        """Load the conf toml and set envs."""
        cdict = toml.load(self.conf_toml)
        pkg = cdict["package"]
        try:
            self.package_name = pkg["name"]
            if self.package_name != self.proj_name:
                self.warner.warn(
                    "name-mismatch",
                    f'"{self.package_name}" mismatches with "{self.proj_name}"'
                )
            self.version = pkg["ver"]
        except KeyError as e:
            raise ProjectTOMLError(f"Expected key `package.{e}' not found")
        self.depdict = cdict["deps"] if "deps" in cdict else {}
        self.envdict = cdict["env"] if "env" in cdict else {}

    async def acquire_lock(self):
        """Acquires project build lock."""
        lockfile = self.proj_dir / "zcbe.lock"
        while lockfile.exists():
            message = (f"The lockfile for project {self.proj_name} exists. "
                       "If you're running multiple builds at the same time, "
                       "don't worry and we'll automatically proceed. "
                       "Otherwise please kill this process and remove "
                       f'the lock file "{lockfile}" '
                       "by yourself. After that, check if everything is OK.")
            eprint('\n'.join(textwrap.wrap(message, 75)))
            await asyncio.sleep(10)
        lockfile.touch()

    async def release_lock(self):
        """Releases project build lock."""
        lockfile = self.proj_dir / "zcbe.lock"
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
        if_rebuild: whether to ignore recipe and force rebuild
        """
        # Solve dependencies recursively
        await self.solve_deps(self.depdict)
        # Not infecting the environ of other projects
        for item in self.envdict:
            self.environ[item] = self.envdict[item]
        # Make sure no two zcbes run in the same project
        async with self.locked():
            # Check if this project has already been built
            # Skip if if_rebuild is set to True
            if not if_rebuild and \
                    self.builder.dep_manager.check("req", self.proj_name):
                print(f"Requirement already satisfied: {self.proj_name}")
                return
            print(f"Entering project {self.proj_name}")
            buildsh = self.locate_conf_toml().parent / "build.sh"
            shpath = buildsh.as_posix()
            os.chdir(self.proj_dir)
            process = await asyncio.create_subprocess_exec(
                "sh",
                "-e",
                shpath,
                stdout=asyncio.subprocess.DEVNULL if self.if_silent else None,
                env=self.environ,
            )
            await process.wait()
            print(f"Leaving project {self.proj_name}")
        if process.returncode:
            # Build failed
            # Lock is still released as no one is writing to that directory
            raise BuildError(
                f"Command 'sh -e {shpath}' returned non-zero exit status"
                f"{process.returncode}."
            )
        # write recipe
        self.builder.dep_manager.add("req", self.proj_name)
