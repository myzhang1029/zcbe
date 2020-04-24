# zcbe.py - The Z Cross Build Environment
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

"""The Z Cross Build Environment.
Concepts:
    a build contains many projects
    a projects is just a program/package
"""

import os
import sys
import argparse
import asyncio
from .exceptions import eprint
from .warner import ZCBEWarner
from .builder import Build

# All available types of warnings (gcc-like)
all_warnings = {
    "name-mismatch": "The project's name specified in conf.toml "
                     "mismatches with that in mapping.toml",
    "generic": "Warnings about ZCBE itself",
    "error": "Error all warnings",
    "all": "Show all warnings",
}

# Gather help strings for all warnings
warnings_help = '\n'.join(
    ["{}: {}".format(x, all_warnings[x]) for x in all_warnings])

default_warnings = set((
    "name-mismatch",
    "generic",
)) & set(all_warnings)

# Help topics and their help message
topics = {
    "topics": "topics: This list of topics\n"
              "warnings: All available warnings\n",
    "warnings": warnings_help,
}


class AboutAction(argparse.Action):
    """Argparse action to show help topics. Exits when finished."""

    def __init__(self, option_strings, dest, nargs=1, **kwargs):
        super().__init__(option_strings, dest, nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        name = values[0]
        try:
            eprint(topics[name], title="")
        except KeyError:
            eprint(f'No such topic "{name}", try "topics" for available ones')
        sys.exit(0)


class WarningsAction(argparse.Action):
    """Argparse action to modify warning behaviour."""

    def __init__(self, option_strings, dest, nargs=1, **kwargs):
        super().__init__(option_strings, dest, nargs, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        reverse = False
        name = values[0]
        if name[0:3] == "no-":
            reverse = True
            name = name[3:]
        if name not in all_warnings:
            warner.warn("generic", f'No such warning "{name}"')
            return
        if reverse:
            warner.setopts({name: False})
        else:
            warner.setopts({name: True})


def start():
    ap = argparse.ArgumentParser(description="The Z Cross Build Environment")
    ap.add_argument("-w", help="Suppress all warnings", action="store_true")
    ap.add_argument("-W", metavar="WARNING",
                    help="Modify warning behaviour", action=WarningsAction)
    ap.add_argument("-C", "--chdir", type=str, help="Change directory to")
    ap.add_argument("-s", "--silent", action="store_true",
                    help="Silence make standard output")
    ap.add_argument("-H", "--about", type=str, action=AboutAction,
                    help='Help on a topic("topics" for a list of topics)')
    ap.add_argument('projects', metavar='PROJ', nargs='+',
                    help='List of projects to build')
    ns = ap.parse_args()
    if ns.w:
        warner.silence()
    if ns.chdir:
        os.chdir(ns.chdir)
    return asyncio.run(main(".", ns.projects, ns.silent))


async def main(projdir, to_build, if_silent):
    # Set up the warner to use
    warner = ZCBEWarner()
    warner.load_default(set(all_warnings), default_warnings)
    # Disable the traceback here so it won't flood the error message
    sys.tracebacklimit = 0
    builder = Build(projdir, warner, if_silent=if_silent)
    success = await builder.build_many(to_build)
    return 0 if success else 1
