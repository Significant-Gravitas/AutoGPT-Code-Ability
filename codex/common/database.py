import prisma.models

INCLUDE_TYPE = {"include": {"RelatedTypes": {"include": {"Fields": True}}}}

INCLUDE_FIELD = {"include": {"Fields": {"include": {"RelatedTypes": True}}}}

INCLUDE_API_ROUTE = {
    "include": {
        "RequestObject": INCLUDE_FIELD,
        "ResponseObject": INCLUDE_FIELD,
    }
}

INCLUDE_FUNC = {
    "include": {
        "FunctionArgs": INCLUDE_TYPE,
        "FunctionReturn": INCLUDE_TYPE,
        "DatabaseSchema": {"include": {"DatabaseTables": True}},
    }
}


def get_database_schema(spec: prisma.models.Specification) -> str:
    return (
        "\n\n".join([t.definition for t in spec.DatabaseSchema.DatabaseTables])
        if spec and spec.DatabaseSchema and spec.DatabaseSchema.DatabaseTables
        else ""
    )
