# Z Cross Build Environment

![Python Package](https://github.com/myzhang1029/zcbe/workflows/Python%20package/badge.svg)
![Upload Python Package](https://github.com/myzhang1029/zcbe/workflows/Upload%20Python%20Package/badge.svg)
[![codecov](https://codecov.io/gh/myzhang1029/zcbe/branch/master/graph/badge.svg)](https://codecov.io/gh/myzhang1029/zcbe)
[![Maintainability](https://api.codeclimate.com/v1/badges/e8785246f7dbe7676393/maintainability)](https://codeclimate.com/github/myzhang1029/zcbe/maintainability)
[![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/4158/badge)](https://bestpractices.coreinfrastructure.org/projects/4158)

## Introduction
The Z cross build environment is a tool for managing cross-compile environments.
It comes with concurrent building, dependency tracking and other useful features.

## Usage

### Installation
ZCBE is available on PyPI:
```shell
pip install zcbe
```

### Tutorial
0. Understanding concepts:
   - A "build" is an environment with multiple projects.
   - A "project" is a single package. They may depend on other projects.
1. The first step is to create a basic directory structure.
   ZCBE uses [TOML](https://toml.io/en/) as its configuration language.
   ```text
   .
   |-- build.toml
   |-- mapping.toml
   |-- zcbe/
      |-- PROJECT.zcbe/
         |-- conf.toml
         |-- build.sh
   |-- ...
   ```
   The sources of projects can be anywhere. But generally it's suggested that
   you put them somewhere under the build's root directory.
2. Then we can populate the configurations.
   - `build.toml`: This file describes how to prepare environment. For example,
     the installation prefix and host triplets are set in this file. Go to
     [`templates/build.toml`](templates/build.toml) for an example.
   - `mapping.toml`: This file sets the working directory for each projects.
     This directory can be absolute or relative to build root. An example is
     at [`templates/mapping.toml`](templates/mapping.toml).
   - `zcbe/*.zcbe`: Each project has a subdirectory here for holding their
     configuration, scripts and data.
   - `zcbe/*.zcbe/conf.toml`: This file contains the information about a project.
     The dependencies are specified here. An example is also available at
     [`templates/conf.toml`](templates/conf.toml).
   - `zcbe/*.zcbe/build.sh`: This is the build script.
3. Start building!
   - To build a single project and its dependencies, run `zcbe <NAME>`.
   - To build everything, pass `-a`.
   - To silence `stdout`, pass `-s`.
   - By default only one process is run at a time. To build concurrently, pass
     `-j <N>`.

   See [CLI Usage Section](#cli-usage) for a complete list of options.


## Contribution
For security-related issues, see [SECURITY.md](SECURITY.md).

Contributions are very welcome on GitHub. Please try to follow PEP-8 coding
guidelines and make sure test suites pass before submitting.

For new features and bug fixes, corresponding tests must be added.

The license is Apache-2.0.

## Usage References and Specifications

### CLI Usage
```text
usage: zcbe [-h] [-w] [-W WARNING] [-B] [-C CHDIR] [-o FILE] [-e FILE]
            [-f FILE] [-p PREFIX] [-t TARGET_TRIPLET] [-m BUILD_NAME]
            [-j JOBS] [-a] [-s] [-n] [-u] [-y] [-H ABOUT]
            [PROJ ...]

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
  -p PREFIX, --prefix PREFIX, --override-prefix PREFIX
                        Override value for prefix
  -t TARGET_TRIPLET, --target-triplet TARGET_TRIPLET, --override-target TARGET_TRIPLET
                        Override value for target triplet
  -m BUILD_NAME, --build-name BUILD_NAME, --override-build-name BUILD_NAME
                        Override value for build name
  -j JOBS, --jobs JOBS  Number of maximum concurrent jobs
  -a, --all             Build all projects in mapping.toml
  -s, --silent          Silence make standard output(short for -o /dev/null)
  -n, --dry-run, --just-print, --recon
                        Don't actually run any commands
  -u, --show-unbuilt    List unbuilt projects and exit
  -y, --yes             Assume yes for all questions
  -H ABOUT, --about ABOUT
                        Help on a topic("topics" for a list of topics)
```

### Environment Specification
In the build script, there are three environment variables set by ZCBE:
- `ZCTOP`: full path to the root of the build. That is, where `zcbe` is
  invoked or where the `-C` option points.
- `ZCPREF`: full path to the installation prefix.
- `ZCHOST`: GNU host triplet to cross compile for.

### `build.toml` Specification
Tables:
- `info`: required.  
  Keys:
  - `build_name`: name of this build environment. Required unless `-m`
    command-line option is set.
  - `prefix`: installation prefix. Required unless `-p` command-line option is
    set.
  - `hostname`: GNU triplet of the cross toolchain. Required unless `-t`
    command-line option is set.
  - `mapping`: Override path to `mapping.toml`. Optional. The default value is
    `"mapping.toml"`.
- `env`: optional. Contains any number of environmental variables which will
  be set for all projects.
- `deps`: optional.  
  Keys:
  - `build`: List of global build-time dependencies. Optional.

### `mapping.toml` Specification
Tables:
- `mapping`: required. Contains any number of key-value mappings from the
  project name to the project path, either absolute or relative to build root.

### `conf.toml` Specification
Tables:
- `package`: required.  
  Keys:
  - `name`: name of this project. Required.
  - `ver`: version of this project. Required.
- `env`: optional. Contains any number of environmental variables which will
  be set for only this projects.
- `deps`: optional.  
  Keys:
  - `build`: List of build-time dependencies. Optional.
  - `req`: List of dependencies on other projects. Optional.
