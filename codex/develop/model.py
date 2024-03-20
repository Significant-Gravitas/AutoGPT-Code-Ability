from typing import List

from prisma.models import Function, ObjectType
from prisma.models import Function as FunctionDBModel
from pydantic import BaseModel

from codex.common.model import FunctionDef
from codex.common.model import ObjectTypeModel as ObjectDef
from codex.develop.function import generate_object_code, generate_object_template


class Package(BaseModel):
    package_name: str
    version: str | None = None
    specifier: str | None = None


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

    def regenerate_compiled_code(self) -> str:
        """
        Regenerate imports & raw code using the available objects and functions.
        """
        imports = self.imports.copy()
        for obj in self.available_objects.values():
            imports.extend(obj.importStatements)
        self.imports = sorted(set(imports))

        def __generate_stub(name, is_enum):
            if not name:
                return ""
            elif is_enum:
                return f"class {name}(Enum):\n    pass"
            else:
                return f"class {name}(BaseModel):\n    pass"

        template_code = "\n\n".join(
            [
                __generate_stub(obj.name, obj.isEnum)
                for obj in self.available_objects.values()
            ]
            + [
                __generate_stub(obj.name, obj.is_enum)
                for obj in self.objects
                if obj.name not in self.available_objects
            ]
        )

        def __append_no_qa(code_block: str) -> str:
            """
            Append `# noqa` to the first line of the code block.
            This is to suppress flake8 warnings for redefined names.
            """
            lines = code_block.split("\n")
            lines[0] = lines[0] + " # noqa"
            return "\n".join(lines)

        objects_code = "\n\n".join(
            [
                __append_no_qa(generate_object_template(obj))
                for obj in self.available_objects.values()
            ]
            + [
                __append_no_qa(generate_object_code(obj))
                for obj in self.objects
                if obj.name not in self.available_objects
            ]
        )

        functions_code = "\n\n".join(
            [
                f.template.strip()
                for f in self.available_functions.values()
                if f.functionName != self.function_name
            ]
            + [
                f.function_code.strip()
                for f in self.functions
                if f.name not in self.available_functions
            ]
        )

        self.rawCode = (
            template_code.strip()
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
