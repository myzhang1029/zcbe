# zcbe

[![Build Status](https://travis-ci.com/myzhang1029/zcbe.svg)](https://travis-ci.com/myzhang1029/zcbe)
![Python package](https://github.com/myzhang1029/zcbe/workflows/Python%20package/badge.svg)
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
zcbe [-h] [-w] [-W WARNING] [-B] [-C CHDIR] [-o FILE] [-e FILE]
            [-f FILE] [-a] [-s] [-n] [-u] [-H ABOUT]
            [PROJ [PROJ ...]]

The Z Cross Build Environment

positional arguments:
  PROJ                  List of projects to build

optional arguments:
  -h, --help            show this help message and exit
  -w                    Suppress all warnings
  -W WARNING            Modify warning behavior
  -B, --rebuild, --always-make, --always-build
                        Force build requested projects and dependencies
  -C CHDIR, --chdir CHDIR, --directory CHDIR
                        Change directory to
  -o FILE, --stdout-to FILE
                        Redirect stdout to FILE ('{n}' expands to the name of
                        the project)
  -e FILE, --stderr-to FILE
                        Redirect stderr to FILE ('{n}' expands to the name of
                        the project)
  -f FILE, --file FILE, --build-toml FILE
                        Read FILE as build.toml
  -a, --all             Build all projects in mapping.toml
  -s, --silent          Silence make standard output(short for -o /dev/null)
  -n, --dry-run, --just-print, --recon
                        Don't actually run any commands
  -u, --show-unbuilt    List unbuilt projects and exit
  -H ABOUT, --about ABOUT
                        Help on a topic("topics" for a list of topics)
```
