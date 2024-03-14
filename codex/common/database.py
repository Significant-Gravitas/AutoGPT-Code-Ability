INCLUDE_TYPE = {"include": {"RelatedTypes": {"include": {"Fields": True}}}}

INCLUDE_FIELD = {"include": {"Fields": {"include": {"RelatedTypes": True}}}}

INCLUDE_API_ROUTE = {
    "include": {
        "RequestObject": INCLUDE_FIELD,
        "ResponseObject": INCLUDE_FIELD,
        "DatabaseSchema": {"include": {"DatabaseTables": True}},
    }
}

INCLUDE_FUNC = {
    "include": {
        "FunctionArgs": INCLUDE_TYPE,
        "FunctionReturn": INCLUDE_TYPE,
        "DatabaseSchema": {"include": {"DatabaseTables": True}},
    }
}
