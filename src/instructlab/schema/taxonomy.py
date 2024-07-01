# SPDX-License-Identifier: Apache-2.0

"""Taxonomy qna.yaml parsing"""

# Standard
import json
import logging
import os
import re
import subprocess
from collections.abc import Mapping
from enum import Enum, auto
from functools import lru_cache, partial
from pathlib import Path
from typing import Any

# Third Party
import yaml
from jsonschema.protocols import Validator
from jsonschema.validators import validator_for
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource
from referencing.jsonschema import DRAFT202012
from typing_extensions import Self

from . import schema_base, schema_versions

logger = logging.getLogger(__name__)

DEFAULT_TAXONOMY_FOLDERS: list[str] = ["compositional_skills", "knowledge"]
"""Taxonomy folders which are also the schema names"""

DEFAULT_YAMLLINT_CONFIG: str = "{extends: relaxed, rules: {line-length: {max: 120}}}"
"""Default yamllint configuration"""


class TaxonomyReadingException(Exception):
    """An exception raised during reading of the taxonomy."""


class TaxonomyMessageFormat(Enum):
    """An enum for the format choices for taxonomy parsing messages"""

    AUTO = auto()
    """
    If specified, then GITHUB will be used if both the GITHUB_ACTIONS and GITHUB_WORKFLOW
    environment variables are set. Otherwise STANDARD will be used.
    """
    STANDARD = auto()
    """
    A plain message starting with ERROR or WARN.
    """
    GITHUB = auto()
    """
    Uses GitHub Actions workflow commands to set error or warning commands.
    """
    LOGGING = auto()
    """
    Uses this module's logger to log warnings or errors.
    """


class Taxonomy:
    """A container for a parsed taxonomy qna.yaml file."""

    def __init__(self, *, path: Path, abs_path: Path, message_format: TaxonomyMessageFormat) -> None:
        """Create a container for a parsed taxonomy qna.yaml file.

        Args:
            path (Path): The taxonomy path for the qna.yaml file.
            This should be a relative path starting at the taxonomy folder holding the qna.yaml file.
            abs_path (Path): The absolute path for the qna.yaml file.
            message_format (TaxonomyMessageFormat): The format of any messages.
            If TaxonomyMessageFormat.AUTO is specified, then TaxonomyMessageFormat.GITHUB will be used if
            both the GITHUB_ACTIONS and GITHUB_WORKFLOW environment variables are set. Otherwise
            TaxonomyMessageFormat.STANDARD will be used.
        """
        self.path: Path = path
        abs_path = abs_path.resolve()
        cwd = Path.cwd()
        self.rel_path: Path = abs_path.relative_to(cwd) if abs_path.is_relative_to(cwd) else abs_path
        if message_format is TaxonomyMessageFormat.AUTO:
            message_format = TaxonomyMessageFormat.GITHUB if "GITHUB_ACTIONS" in os.environ and "GITHUB_WORKFLOW" in os.environ else TaxonomyMessageFormat.STANDARD
        self.message_format: TaxonomyMessageFormat = message_format
        self.errors: int = 0
        self.warnings: int = 0
        self.parsed: Mapping[str, Any] = {}
        self.version: int = 0

    def error(
        self,
        message: str,
        *message_args: Any,
        line: str | int = 1,
        col: str | int = 1,
        yaml_path: str = "",
    ) -> Self:
        """Report an error on the taxonomy qna.yaml file.

        Args:
            message (str): The error message. The message supports string formatting using the specified message_args, if any.
            message_args (Any, optional): Values used by the message string formatting.
            line (str | int, optional): The line in the qna.yaml file where the error occurred. Defaults to 1.
            col (str | int, optional): The column in the qna.yaml file where the error occurred. Defaults to 1.
            yaml_path (str, optional): The yaml path to the item in the qna.yaml file where the error occurred.

        Returns:
            Self: This Taxonomy object.
        """
        self.errors += 1
        match self.message_format:
            case TaxonomyMessageFormat.GITHUB:
                if message_args:
                    message = message % message_args
                print(
                    f"::error file={self.rel_path},line={line},col={col}::{line}:{col} [{yaml_path}] {message}"
                    if yaml_path
                    else f"::error file={self.rel_path},line={line},col={col}::{line}:{col} {message}"
                )
            case TaxonomyMessageFormat.LOGGING:
                if yaml_path:
                    logger.error(
                        "%s:%s:%s [%s] " + message,
                        self.rel_path,
                        line,
                        col,
                        yaml_path,
                        *message_args,
                    )
                else:
                    logger.error("%s:%s:%s " + message, self.rel_path, line, col, *message_args)
            case TaxonomyMessageFormat.STANDARD | _:
                if message_args:
                    message = message % message_args
                print(f"ERROR: {self.rel_path}:{line}:{col} [{yaml_path}] {message}" if yaml_path else f"ERROR: {self.rel_path}:{line}:{col} {message}")
        return self

    def warning(
        self,
        message: str,
        *message_args: Any,
        line: str | int = 1,
        col: str | int = 1,
        yaml_path: str = "",
    ) -> Self:
        """Report a warning on the taxonomy qna.yaml file.

        Args:
            message (str): The warning message. The message supports string formatting using the specified message_args, if any.
            message_args (Any, optional): Values used by the message string formatting.
            line (str | int, optional): The line in the qna.yaml file where the warning occurred. Defaults to 1.
            col (str | int, optional): The column in the qna.yaml file where the warning occurred. Defaults to 1.
            yaml_path (str, optional): The yaml path to the item in the qna.yaml file where the warning occurred.

        Returns:
            Self: This Taxonomy object.
        """
        self.warnings += 1
        match self.message_format:
            case TaxonomyMessageFormat.GITHUB:
                if message_args:
                    message = message % message_args
                print(
                    f"::warning file={self.rel_path},line={line},col={col}::{line}:{col} [{yaml_path}] {message}"
                    if yaml_path
                    else f"::warning file={self.rel_path},line={line},col={col}::{line}:{col} {message}"
                )
            case TaxonomyMessageFormat.LOGGING:
                if yaml_path:
                    logger.warning(
                        "%s:%s:%s [%s] " + message,
                        self.rel_path,
                        line,
                        col,
                        yaml_path,
                        *message_args,
                    )
                else:
                    logger.warning("%s:%s:%s " + message, self.rel_path, line, col, *message_args)
            case TaxonomyMessageFormat.STANDARD | _:
                if message_args:
                    message = message % message_args
                print(f"WARN: {self.rel_path}:{line}:{col} [{yaml_path}] {message}" if yaml_path else f"WARN: {self.rel_path}:{line}:{col} {message}")
        return self


class TaxonomyParser:
    """A parser for taxonomy qna.yaml files. The parser will return a Taxonomy object."""

    def __init__(
        self,
        *,
        taxonomy_folders: list[str] | None = None,
        schema_version: int | None = None,
        yamllint_config: str | None = None,
        yamllint_strict: bool = False,
        message_format: TaxonomyMessageFormat | str | None = None,
    ) -> None:
        """Create a parser for a taxonomy qna.yaml file.

        Args:
            taxonomy_folders (list[str] | None, optional): The folder/schema names.
            DEFAULT_TAXONOMY_FOLDERS is used if None is specified.
            schema_version (int | None, optional): The version of the Taxonomy schema.
            Specifying a version less than 1 will use the schema version specified by each YAML document's "version" key.
            The highest schema version is used if None is specified.
            yamllint_config (str | None, optional): The yamllint configuration data.
            DEFAULT_YAMLLINT_CONFIG is used if None is specified.
            message_format (TaxonomyMessageFormat | str | None, optional): The format of any messages.
            TaxonomyMessageFormat.AUTO is used if None is specified.
        """
        if taxonomy_folders is None:
            taxonomy_folders = DEFAULT_TAXONOMY_FOLDERS
        self.taxonomy_folders: list[str] = taxonomy_folders
        if schema_version is None:
            versions = schema_versions()
            if not versions:
                raise TaxonomyReadingException(f'Schema base "{schema_base()}" does not contain any schema versions')
            schema_version = int(versions[-1].name[1:])
        self.schema_version: int = schema_version
        if yamllint_config is None:
            yamllint_config = DEFAULT_YAMLLINT_CONFIG
        self.yamllint_config: str = yamllint_config
        self.yamllint_strict: bool = yamllint_strict
        if message_format is None:
            message_format = TaxonomyMessageFormat.AUTO
        elif isinstance(message_format, str):
            message_format = TaxonomyMessageFormat[message_format.upper()]
        self.message_format: TaxonomyMessageFormat = message_format
        self.yq_available: bool = True

    def _yamllint(self, content: str, taxonomy: Taxonomy) -> None:
        yamllint_cmd = [
            "yamllint",
            "-f",
            "parsable",
            "-d",
            self.yamllint_config,
            "-",  # read from stdin
        ]

        try:
            result = subprocess.run(
                yamllint_cmd,
                check=False,
                input=content,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except FileNotFoundError as e:
            logger.warning(
                "could not run yamllint command",
                exc_info=e,
            )
            return

        lines = result.stdout.splitlines()
        if lines:
            pattern = re.compile(r"[^:]+:(?P<line>[^:]+):(?P<col>[^:]+):\s*\[(?P<severity>[^]]+)\]\s*(?P<message>.*)")
            for line in lines:
                match = pattern.match(line)
                if match:
                    line = match.group("line")
                    col = match.group("col")
                    severity = match.group("severity")
                    message = match.group("message")
                    if self.yamllint_strict or severity == "error":
                        taxonomy.error(
                            message,
                            line=line,
                            col=col,
                        )
                    else:
                        taxonomy.warning(
                            message,
                            line=line,
                            col=col,
                        )

    @lru_cache
    def _load_schema(self, path: str) -> Resource:
        try:
            schema_path = schema_base().joinpath(path)
            contents = json.loads(schema_path.read_text(encoding="utf-8"))
            resource = Resource.from_contents(contents=contents, default_specification=DRAFT202012)
            return resource
        except Exception as e:
            raise NoSuchResource(path) from e

    def _retrieve(self, version_base: str, schema: str) -> Resource:
        path = Path(version_base, schema).as_posix()
        return self._load_schema(path)

    def _schema_validate(self, content: str, taxonomy: Taxonomy) -> None:
        retrieve = partial(self._retrieve, f"v{taxonomy.version}")
        schema_name = taxonomy.path.parts[0]
        if schema_name not in self.taxonomy_folders:
            schema_name = "knowledge" if "document" in taxonomy.parsed else "compositional_skills"

        try:
            schema_resource = retrieve(f"{schema_name}.json")
            schema = schema_resource.contents
            validator_cls = validator_for(schema)
            registry: Registry = Registry(retrieve=retrieve)  # type: ignore[call-arg]
            validator: Validator = validator_cls(schema, registry=registry)

            for validation_error in validator.iter_errors(taxonomy.parsed):
                yaml_path = validation_error.json_path[1:]
                if not yaml_path:
                    yaml_path = "."
                line: str | int = 1
                if self.yq_available:
                    try:
                        yq_expression = f"{yaml_path} | line"
                        line = subprocess.check_output(["yq", yq_expression], input=content, text=True)
                        line = line.strip() if line else 1
                    except (subprocess.SubprocessError, FileNotFoundError) as e:
                        if isinstance(e, FileNotFoundError):
                            self.yq_available = False
                        logger.warning(
                            "could not run yq command",
                            exc_info=e,
                        )
                if validation_error.validator == "minItems":
                    # Special handling for minItems which can have a long message for seed_examples
                    taxonomy.error(
                        "Value must have at least %s items",
                        validation_error.validator_value,
                        line=line,
                        yaml_path=yaml_path,
                    )
                else:
                    taxonomy.error(
                        validation_error.message[-200:],
                        line=line,
                        yaml_path=yaml_path,
                    )
        except NoSuchResource as e:
            taxonomy.error(
                "Cannot load schema file %s. %s",
                e.ref,
                e,
            )

    def parse(self, path: str | Path) -> Taxonomy:
        """Parse a qna.yaml file into a Taxonomy object.

        Args:
            path (str | Path): The path to the qna.yaml file to parse.

        Raises:
            TaxonomyReadingException: If an exception is raised while parsing.

        Returns:
            Taxonomy: A Taxonomy object holding the parsed qna.yaml file and any errors or warnings
            identified during parsing the qna.yaml file.
            These can include lint issues and also schema validation issues.
        """
        abs_path = Path(path).resolve()
        for i in range(len(abs_path.parts) - 1, -1, -1):
            if abs_path.parts[i] in self.taxonomy_folders:
                taxonomy = Taxonomy(path=Path(*abs_path.parts[i:]), abs_path=abs_path, message_format=self.message_format)
                break
        else:
            taxonomy = Taxonomy(path=abs_path, abs_path=abs_path, message_format=self.message_format)

        if not os.path.isfile(abs_path):
            return taxonomy.error(
                'The file "%s" does not exist or is not a file',
                abs_path,
            )

        if abs_path.name != "qna.yaml":
            return taxonomy.error(
                'Taxonomy file must be named "qna.yaml"; "%s" is not a valid name',
                abs_path.name,
            )

        try:
            with open(abs_path, encoding="utf-8") as stream:
                content = stream.read()

            parsed: Mapping[str, Any] = yaml.safe_load(content)
            if not parsed:
                return taxonomy.warning("The file is empty")

            if not isinstance(parsed, Mapping):
                return taxonomy.error(
                    "The file is not valid. The top-level element is not an object with key-value pairs.",
                )

            version: int = self.schema_version
            if version < 1:  # Use version from YAML document
                parsed_version = parsed.get("version", 1)
                if isinstance(parsed_version, int):
                    version = parsed_version
                else:
                    # schema validation will complain about the type
                    try:
                        version = int(parsed_version)
                    except ValueError:
                        version = 1  # fallback to version 1

            taxonomy.version = version
            taxonomy.parsed = parsed

            if version > 1:  # no linting for version 1 yaml
                self._yamllint(content=content, taxonomy=taxonomy)

            self._schema_validate(content=content, taxonomy=taxonomy)
        except Exception as e:
            raise TaxonomyReadingException from e

        return taxonomy
