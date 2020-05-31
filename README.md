# zcbe

[![Build Status](https://travis-ci.com/myzhang1029/zcbe.svg)](https://travis-ci.com/myzhang1029/zcbe)
[![codecov](https://codecov.io/gh/myzhang1029/zcbe/branch/master/graph/badge.svg)](https://codecov.io/gh/myzhang1029/zcbe)
[![Maintainability](https://api.codeclimate.com/v1/badges/e8785246f7dbe7676393/maintainability)](https://codeclimate.com/github/myzhang1029/zcbe/maintainability)
## Introduction
The Z cross build environment is a tool for managing cross-compile environments.
It comes with concurrent building, dependency tracking and other useful features.

## Usage
### Tutorial
TODO
### CLI Usage
```
zcbe [-h] [-w] [-W WARNING] [-B] [-C CHDIR] [-f FILE] [-a] [-s]
            [-H ABOUT]
            [PROJ [PROJ ...]]

The Z Cross Build Environment

positional arguments:
  PROJ                  List of projects to build

optional arguments:
  -h, --help            show this help message and exit
  -w                    Suppress all warnings
  -W WARNING            Modify warning behavior
  -B, --rebuild         Force build requested projects and dependencies
  -C CHDIR, --chdir CHDIR
                        Change directory to
  -f FILE, --file FILE  Read FILE as build.toml
  -a, --all             Build all projects in mapping.toml
  -s, --silent          Silence make standard output
  -H ABOUT, --about ABOUT
                        Help on a topic("topics" for a list of topics)
```

