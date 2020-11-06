# zcbe/build.py
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

"""ZCBE build."""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import toml

from .dep_manager import DepManager
from .env import expandvars as expand
from .exceptions import BuildTOMLError, MappingTOMLError, eprint
from .project import Project
from .warner import ZCBEWarner

if sys.version_info >= (3, 8):
    # pylint: disable=no-name-in-module
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


class BuildSettings(TypedDict, total=False):
    """Container for build settings."""
    # Whether to build even if the project has been built
    rebuild: bool
    # Whether to dry run
    dryrun: bool
    # Stdout filenames
    stdout: Optional[str]
    # Stderr filename
    stderr: Optional[str]
    # Top level
    build_dir: Path
    # Path() to build.toml
    build_toml_path: Path
    # Path() to mapping.toml
    mapping_toml_path: Path
    # Name of this build
    build_name: str
    # Prefix
    prefix: Path
    # Host triplet
    host: str


class Build:
    """Represents a build (see concepts).

    Args:
        build_dir: Directory of the build root
        warner: ZCBE warner
        if_rebuild: whether to ignore recipe and force rebuild
        if_dryrun: whether to dry run
        build_toml_filename: override build.toml's file name
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(
            self,
            build_dir: str,
            warner: ZCBEWarner,
            *,
            if_rebuild: bool = False,
            if_dryrun: bool = False,
            build_toml_filename: str = "build.toml",
            stdout: Optional[str] = None,
            stderr: Optional[str] = None

    ):
        self._warner = warner
        build_dir_path = Path(build_dir).resolve()
        self._settings: BuildSettings = {
            "rebuild": if_rebuild,
            "dryrun": if_dryrun,
            "stdout": stdout,
            "stderr": stderr,
            "build_dir": build_dir_path,
            "build_toml_path": build_dir_path / build_toml_filename,
            # Default value, can be overridden in build.toml
            "mapping_toml_path": build_dir_path / "mapping.toml",
        }
        self._build_bus: Dict[str, asyncio.Task] = {}
        self._parse_build_toml()

    def _parse_build_toml(self):
        """Load the build toml (i.e. top level conf) and set environ."""
        build_toml: Path = self._settings["build_toml_path"]
        if not build_toml.exists():
            raise BuildTOMLError("build toml not found")
        bdict = toml.load(build_toml)
        info = bdict["info"]
        try:
            # Read configuration parameters
            more_settings = {
                "build_name": info["build-name"],
                "prefix": Path(info["prefix"]).resolve(),
                "host": info["hostname"],
            }
            self._settings.update(more_settings)
            # Make sure prefix exists and is a directory
            self._settings["prefix"].mkdir(parents=True, exist_ok=True)
            # Initialize dependency and built recorder
            self._dep_manager = DepManager(
                self._settings["prefix"] / "zcbe.recipe")
            os.environ["ZCPREF"] = self._settings["prefix"].as_posix()
            os.environ["ZCHOST"] = self._settings["host"]
            os.environ["ZCTOP"] = self._settings["build_dir"].as_posix()
        except KeyError as err:
            raise BuildTOMLError(
                f"Expected key `info.{err}' not found") from err
        # Override default mapping file name
        if "mapping" in info:
            self._settings["mapping_toml_path"] = \
                self._settings["build_dir"] / info["mapping"]
        if not self._settings["mapping_toml_path"].exists():
            raise MappingTOMLError("mapping toml not found")
        if "env" in bdict:
            edict = bdict["env"]
            # Expand sh-style variable
            os.environ.update({k: expand(edict[k]) for k in edict})
        # Build-wide dependency - only build key is allowed
        if "deps" in bdict:
            for key in bdict["deps"]:
                if key != "build":
                    raise BuildTOMLError("Unexpected global dependency type "
                                         f"`deps.{key}'. Only \"build\" "
                                         "dependencies are allowed here")
                for item in bdict["deps"]["build"]:
                    self._dep_manager.check("build", item)

    def get_proj_path(self, proj_name: str) -> Path:
        """Get a project's root directory by looking up mapping toml.

        Args:
            projname: The name of the project to look up
        """
        mapping_toml = self._settings["mapping_toml_path"]
        if not mapping_toml.exists():
            raise MappingTOMLError("mapping toml not found")
        mapping = toml.load(mapping_toml)["mapping"]
        try:
            return self._settings["build_dir"] / mapping[proj_name]
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
        mapping_toml = self._settings["mapping_toml_path"]
        mapping = toml.load(mapping_toml)["mapping"]
        return await self.build_many(list(mapping))

    async def _build_proj_wrapper(self, proj_name: str):
        """A single coroutine including everything about calling Project.build.

        Args:
            proj_name: the name of the project
        """
        proj = self.get_proj(proj_name)
        await proj.build()

    def build(self, proj_name: str) -> asyncio.Task:
        """Build a project.

        Args:
            proj_name: the name of the project

        Return:
            The asyncio.Task of the build process
        """
        # A build already in progress
        if proj_name in self._build_bus:
            return self._build_bus[proj_name]
        build_task = asyncio.create_task(self._build_proj_wrapper(proj_name))
        self._build_bus[proj_name] = build_task
        return build_task

    async def build_many(self, projs: List[str]) -> bool:
        """Asynchronously build many projects.

        Args:
            projs: List of project names to be built

        Return:
            whether all projects succeeded.
        """
        if not projs:
            # Filter out empty build requests
            return True
        successful = True
        tasks = [self.build(item) for item in projs]
        await asyncio.wait(tasks)
        for idx, task in enumerate(tasks):
            exception_maybe = task.exception()
            if exception_maybe:
                successful = False
                eprint(f'Project "{projs[idx]}" failed:')
                eprint(exception_maybe, title=None)
        return successful

    def show_unbuilt(self) -> bool:
        """Show all unbuilt projects.

        Return False if everything has been built, otherwise True
        """
        mapping_toml = self._settings["mapping_toml_path"]
        mapping = toml.load(mapping_toml)["mapping"]
        ret = False
        for proj in mapping:
            if not self._dep_manager.check("req", proj):
                ret = True
                print(proj)
        return ret

    def get_warner(self) -> ZCBEWarner:
        """Return the internal warner used."""
        return self._warner

    def get_dep_manager(self) -> DepManager:
        """Return the dependency manager used."""
        return self._dep_manager

    def get_settings(self) -> BuildSettings:
        """Return the settings dictionary."""
        return self._settings
