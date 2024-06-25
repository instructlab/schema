# SPDX-License-Identifier: Apache-2.0

# Standard
import importlib.resources
import json
from importlib.abc import Traversable

# Third Party
from assertpy import assert_that
from referencing import Resource
from referencing.jsonschema import DRAFT202012

from instructlab.schema import schema_base, schema_versions


class TestVersions:
    def _load_schemas(self, version: Traversable) -> None:
        assert_that(version).is_not_none()
        for schema_name in ("compositional_skills", "knowledge", "version"):
            path = version.joinpath(f"{schema_name}.json")
            text = path.read_text(encoding="utf-8")
            assert_that(text).is_not_none().is_not_empty()
            contents = json.loads(text)
            assert_that(contents).is_not_none().is_not_empty()
            resource = Resource.from_contents(contents=contents, default_specification=DRAFT202012)
            assert_that(resource).is_not_none().has_contents(contents)

    def test_schema_base(self) -> None:
        base = schema_base()
        assert_that(base).is_not_none()
        versions = schema_versions()
        assert_that(versions).is_not_none().is_not_empty()
        for i in range(len(versions)):
            version = base.joinpath(f"v{i+1}")
            self._load_schemas(version)

    def test_schema_versions(self) -> None:
        versions = schema_versions()
        assert_that(versions).is_not_none().is_not_empty()
        for i, version in enumerate(versions):
            assert_that(version).has_name(f"v{i+1}")
            self._load_schemas(version)

    def test_importlib_schema(self) -> None:
        versions = schema_versions()
        assert_that(versions).is_not_none().is_not_empty()
        for i in range(len(versions)):
            version = importlib.resources.files(f"instructlab.schema.v{i+1}")
            self._load_schemas(version)
