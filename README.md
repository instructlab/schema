# Taxonomy Schema

![Lint](https://github.com/instructlab/schema/actions/workflows/lint.yml/badge.svg?branch=main)
![Tests](https://github.com/instructlab/schema/actions/workflows/test.yml/badge.svg?branch=main)
![Build](https://github.com/instructlab/schema/actions/workflows/pypi.yml/badge.svg?branch=main)

This Python package defines the JSON schema and a parser for the InstructLab [Taxonomy](https://github.com/instructlab/taxonomy) YAML.

Consumers of this schema can `pip install instructlab-schema`, and use the `instructlab.schema.taxonomy.TaxonomyParser` class to parse and validate `qna.yaml` taxonomy files.
Schema files can be directly accessed using the `instructlab.schema.schema_base()` method to get access the base of the schema resources.
