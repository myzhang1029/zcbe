#!/usr/bin/env python
# setup.py - easy_install script for zcbe
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

"""Setuptools script for ZCBE."""

from setuptools import setup

setup(
    name="zcbe",
    version="0.3.2",
    description="The Z Cross Build Environment",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Zhang Maiyun",
    author_email="myzhang1029@hotmail.com",
    url="https://github.com/myzhang1029/zcbe",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
    ],
    python_requires='>=3.7',
    packages=["zcbe"],
    install_requires=["toml"],
    extras_require={
        ":python_version<'3.8'": ["typing_extensions"]
    },
    entry_points={
        "console_scripts": [
            "zcbe = zcbe:start"
        ]
    }
)
