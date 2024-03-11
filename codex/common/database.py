INCLUDE_TYPE = {"include": {"RelatedTypes": {"include": {"Fields": True}}}}

INCLUDE_FUNC = {
    "include": {
        "FunctionArgs": INCLUDE_TYPE,
        "FunctionReturn": INCLUDE_TYPE,
        "DatabaseSchema": {"include": {"DatabaseTables": True}},
    }
}
