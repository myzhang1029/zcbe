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
import argparse
from .warner import ZCBEWarner
from .builder import Build

all_warnings = {
    "name-mismatch": "The project's name specified in conf.toml mismatches with that in mapping.toml",
    "generic": "Warnings about ZCBE itself",
    "error": "Error all warnings",
    "all": "Show all warnings",
}

default_warnings = set((
    "name-mismatch",
    "generic",
)) & set(all_warnings)


warner = ZCBEWarner()
warner.load_default(set(all_warnings), default_warnings)


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
        if not name in all_warnings:
            warner.warn("generic", f"No such warning `{name}'")
            return
        if reverse:
            warner.setopts({name: False})
        else:
            warner.setopts({name: True})


def start():
    ap = argparse.ArgumentParser(description="The Z Cross Build Environment")
    ap.add_argument("-w", help="Suppress all warnings", action="store_true")
    ap.add_argument(
        "-W", help="Modify warning behaviour", action=WarningsAction)
    ap.add_argument("-C", "--chdir", type=str, help="Change directory to")
    # ap.add_argument("-p", "--project-directory",
    #                type=str, help="Specify project root")
    ap.add_argument('projects', metavar='PROJ', nargs='+',
                    help='List of projects to build')
    ns = ap.parse_args()
    if ns.w:
        warner.silence()
    if ns.chdir:
        os.chdir(ns.chdir)
    main(".", ns.projects)


def main(projdir, to_build):
    with Build(projdir, warner) as proj:
        for one in to_build:
            proj.build(one)
