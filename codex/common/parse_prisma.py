import re
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, validator


class FieldInfo(BaseModel):
    type: str
    attributes: List[str] = []
    relation: Optional[str] = None


class ModelInfo(BaseModel):
    name: str
    fields: Dict[str, FieldInfo]
    definition: str


class EnumInfo(BaseModel):
    name: str
    values: List[str]
    definition: str


class DatasourceInfo(BaseModel):
    provider: str
    name: str
    url: str
    extensions: Optional[List[str]] = None

    @validator("provider")
    def validate_provider(cls, v):
        if v not in ["postgresql", "mysql", "sqlite"]:
            raise ValueError(f"Invalid datasource provider: {v}")
        return v


class GeneratorInfo(BaseModel):
    provider: str
    name: str
    config: Dict[str, Union[str, List[str]]]
    definition: str

    @validator("provider")
    def validate_provider(cls, v):
        if v not in ["prisma-client-py", "prisma-docs", "prisma-dbml-generator"]:
            raise ValueError(f"Invalid generator provider: {v}")
        return v


class SchemaInfo(BaseModel):
    datasource: Optional[DatasourceInfo] = None
    generators: list[GeneratorInfo] = []
    enums: Dict[str, EnumInfo] = {}
    models: Dict[str, ModelInfo] = {}


def parse_prisma_schema(schema_text: str) -> SchemaInfo:
    # # Regular expressions to match different parts of the schema
    datasource_pattern = re.compile(r"datasource\s+(\w+)\s*{\s*([\s\S]*?)\s*}")
    generator_pattern = re.compile(r"generator\s+(\w+)\s*{\s*([\s\S]*?)\s*}")
    enum_pattern = re.compile(r"enum\s+(\w+)\s*{\s*([\s\S]*?)\s*}")
    model_pattern = re.compile(
        r"model\s+(\w+)\s*{\s*((?:[^{}]|//.*$)*?)\s*}", re.MULTILINE
    )
    field_pattern = re.compile(
        r"(\w+)\s+(\w+(?:\[])?\??)(?:\s+(@.*))*(?:\s*//\s*(.*))?"
    )
    attribute_pattern = re.compile(r"@\w+(\((?:[^()]*|\((?:[^()]*|\([^()]*\))*\))*\))?")
    relation_pattern = re.compile(r"@relation\((.*?)\)")

    # Parse datasource
    datasource = None
    datasource_match = datasource_pattern.search(schema_text)
    if datasource_match:
        datasource_name = datasource_match.group(1)
        datasource_fields = datasource_match.group(2).strip().split("\n")
        datasource_info = {}
        for field in datasource_fields:
            field = field.strip()
            if field:
                key, value = field.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key == "extensions":
                    value = [
                        ext.strip().strip('"').strip("'")
                        for ext in value[1:-1].split(",")
                    ]
                datasource_info[key] = value
        datasource = DatasourceInfo(name=datasource_name, **datasource_info)

    # Parse generators
    generators = []
    for generator_match in generator_pattern.finditer(schema_text):
        generator_name = generator_match.group(1)
        generator_definition = generator_match.group(0)
        generator_fields = generator_match.group(2).strip().split("\n")
        generator_config = {}
        generator_provider = None
        for field in generator_fields:
            field = field.strip()
            if field:
                key, value = field.split("=", 1)
                key = key.strip()
                value = value.strip()
                if key == "provider":
                    generator_provider = value.strip('"')
                else:
                    if value.startswith("[") and value.endswith("]"):
                        value = [
                            item.strip().strip('"') for item in value[1:-1].split(",")
                        ]
                    else:
                        value = value.strip('"')
                    generator_config[key] = value
        if generator_provider:
            generator = GeneratorInfo(
                name=generator_name,
                provider=generator_provider,
                config=generator_config,
                definition=generator_definition,
            )
            generators.append(generator)

    # Parse enums
    enums = {}
    for enum_match in enum_pattern.finditer(schema_text):
        enum_name = enum_match.group(1)
        enum_values = [value.strip() for value in enum_match.group(2).split()]
        enum_definition = enum_match.group(0)
        enums[enum_name] = EnumInfo(
            name=enum_name, values=enum_values, definition=enum_definition
        )

    # Parse models
    models = {}
    for model_match in model_pattern.finditer(schema_text):
        model_name = model_match.group(1)
        model_definition = model_match.group(0)
        model_fields = {}
        fields = model_match.group(2).strip().split("\n")
        for field in fields:
            field = field.strip()
            if field:
                field_match = field_pattern.match(field)
                if field_match:
                    field_name = field_match.group(1)
                    field_type = field_match.group(2)
                    field_attributes = []
                    field_relation = None
                    if _attributes_str := field_match.group(3):
                        for attribute_match in attribute_pattern.finditer(
                            _attributes_str
                        ):
                            attribute = attribute_match.group()
                            if attribute.startswith("@relation"):
                                relation_match = relation_pattern.search(attribute)
                                if relation_match:
                                    field_relation = (
                                        f"@relation({relation_match.group(1)})"
                                    )
                            else:
                                field_attributes.append(attribute)
                    model_fields[field_name] = FieldInfo(
                        type=field_type,
                        attributes=field_attributes,
                        relation=field_relation,
                    )
        models[model_name] = ModelInfo(
            name=model_name, fields=model_fields, definition=model_definition
        )

    return SchemaInfo(
        datasource=datasource, generators=generators, enums=enums, models=models
    )


def print_parsed_schema(parsed_schema: SchemaInfo):
    if parsed_schema.datasource:
        print("Datasource:")
        print(f"  Provider: {parsed_schema.datasource.provider}")
        print(f"  URL: {parsed_schema.datasource.url}")
        print(f"  Extensions: {parsed_schema.datasource.extensions}")
    if len(parsed_schema.generators) > 0:
        for generator in parsed_schema.generators:
            print(f"Generator {generator.name}:")
            print(f"  Provider: {generator.provider}")
            print(f"  Config: {generator.config}")
    for enum_name, enum_info in parsed_schema.enums.items():
        print(f"Enum: {enum_name}")
        print(f"  Definition: {enum_info.definition}")
        print(f"  Values: {enum_info.values}")
    for model_name, model_info in parsed_schema.models.items():
        print(f"Model: {model_name}")
        print(f"  Definition: {model_info.definition}")
        for field_name, field_data in model_info.fields.items():
            print(f"  Field: {field_name}")
            print(f"    Type: {field_data.type}")
            print(f"    Attributes: {field_data.attributes}")
            print(f"    Relation: {field_data.relation}")
