# -*- coding: utf-8 -*-
"""Python version compatibility shims."""

import sys

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        """Backport of StrEnum for Python < 3.11."""

        pass


__all__ = ["StrEnum"]
