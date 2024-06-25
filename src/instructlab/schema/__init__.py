# SPDX-License-Identifier: Apache-2.0

"""InstructLab Taxonomy Schema"""

# Standard
import importlib.resources
from importlib.abc import Traversable

__all__ = ["schema_base", "schema_versions"]


def schema_base() -> Traversable:
    """Return the schema base.

    Returns:
        Traversable: The base for the schema versions.
    """
    base = importlib.resources.files(__name__)
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
