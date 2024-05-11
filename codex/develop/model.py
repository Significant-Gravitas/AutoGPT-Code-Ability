from typing import List

from prisma.models import Function
from prisma.models import Function as FunctionDBModel
from prisma.models import ObjectType
from pydantic import BaseModel

from codex.common.model import FunctionDef
from codex.common.model import ObjectTypeModel as ObjectDef
from codex.develop.function import generate_object_code, generate_object_template


class FunctionResponse(BaseModel):
    id: str
    name: str
    requirements: list[str]
    code: str


class Package(BaseModel):
    package_name: str
    version: str | None = None
    specifier: str | None = None

    def __str__(self):
        if self.version:
            return f"{self.package_name}{self.specifier}{self.version}"
        else:
            return self.package_name


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

    functions: List[FunctionDef]
    objects: List[ObjectDef]
    db_schema: str

    def get_compiled_code(self) -> str:
        return "\n".join(self.imports) + "\n\n" + self.rawCode.strip()

    def regenerate_compiled_code(self, add_code_stubs: bool = True) -> str:
        """
        Regenerate imports & raw code using the available objects and functions.
        """
        imports = self.imports.copy()
        for obj in self.available_objects.values():
            imports.extend(obj.importStatements)
        self.imports = sorted(set(imports))

        def __append_comment(code_block: str, comment: str) -> str:
            """
            Append `# noqa` to the first line of the code block.
            This is to suppress flake8 warnings for redefined names.
            """
            lines = code_block.split("\n")
            lines[0] = lines[0] + " # " + comment
            return "\n".join(lines)

        def __generate_stub(name, is_enum):
            if not name:
                return ""
            elif is_enum:
                return f"class {name}(Enum):\n    pass"
            else:
                return f"class {name}(BaseModel):\n    pass"

        stub_objects = self.available_objects if add_code_stubs else {}
        stub_functions = self.available_functions if add_code_stubs else {}

        object_stubs_code = "\n\n".join(
            [
                __append_comment(__generate_stub(obj.name, obj.isEnum), "type: ignore")
                for obj in stub_objects.values()
            ]
            + [
                __append_comment(__generate_stub(obj.name, obj.is_enum), "type: ignore")
                for obj in self.objects
                if obj.name not in stub_objects
            ]
        )

        objects_code = "\n\n".join(
            [
                __append_comment(generate_object_template(obj), "noqa")
                for obj in stub_objects.values()
            ]
            + [
                __append_comment(generate_object_code(obj), "noqa")
                for obj in self.objects
                if obj.name not in stub_objects
            ]
        )

        functions_code = "\n\n".join(
            [
                __append_comment(f.template.strip(), "type: ignore")
                for f in stub_functions.values()
                if f.functionName != self.function_name
            ]
            + [
                __append_comment(f.function_template.strip(), "type: ignore")
                for f in self.functions
                if f.name not in stub_functions and f.function_template
            ]
        )

        self.rawCode = (
            object_stubs_code.strip()
            + "\n\n"
            + objects_code.strip()
            + "\n\n"
            + functions_code.strip()
            + "\n\n"
            + self.functionCode.strip()
        )

        return self.get_compiled_code()


class ApplicationGraphs(BaseModel):
    code_graphs: List[FunctionDBModel]
