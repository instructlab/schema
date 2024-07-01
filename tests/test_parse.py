# SPDX-License-Identifier: Apache-2.0

# Standard
import logging
import os
import re
from collections.abc import Callable
from pathlib import Path

# Third Party
from assertpy import assert_that
from pytest import CaptureFixture, LogCaptureFixture

from instructlab.schema.taxonomy import TaxonomyMessageFormat, TaxonomyParser

testdata = Path("tests/testdata")


class TestParsing:
    def message_filter(self, regex: str) -> Callable[[logging.LogRecord], bool]:
        pattern = re.compile(regex)
        return lambda r: bool(re.search(pattern, r.message))

    def test_invalid(self, caplog: LogCaptureFixture):
        caplog.set_level(logging.INFO, logger="instructlab.schema")
        test_yaml = "compositional_skills/invalid_yaml/qna.yaml"
        rel_path = testdata.joinpath(test_yaml)
        parser = TaxonomyParser(schema_version=0, message_format=TaxonomyMessageFormat.LOGGING)
        taxonomy = parser.parse(rel_path)

        assert_that(taxonomy.warnings).is_greater_than_or_equal_to(1)
        assert_that(taxonomy.errors).is_greater_than_or_equal_to(2)
        assert_that(taxonomy.path.as_posix()).is_equal_to(test_yaml)
        assert_that(taxonomy.rel_path).is_equal_to(rel_path)
        assert_that(caplog.records).extracting(
            "message",
            filter=self.message_filter(f"{re.escape(test_yaml)}:"),  # type: ignore[call-arg]
        ).is_length(len(caplog.records))
        assert_that(caplog.records).extracting(
            "levelno",
            filter=self.message_filter(r"line too long"),  # type: ignore[call-arg]
        ).contains_only(logging.WARNING)
        assert_that(caplog.records).extracting(
            "levelno",
            filter=self.message_filter(r"Unevaluated properties.*createdby"),  # type: ignore[call-arg]
        ).contains_only(logging.ERROR)
        assert_that(caplog.records).extracting(
            "levelno",
            filter=self.message_filter(r"created_by.*required property"),  # type: ignore[call-arg]
        ).contains_only(logging.ERROR)

    def test_invalid_yamlint_strict(self, caplog: LogCaptureFixture):
        caplog.set_level(logging.INFO, logger="instructlab.schema")
        test_yaml = "compositional_skills/invalid_yaml/qna.yaml"
        rel_path = testdata.joinpath(test_yaml)
        parser = TaxonomyParser(schema_version=0, yamllint_strict=True, message_format=TaxonomyMessageFormat.LOGGING)
        taxonomy = parser.parse(rel_path)

        assert_that(taxonomy.warnings).is_zero()
        assert_that(taxonomy.errors).is_greater_than_or_equal_to(3)
        assert_that(taxonomy.path.as_posix()).is_equal_to(test_yaml)
        assert_that(taxonomy.rel_path).is_equal_to(rel_path)
        assert_that(caplog.records).extracting(
            "message",
            filter=self.message_filter(f"{re.escape(test_yaml)}:"),  # type: ignore[call-arg]
        ).is_length(len(caplog.records))
        assert_that(caplog.records).extracting(
            "levelno",
            filter=self.message_filter(r"line too long"),  # type: ignore[call-arg]
        ).contains_only(logging.ERROR)
        assert_that(caplog.records).extracting(
            "levelno",
            filter=self.message_filter(r"Unevaluated properties.*createdby"),  # type: ignore[call-arg]
        ).contains_only(logging.ERROR)
        assert_that(caplog.records).extracting(
            "levelno",
            filter=self.message_filter(r"created_by.*required property"),  # type: ignore[call-arg]
        ).contains_only(logging.ERROR)

    def test_invalid_custom_yaml_config(self, caplog: LogCaptureFixture):
        caplog.set_level(logging.INFO, logger="instructlab.schema")
        yamllint_config = "{extends: relaxed, rules: {line-length: {max: 180}}}"
        test_yaml = "compositional_skills/invalid_yaml/qna.yaml"
        rel_path = testdata.joinpath(test_yaml)
        parser = TaxonomyParser(
            schema_version=0,
            message_format="LOGGING",
            yamllint_config=yamllint_config,
        )
        taxonomy = parser.parse(rel_path)

        assert_that(taxonomy.warnings).is_zero()
        assert_that(taxonomy.errors).is_greater_than_or_equal_to(2)
        assert_that(taxonomy.path.as_posix()).is_equal_to(test_yaml)
        assert_that(taxonomy.rel_path).is_equal_to(rel_path)
        assert_that(caplog.records).extracting(
            "message",
            filter=self.message_filter(f"{re.escape(test_yaml)}:"),  # type: ignore[call-arg]
        ).is_length(len(caplog.records))
        assert_that(caplog.records).extracting(
            "levelno",
            filter=self.message_filter(r"line too long"),  # type: ignore[call-arg]
        ).is_empty()
        assert_that(caplog.records).extracting(
            "levelno",
            filter=self.message_filter(r"Unevaluated properties.*createdby"),  # type: ignore[call-arg]
        ).contains_only(logging.ERROR)
        assert_that(caplog.records).extracting(
            "levelno",
            filter=self.message_filter(r"created_by.*required property"),  # type: ignore[call-arg]
        ).contains_only(logging.ERROR)

    def test_incomplete_skill(self, caplog: LogCaptureFixture):
        caplog.set_level(logging.INFO, logger="instructlab.schema")
        test_yaml = "compositional_skills/skill_incomplete/qna.yaml"
        rel_path = testdata.joinpath(test_yaml)
        parser = TaxonomyParser(schema_version=0, message_format=TaxonomyMessageFormat.LOGGING)
        taxonomy = parser.parse(rel_path)

        assert_that(taxonomy.warnings).is_zero()
        assert_that(taxonomy.errors).is_greater_than_or_equal_to(1)
        assert_that(taxonomy.path.as_posix()).is_equal_to(test_yaml)
        assert_that(taxonomy.rel_path).is_equal_to(rel_path)
        assert_that(caplog.records).extracting(
            "message",
            filter=self.message_filter(f"{re.escape(test_yaml)}:"),  # type: ignore[call-arg]
        ).is_length(len(caplog.records))
        assert_that(caplog.records).extracting(
            "levelno",
            filter=self.message_filter(r"[\.seed_examples].*Value must have at least"),  # type: ignore[call-arg]
        ).contains_only(logging.ERROR)

    def test_valid_skill(self, caplog: LogCaptureFixture):
        caplog.set_level(logging.INFO, logger="instructlab.schema")
        test_yaml = "compositional_skills/skill_valid/qna.yaml"
        rel_path = testdata.joinpath(test_yaml)
        parser = TaxonomyParser(schema_version=0, message_format="logging")
        taxonomy = parser.parse(rel_path)

        assert_that(taxonomy.warnings).is_zero()
        assert_that(taxonomy.errors).is_zero()
        assert_that(taxonomy.path.as_posix()).is_equal_to(test_yaml)
        assert_that(taxonomy.rel_path).is_equal_to(rel_path)
        assert_that(caplog.records).is_empty()

        assert_that(taxonomy.parsed).contains_only("version", "created_by", "seed_examples", "task_description")
        assert_that(taxonomy.parsed.get("seed_examples")).is_length(5)

    def test_valid_knowledge(self, caplog: LogCaptureFixture):
        caplog.set_level(logging.INFO, logger="instructlab.schema")
        test_yaml = "knowledge/knowledge_valid/qna.yaml"
        rel_path = testdata.joinpath(test_yaml)
        parser = TaxonomyParser(schema_version=0, message_format=TaxonomyMessageFormat.LOGGING)
        taxonomy = parser.parse(rel_path)

        assert_that(taxonomy.warnings).is_zero()
        assert_that(taxonomy.errors).is_zero()
        assert_that(taxonomy.path.as_posix()).is_equal_to(test_yaml)
        assert_that(taxonomy.rel_path).is_equal_to(rel_path)
        assert_that(caplog.records).is_empty()

        assert_that(taxonomy.parsed).contains_only(
            "version",
            "created_by",
            "seed_examples",
            "task_description",
            "document",
            "domain",
        )
        assert_that(taxonomy.parsed.get("seed_examples")).is_length(5)
        assert_that(taxonomy.parsed.get("document")).contains_only("repo", "commit", "patterns")

    def test_file_does_not_exist(self, caplog: LogCaptureFixture):
        caplog.set_level(logging.INFO, logger="instructlab.schema")
        test_yaml = "knowledge/invalid_name/qna.yaml"
        rel_path = testdata.joinpath(test_yaml)
        parser = TaxonomyParser(schema_version=0, message_format=TaxonomyMessageFormat.LOGGING)
        taxonomy = parser.parse(rel_path)

        assert_that(taxonomy.warnings).is_zero()
        assert_that(taxonomy.errors).is_equal_to(1)
        assert_that(taxonomy.path.as_posix()).is_equal_to(test_yaml)
        assert_that(taxonomy.rel_path).is_equal_to(rel_path)
        assert_that(caplog.records).extracting(
            "message",
            filter=self.message_filter(re.escape(test_yaml)),  # type: ignore[call-arg]
        ).is_length(len(caplog.records))
        assert_that(caplog.records).extracting(
            "levelno",
            filter=self.message_filter(r"does not exist or is not a file"),  # type: ignore[call-arg]
        ).contains_only(logging.ERROR)

    def test_file_has_wrong_extension(self, caplog: LogCaptureFixture):
        caplog.set_level(logging.INFO, logger="instructlab.schema")
        test_yaml = "knowledge/invalid_name/qna.yml"
        rel_path = testdata.joinpath(test_yaml)
        parser = TaxonomyParser(schema_version=0, message_format=TaxonomyMessageFormat.LOGGING)
        taxonomy = parser.parse(rel_path)

        assert_that(taxonomy.warnings).is_zero()
        assert_that(taxonomy.errors).is_equal_to(1)
        assert_that(taxonomy.path.as_posix()).is_equal_to(test_yaml)
        assert_that(taxonomy.rel_path).is_equal_to(rel_path)
        assert_that(caplog.records).extracting(
            "message",
            filter=self.message_filter(re.escape(test_yaml)),  # type: ignore[call-arg]
        ).is_length(len(caplog.records))
        assert_that(caplog.records).extracting(
            "levelno",
            filter=self.message_filter(r"""Taxonomy file must be named "qna\.yaml".*qna.yml"""),  # type: ignore[call-arg]
        ).contains_only(logging.ERROR)

    def test_file_has_wrong_name(self, caplog: LogCaptureFixture):
        caplog.set_level(logging.INFO, logger="instructlab.schema")
        test_yaml = "knowledge/invalid_name/file.yaml"
        rel_path = testdata.joinpath(test_yaml)
        parser = TaxonomyParser(schema_version=0, message_format=TaxonomyMessageFormat.LOGGING)
        taxonomy = parser.parse(rel_path)

        assert_that(taxonomy.warnings).is_zero()
        assert_that(taxonomy.errors).is_equal_to(1)
        assert_that(taxonomy.path.as_posix()).is_equal_to(test_yaml)
        assert_that(taxonomy.rel_path).is_equal_to(rel_path)
        assert_that(caplog.records).extracting(
            "message",
            filter=self.message_filter(re.escape(test_yaml)),  # type: ignore[call-arg]
        ).is_length(len(caplog.records))
        assert_that(caplog.records).extracting(
            "levelno",
            filter=self.message_filter(r"""Taxonomy file must be named "qna\.yaml".*file\.yaml"""),  # type: ignore[call-arg]
        ).contains_only(logging.ERROR)

    def test_empty_yaml(self, caplog: LogCaptureFixture):
        caplog.set_level(logging.INFO, logger="instructlab.schema")
        test_yaml = "compositional_skills/empty_yaml/qna.yaml"
        rel_path = testdata.joinpath(test_yaml)
        parser = TaxonomyParser(schema_version=0, message_format=TaxonomyMessageFormat.LOGGING)
        taxonomy = parser.parse(rel_path)

        assert_that(taxonomy.warnings).is_equal_to(1)
        assert_that(taxonomy.errors).is_zero()
        assert_that(taxonomy.path.as_posix()).is_equal_to(test_yaml)
        assert_that(taxonomy.rel_path).is_equal_to(rel_path)
        assert_that(caplog.records).extracting(
            "message",
            filter=self.message_filter(re.escape(test_yaml)),  # type: ignore[call-arg]
        ).is_length(len(caplog.records))
        assert_that(caplog.records).extracting(
            "levelno",
            filter=self.message_filter(r"The file is empty"),  # type: ignore[call-arg]
        ).contains_only(logging.WARNING)

    def test_array_yaml(self, caplog: LogCaptureFixture):
        caplog.set_level(logging.INFO, logger="instructlab.schema")
        test_yaml = "compositional_skills/array_yaml/qna.yaml"
        rel_path = testdata.joinpath(test_yaml)
        parser = TaxonomyParser(schema_version=0, message_format=TaxonomyMessageFormat.LOGGING)
        taxonomy = parser.parse(rel_path)

        assert_that(taxonomy.warnings).is_zero()
        assert_that(taxonomy.errors).is_equal_to(1)
        assert_that(taxonomy.path.as_posix()).is_equal_to(test_yaml)
        assert_that(taxonomy.rel_path).is_equal_to(rel_path)
        assert_that(caplog.records).extracting(
            "message",
            filter=self.message_filter(re.escape(test_yaml)),  # type: ignore[call-arg]
        ).is_length(len(caplog.records))
        assert_that(caplog.records).extracting(
            "levelno",
            filter=self.message_filter(r"The file is not valid"),  # type: ignore[call-arg]
        ).contains_only(logging.ERROR)

    def test_version_1(self, caplog: LogCaptureFixture):
        caplog.set_level(logging.INFO, logger="instructlab.schema")
        test_yaml = "compositional_skills/version_1/qna.yaml"
        rel_path = testdata.joinpath(test_yaml)
        parser = TaxonomyParser(schema_version=0, message_format=TaxonomyMessageFormat.LOGGING)
        taxonomy = parser.parse(rel_path)

        assert_that(taxonomy.warnings).is_zero()
        assert_that(taxonomy.errors).is_zero()
        assert_that(taxonomy.path.as_posix()).is_equal_to(test_yaml)
        assert_that(taxonomy.rel_path).is_equal_to(rel_path)
        assert_that(taxonomy.version).is_equal_to(1)
        assert_that(caplog.records).is_empty()

    def test_version_1_as_version_2(self, caplog: LogCaptureFixture):
        caplog.set_level(logging.INFO, logger="instructlab.schema")
        test_yaml = "compositional_skills/version_1/qna.yaml"
        rel_path = testdata.joinpath(test_yaml)
        parser = TaxonomyParser(schema_version=2, message_format=TaxonomyMessageFormat.LOGGING)
        taxonomy = parser.parse(rel_path)

        assert_that(taxonomy.warnings).is_greater_than_or_equal_to(1)
        assert_that(taxonomy.errors).is_greater_than_or_equal_to(1)
        assert_that(taxonomy.path.as_posix()).is_equal_to(test_yaml)
        assert_that(taxonomy.rel_path).is_equal_to(rel_path)
        assert_that(taxonomy.version).is_equal_to(2)
        assert_that(caplog.records).extracting(
            "message",
            filter=self.message_filter(f"{re.escape(test_yaml)}:"),  # type: ignore[call-arg]
        ).is_length(len(caplog.records))
        assert_that(caplog.records).extracting(
            "levelno",
            filter=self.message_filter(r"line too long"),  # type: ignore[call-arg]
        ).contains_only(logging.WARNING)
        assert_that(caplog.records).extracting(
            "levelno",
            filter=self.message_filter(r"version.*required property"),  # type: ignore[call-arg]
        ).contains_only(logging.ERROR)

    def test_format_github(self, capsys: CaptureFixture[str]):
        test_yaml = "compositional_skills/invalid_yaml/qna.yaml"
        rel_path = testdata.joinpath(test_yaml)
        parser = TaxonomyParser(schema_version=0, message_format=TaxonomyMessageFormat.GITHUB)
        taxonomy = parser.parse(rel_path)

        assert_that(taxonomy.warnings).is_greater_than_or_equal_to(1)
        assert_that(taxonomy.errors).is_greater_than_or_equal_to(2)
        assert_that(taxonomy.path.as_posix()).is_equal_to(test_yaml)
        assert_that(taxonomy.rel_path).is_equal_to(rel_path)
        captured = capsys.readouterr()
        assert_that(captured.err).is_empty()
        assert_that(captured.out).is_not_empty()
        lines: list[str] = captured.out.splitlines()
        assert_that(lines).is_not_empty()
        pattern = f"^::(error|warning) file={re.escape(str(rel_path))},"
        for line in lines:
            assert_that(line).matches(pattern)  # type: ignore[arg-type]

    def test_format_standard(self, capsys: CaptureFixture[str]):
        test_yaml = "compositional_skills/invalid_yaml/qna.yaml"
        rel_path = testdata.joinpath(test_yaml)
        parser = TaxonomyParser(schema_version=0, message_format=TaxonomyMessageFormat.STANDARD)
        taxonomy = parser.parse(rel_path)

        assert_that(taxonomy.warnings).is_greater_than_or_equal_to(1)
        assert_that(taxonomy.errors).is_greater_than_or_equal_to(2)
        assert_that(taxonomy.path.as_posix()).is_equal_to(test_yaml)
        assert_that(taxonomy.rel_path).is_equal_to(rel_path)
        captured = capsys.readouterr()
        assert_that(captured.err).is_empty()
        assert_that(captured.out).is_not_empty()
        lines: list[str] = captured.out.splitlines()
        assert_that(lines).is_not_empty()
        pattern = f"^(ERROR|WARN): {re.escape(str(rel_path))}:"
        for line in lines:
            assert_that(line).matches(pattern)  # type: ignore[arg-type]

    def test_format_auto(self, capsys: CaptureFixture[str]):
        test_yaml = "compositional_skills/invalid_yaml/qna.yaml"
        rel_path = testdata.joinpath(test_yaml)
        parser = TaxonomyParser(schema_version=0)
        taxonomy = parser.parse(rel_path)

        assert_that(taxonomy.warnings).is_greater_than_or_equal_to(1)
        assert_that(taxonomy.errors).is_greater_than_or_equal_to(2)
        assert_that(taxonomy.path.as_posix()).is_equal_to(test_yaml)
        assert_that(taxonomy.rel_path).is_equal_to(rel_path)
        captured = capsys.readouterr()
        assert_that(captured.err).is_empty()
        assert_that(captured.out).is_not_empty()
        lines: list[str] = captured.out.splitlines()
        assert_that(lines).is_not_empty()
        pattern = (
            f"^::(error|warning) file={re.escape(str(rel_path))},"
            if "GITHUB_ACTIONS" in os.environ and "GITHUB_WORKFLOW" in os.environ
            else f"^(ERROR|WARN): {re.escape(str(rel_path))}:"
        )
        for line in lines:
            assert_that(line).matches(pattern)  # type: ignore[arg-type]
