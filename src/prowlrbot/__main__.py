# -*- coding: utf-8 -*-
"""Allow running ProwlrBot via ``python -m prowlrbot``."""
from .cli.main import cli

if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
