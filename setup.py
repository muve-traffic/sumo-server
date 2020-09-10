#!/usr/bin/env python

"""Shim to allow editable setuptools installs.

See https://snarky.ca/what-the-heck-is-pyproject-toml/ for more details.
"""

import setuptools

if __name__ == "__main__":
    setuptools.setup()
