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
    from typing import TypedDict  # pragma: no cover
else:
    from typing_extensions import TypedDict  # pragma: no cover


class AsyncNullContext:
    """Empty async context manager."""

    def __init__(self):
        pass

    async def __aenter__(self):
        pass

    async def __aexit__(self, *args):
        pass


class BuildSettings(TypedDict, total=False):
    """Container for build settings."""
    # Whether to build even if the project has been built
    rebuild: bool
    # Whether to dry run
    dryrun: bool
    # Whether to assume yes for all questions
    assume_yes: bool
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
    # Environment variables
    environ: Optional[Dict[str, str]]
    # Global build-time dependencies
    deps: Optional[Dict[str, str]]
    # Target triplet
    triplet: str


class Build:
    """Represents a build (see concepts).

    Args:
        build_dir: Directory of the build root
        warner: ZCBE warner
        if_rebuild: whether to ignore recipe and force rebuild
        if_dryrun: whether to dry run
        build_toml_filename: override build.toml's file name
        stdout: filename to redirect stdout into
        stderr: filename to redirect stderr into
        max_jobs: number of maximum jobs
        assume_yes: whether to assume yes for all questions
        override_build_name: an overriding value for the name of this build
        override_prefix: an overriding value for the prefix
        override_triplet: an overriding value for the target triplet
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
            stderr: Optional[str] = None,
            max_jobs: Optional[int] = 0,
            assume_yes: bool = False,
            override_build_name: str = None,
            override_prefix: str = None,
            override_triplet: str = None,
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
            "assume_yes": assume_yes,
        }
        self._build_bus: Dict[str, asyncio.Task] = {}
        self.job_semaphore = asyncio.Semaphore(
            max_jobs) if max_jobs else AsyncNullContext()
        self._parse_build_toml(override_build_name,
                               override_prefix, override_triplet)
        self._check_config()
        self._set_global_env()
        self._resolve_global_deps()

    def _parse_build_toml(self,
                          override_build_name: str = None,
                          override_prefix: str = None,
                          override_triplet: str = None
                          ):
        """Load the build toml (i.e. top level conf) and set environ."""
        build_toml: Path = self._settings["build_toml_path"]
        if not build_toml.exists():
            raise BuildTOMLError("build toml not found")
        bdict = toml.load(build_toml)
        try:
            info = bdict["info"]
            # Read configuration parameters
            self._settings.update({
                "build_name": override_build_name or info["build-name"],
                "prefix": Path(override_prefix or info["prefix"]).resolve(),
                "triplet": override_triplet or info["hostname"],
            })
        except KeyError as err:
            raise BuildTOMLError(
                "Incomplete or missing `info' section") from err
        # Override default mapping file name
        if "mapping" in info:
            self._settings["mapping_toml_path"] = \
                self._settings["build_dir"] / info["mapping"]
        self._settings["environ"] = bdict["env"] if "env" in bdict else {}
        self._settings["deps"] = bdict["deps"] if "deps" in bdict else {}

    def _resolve_global_deps(self):
        """Check global build-time dependencies."""
        # Build-wide dependency - only build key is allowed
        for key in self._settings["deps"]:
            if key != "build":
                raise BuildTOMLError("Unexpected global dependency type "
                                     f"`deps.{key}'. Only \"build\" "
                                     "dependencies are allowed here")
            for item in self._settings["deps"]["build"]:
                self._dep_manager.check("build", item)

    def _check_config(self):
        """Check provided configuration."""
        # Make sure prefix exists and is a directory
        self._settings["prefix"].mkdir(parents=True, exist_ok=True)
        # Initialize dependency and built recorder
        self._dep_manager = DepManager(
            self._settings["prefix"] / "zcbe.recipe",
            assume_yes=self._settings["assume_yes"])
        if not self._settings["mapping_toml_path"].exists():
            raise MappingTOMLError("mapping toml not found")

    def _set_global_env(self):
        """Set global environment variables."""
        os.environ["ZCPREF"] = self._settings["prefix"].as_posix()
        os.environ["ZCHOST"] = self._settings["triplet"]
        os.environ["ZCTOP"] = self._settings["build_dir"].as_posix()
        edict = self._settings["environ"]
        # Expand sh-style variable
        os.environ.update({k: expand(edict[k]) for k in edict})

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
        build_task = asyncio.create_task(
            self._build_proj_wrapper(proj_name))
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
