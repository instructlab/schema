# SPDX-License-Identifier: Apache-2.0

# Standard
import json
from importlib import resources

# Third Party
from referencing import Resource
from referencing.jsonschema import DRAFT202012

from instructlab.schema import schema_versions


class TestVersions:
    def test_versions(self):
        versions = schema_versions()
        assert versions is not None
        assert len(versions) > 1
        for i, v in enumerate(versions):
            assert v.name == f"v{i+1}"

    def _load_schema(self, path):
        text = path.read_text(encoding="utf-8")
        assert text
        assert len(text) > 1
        contents = json.loads(text)
        assert contents
        assert len(contents) > 1
        resource = Resource.from_contents(
            contents=contents, default_specification=DRAFT202012
        )
        assert resource
        assert resource.contents == contents

    def test_import_schema_base(self):
        schema_base = resources.files("instructlab.schema")
        for i in range(len(schema_versions())):
            schema_version = schema_base.joinpath(f"v{i+1}")
            for schema_name in ("compositional_skills", "knowledge", "version"):
                path = schema_version.joinpath(f"{schema_name}.json")
                self._load_schema(path)

    def test_import_schema_versions(self):
        for i in range(len(schema_versions())):
            schema_version = resources.files(f"instructlab.schema.v{i+1}")
            for schema_name in ("compositional_skills", "knowledge", "version"):
                path = schema_version.joinpath(f"{schema_name}.json")
                self._load_schema(path)
