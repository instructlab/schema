# Taxonomy Schema

This Python package defines the JSON schema and a parser for the InstructLab [Taxonomy](https://github.com/instructlab/taxonomy) YAML.

Consumers of this schema can `pip install instructlab-schema`, and use the `instructlab.schema.taxonomy.TaxonomyParser` class to parse and validate `qna.yaml` taxonomy files.
Schema files can be directly accessed using the `instructlab.schema.schema_base()` method to get access the base of the schema resources.
