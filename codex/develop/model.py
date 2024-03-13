from typing import Dict, List, Optional

from prisma.models import Function as FunctionDBModel
from prisma.models import ObjectType, Function
from pydantic import BaseModel

from codex.common.model import ObjectTypeModel as ObjectDef


class Package(BaseModel):
    package_name: str
    version: str | None = None
    specifier: str | None = None


class FunctionDef(BaseModel):
    name: str
    arg_types: List[tuple[str, str]]
    arg_descs: dict[str, str]
    return_type: str | None = None
    return_desc: str
    is_implemented: bool
    function_desc: str
    function_code: str
    function_template: str | None = None

    def __generate_function_template(f) -> str:
        args_str = ", ".join([f"{name}: {type}" for name, type in f.arg_types])
        arg_desc = f"\n{' '*12}".join(
            [
                f'{name} ({type}): {f.arg_descs.get(name, "-")}'
                for name, type in f.arg_types
            ]
        )

        template = f"""
        def {f.name}({args_str}) -> {f.return_type}:
            \"\"\"
            {f.function_desc}

            Args:
            {arg_desc}

            Returns:
            {f.return_type}: {f.return_desc}
            \"\"\"
            pass
        """
        return "\n".join([line[8:] for line in template.split("\n")]).strip()

    def __init__(self, function_template: Optional[str] = None, **data):
        super().__init__(**data)
        self.function_template = (
            function_template or self.__generate_function_template()
        )


class GeneratedFunctionResponse(BaseModel):
    function_id: str | None = None

    function_name: str
    compiled_route_id: str
    available_objects: dict[str, ObjectType]
    available_functions: dict[str, Function]
    template: str

    rawCode: str

    packages: List[Package]
    imports: List[str]
    functionCode: str

    functions: Dict[str, FunctionDef]
    objects: Dict[str, ObjectDef]


class ApplicationGraphs(BaseModel):
    code_graphs: List[FunctionDBModel]
