# SPDX-License-Identifier: Apache-2.0

"""InstructLab Taxonomy Schema"""

# Standard
from importlib import resources

try:
    from importlib.resources.abc import Traversable  # type: ignore[import-not-found]
except ImportError:  # python<3.11
    from importlib.abc import Traversable

__all__ = ["schema_versions"]


def schema_versions() -> list[Traversable]:
    """Return the sorted list of schema versions.

    Returns:
        list[Traversable]: A sorted list of schema versions.
    """
    schema_base = resources.files(__package__)
    versions = sorted(
        (v for v in schema_base.iterdir() if v.name[0] == "v" and v.name[1:].isdigit()),
        key=lambda k: int(k.name[1:]),
    )
    return versions
