# zcbe/exceptions.py
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

"""ZCBE exceptions and error handling."""
import sys

__all__ = ["BuildError", "ConfigError", "BuildTOMLError",
           "MappingTOMLError", "ProjectTOMLError", "eprint"]


class BuildError(Exception):
    """Exception raised when build failed."""


class ConfigError(Exception):
    """Base exception raised when configs are faluty."""


class BuildTOMLError(ConfigError):
    """Exception raised when build.toml is faluty."""


class MappingTOMLError(ConfigError):
    """Exception raised when mapping.toml is faluty."""


class ProjectTOMLError(ConfigError):
    """Exception raised when conf.toml is faluty."""


def eprint(*args, title="Error: ", **kwargs):
    """Print to stderr, use title as the starting if supplied."""
    if title:
        print("zcbe ***", title, end='', file=sys.stderr)
    print(*args, file=sys.stderr, **kwargs)
