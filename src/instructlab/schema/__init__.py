# SPDX-License-Identifier: Apache-2.0

"""InstructLab Taxonomy Schema"""

# Standard
from importlib import resources

try:
    from importlib.resources.abc import Traversable  # type: ignore[import-not-found]
except ImportError:  # python<3.11
    from importlib.abc import Traversable

__all__ = ["schema_base", "schema_versions"]


def schema_base() -> Traversable:
    """Return the schema base.

    Returns:
        Traversable: The base for the schema versions.
    """
    base = resources.files(__package__)
    return base


def schema_versions() -> list[Traversable]:
    """Return the sorted list of schema versions.

    Returns:
        list[Traversable]: A sorted list of schema versions.
    """
    versions = sorted(
        (v for v in schema_base().iterdir() if v.name[0] == "v" and v.name[1:].isdigit()),
        key=lambda k: int(k.name[1:]),
    )
    return versions
