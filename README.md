# RadSSH

[![CI](https://github.com/hsmalley/radssh/workflows/CI/badge.svg)](https://github.com/hsmalley/radssh/actions/workflows/ci.yml)
[![Code Quality](https://github.com/hsmalley/radssh/workflows/Code%20Quality/badge.svg)](https://github.com/hsmalley/radssh/actions/workflows/code-quality.yml)
[![Security](https://github.com/hsmalley/radssh/workflows/Security%20Scan/badge.svg)](https://github.com/hsmalley/radssh/actions/workflows/security.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-BSD-green.svg)](LICENSE.txt)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

RadSSH is a Python package built with Paramiko that enables you to execute commands across multiple SSH hosts simultaneously.

## Features

- Execute commands on dozens or hundreds of hosts simultaneously
- Interactive shell interface with familiar SSH syntax
- Plugin system for extensibility
- High-level API for building custom applications
- Modern Python 3.12+ support with type hints
- Comprehensive test suite and CI/CD

## Installation

```bash
pip install radssh
```

## Quick Start

----

The RadSSH shell behaves similar to a normal ssh command line client, but instead of connecting to one host (at a time), you can connect to dozens or even hundreds at a time, and issue interactive command lines to all hosts at once. It requires very little learning curve to get started, and leverages on existing command line syntax that you already know.

```
[paul@localhost ~]$ python -m radssh.shell huey dewey louie
Please enter a password for (paul) :
Connecting to 3 hosts...
...
RadSSH $ hostname
[huey] huey.example.org
[dewey] dewey.example.org
[louie] louie.example.org
Average completion time for 3 hosts: 0.058988s

RadSSH $ uptime
[huey]  15:21:28 up 6 days, 22:49, 17 users,  load average: 0.30, 0.43, 0.39
[louie] 15:43  up 652 days,  4:59, 0 users, load averages: 0.44 0.20 0.17
[dewey]  15:21:28 up 109 days, 23:28,  3 users,  load average: 0.27, 0.09, 0.07
Average completion time for 3 hosts: 0.044532s

RadSSH $ df -h /
[huey] Filesystem            Size  Used Avail Use% Mounted on
[huey] /dev/mapper/vg-Scientific
[huey]                        24G   22G  694M  97% /
[louie] Filesystem     Size   Used  Avail Capacity  Mounted on
[louie] /dev/disk0s3   234G   134G    99G    57%    /
[dewey] Filesystem                        Size  Used Avail Use% Mounted on
[dewey] /dev/mapper/vg_pkapp745-LogVol00   20G   17G  2.1G  89% /
Average completion time for 3 hosts: 0.036792s

RadSSH $ *exit
Shell exiting
```

RadSSH includes a loadable plugin facility to extend the functionality of the shell with basic Python scripting, as well as a high level API that can be used to build stand alone applications for dedicated SSH control processing in a parallel environment.

Interested in more? 
 - Download at https://pypi.python.org/pypi/radssh
 - Read the Docs at http://radssh.readthedocs.org/en/latest/index.html
 - Participate at https://github.com/radssh/radssh
