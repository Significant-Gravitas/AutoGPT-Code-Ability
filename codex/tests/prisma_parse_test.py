import pytest

from codex.common.parse_prisma import parse_prisma_schema
from codex.develop.code_validation import validate_normalize_prisma
from codex.develop.model import GeneratedFunctionResponse


@pytest.mark.unit
def test_valid_prisma_schema():
    model_user_definition = """
model User {
    id Int @id @default(autoincrement())
    name String
    email String @unique
    posts Post[]
}""".lstrip()

    model_post_definition = """
model Post {
    id Int @id @default(autoincrement())
    title String
    content String
    published Boolean @default(false)
    author User @relation(fields: [authorId], references: [id])
    authorId Int
}""".lstrip()

    model_search_log_definition = """
model SearchLog {
    id String @id @default(dbgenerated("gen_random_uuid()"))
    createdAt DateTime @default(now())
    updatedAt DateTime @updatedAt
    userId String
    query String
    filters Json // Example: {"location": "New York", "skills": ["Python", "Django"]}
}""".lstrip()

    schema = "\n".join(
        f"{m}\n"
        for m in (
            model_user_definition,
            model_post_definition,
            model_search_log_definition,
        )
    )

    response = parse_prisma_schema(schema)
    # User Object
    assert response.models["User"].fields["id"].type == "Int"
    assert response.models["User"].fields["id"].attributes == [
        "@id",
        "@default(autoincrement())",
    ]
    assert response.models["User"].fields["name"].type == "String"
    assert response.models["User"].fields["email"].type == "String"
    assert response.models["User"].fields["email"].attributes == ["@unique"]
    assert response.models["User"].fields["posts"].type == "Post[]"
    assert response.models["User"].definition == model_user_definition

    # Post Object
    assert response.models["Post"].fields["id"].type == "Int"
    assert response.models["Post"].fields["id"].attributes == [
        "@id",
        "@default(autoincrement())",
    ]
    assert response.models["Post"].fields["title"].type == "String"
    assert response.models["Post"].fields["content"].type == "String"
    assert response.models["Post"].fields["published"].type == "Boolean"
    assert response.models["Post"].fields["published"].attributes == ["@default(false)"]
    assert response.models["Post"].fields["author"].type == "User"
    assert (
        response.models["Post"].fields["author"].relation
        == "@relation(fields: [authorId], references: [id])"
    )
    assert response.models["Post"].fields["authorId"].type == "Int"
    assert response.models["Post"].definition == model_post_definition

    # SearchLog Object
    assert response.models["SearchLog"].fields["id"].type == "String"
    assert response.models["SearchLog"].fields["id"].attributes == [
        "@id",
        '@default(dbgenerated("gen_random_uuid()"))',
    ]
    assert response.models["SearchLog"].fields["createdAt"].type == "DateTime"
    assert response.models["SearchLog"].fields["createdAt"].attributes == [
        "@default(now())"
    ]
    assert response.models["SearchLog"].fields["updatedAt"].type == "DateTime"
    assert response.models["SearchLog"].fields["updatedAt"].attributes == ["@updatedAt"]
    assert response.models["SearchLog"].fields["userId"].type == "String"
    assert response.models["SearchLog"].fields["query"].type == "String"
    assert response.models["SearchLog"].fields["filters"].type == "Json"
    assert response.models["SearchLog"].definition == model_search_log_definition

    # No enums
    assert response.enums == {}


@pytest.mark.unit
def test_complex():
    # Example usage
    schema_text = """
enum UserRole {
    Tutor
    Client
}enum InvoiceStatus {
    Paid
    Unpaid
    Failed
}model User {
    id              Int         @id @default(autoincrement())
    email           String      @unique
    password        String?
    role            UserRole    @default(Client)
    OAuthProviderId String?
    OAuthProvider   String?
    appointments    Appointment[]
    invoices        Invoice[]
    FinancialReport FinancialReport[]
}model Appointment {
    id            Int          @id @default(autoincrement())
    tutorId       Int
    clientId      Int
    scheduledTime DateTime
    status        String
    tutor         User         @relation(fields: [tutorId], references: [id])
    client        User         @relation(fields: [clientId], references: [id])
    Invoice       Invoice?
}model Invoice {
    id            Int          @id @default(autoincrement())
    appointmentId Int
    amount        Float
    status        InvoiceStatus
    appointment   Appointment  @relation(fields: [appointmentId], references: [id])
    paidBy        User         @relation("UserInvoices")
}model FinancialReport {
    id           Int      @id @default(autoincrement())
    tutorId      Int
    periodStart  DateTime
    periodEnd    DateTime
    totalIncome  Float
    tutor        User     @relation(fields: [tutorId], references: [id])
}model SearchLog {
    id        String   @id @default(dbgenerated("gen_random_uuid()"))
    createdAt DateTime @default(now())
    updatedAt DateTime @updatedAt
    userId    String
    query     String
    filters   Json     // Example: {"location": "New York", "skills": ["Python", "Django"]}
}
    """
    response = parse_prisma_schema(schema_text)
    # UserRole Enum
    assert response.enums["UserRole"].values == ["Tutor", "Client"]
    assert (
        response.enums["UserRole"].definition
        == "enum UserRole {\n    Tutor\n    Client\n}"
    )

    # InvoiceStatus Enum
    assert response.enums["InvoiceStatus"].values == ["Paid", "Unpaid", "Failed"]
    assert (
        response.enums["InvoiceStatus"].definition
        == "enum InvoiceStatus {\n    Paid\n    Unpaid\n    Failed\n}"
    )

    # User Object
    assert response.models["User"].fields["id"].type == "Int"
    assert response.models["User"].fields["id"].attributes == [
        "@id",
        "@default(autoincrement())",
    ]
    assert response.models["User"].fields["email"].type == "String"
    assert response.models["User"].fields["email"].attributes == ["@unique"]
    assert response.models["User"].fields["password"].type == "String?"
    assert response.models["User"].fields["role"].type == "UserRole"
    assert response.models["User"].fields["role"].attributes == ["@default(Client)"]
    assert response.models["User"].fields["OAuthProviderId"].type == "String?"
    assert response.models["User"].fields["OAuthProvider"].type == "String?"
    assert response.models["User"].fields["appointments"].type == "Appointment[]"
    assert response.models["User"].fields["invoices"].type == "Invoice[]"
    assert response.models["User"].fields["FinancialReport"].type == "FinancialReport[]"
    assert (
        response.models["User"].definition
        == "model User {\n    id              Int         @id @default(autoincrement())\n    email           String      @unique\n    password        String?\n    role            UserRole    @default(Client)\n    OAuthProviderId String?\n    OAuthProvider   String?\n    appointments    Appointment[]\n    invoices        Invoice[]\n    FinancialReport FinancialReport[]\n}"
    )

    # Appointment Object
    assert response.models["Appointment"].fields["id"].type == "Int"
    assert response.models["Appointment"].fields["id"].attributes == [
        "@id",
        "@default(autoincrement())",
    ]
    assert response.models["Appointment"].fields["tutorId"].type == "Int"
    assert response.models["Appointment"].fields["clientId"].type == "Int"
    assert response.models["Appointment"].fields["scheduledTime"].type == "DateTime"
    assert response.models["Appointment"].fields["status"].type == "String"
    assert response.models["Appointment"].fields["tutor"].type == "User"
    assert (
        response.models["Appointment"].fields["tutor"].relation
        == "@relation(fields: [tutorId], references: [id])"
    )
    assert response.models["Appointment"].fields["client"].type == "User"
    assert (
        response.models["Appointment"].fields["client"].relation
        == "@relation(fields: [clientId], references: [id])"
    )
    assert response.models["Appointment"].fields["Invoice"].type == "Invoice?"
    assert (
        response.models["Appointment"].definition
        == "model Appointment {\n    id            Int          @id @default(autoincrement())\n    tutorId       Int\n    clientId      Int\n    scheduledTime DateTime\n    status        String\n    tutor         User         @relation(fields: [tutorId], references: [id])\n    client        User         @relation(fields: [clientId], references: [id])\n    Invoice       Invoice?\n}"
    )

    # Invoice Object
    assert response.models["Invoice"].fields["id"].type == "Int"
    assert response.models["Invoice"].fields["id"].attributes == [
        "@id",
        "@default(autoincrement())",
    ]
    assert response.models["Invoice"].fields["appointmentId"].type == "Int"
    assert response.models["Invoice"].fields["amount"].type == "Float"
    assert response.models["Invoice"].fields["status"].type == "InvoiceStatus"
    assert response.models["Invoice"].fields["appointment"].type == "Appointment"
    assert (
        response.models["Invoice"].fields["appointment"].relation
        == "@relation(fields: [appointmentId], references: [id])"
    )
    assert response.models["Invoice"].fields["paidBy"].type == "User"
    assert (
        response.models["Invoice"].fields["paidBy"].relation
        == '@relation("UserInvoices")'
    )
    assert (
        response.models["Invoice"].definition
        == 'model Invoice {\n    id            Int          @id @default(autoincrement())\n    appointmentId Int\n    amount        Float\n    status        InvoiceStatus\n    appointment   Appointment  @relation(fields: [appointmentId], references: [id])\n    paidBy        User         @relation("UserInvoices")\n}'
    )

    # FinancialReport Object
    assert response.models["FinancialReport"].fields["id"].type == "Int"
    assert response.models["FinancialReport"].fields["id"].attributes == [
        "@id",
        "@default(autoincrement())",
    ]
    assert response.models["FinancialReport"].fields["tutorId"].type == "Int"
    assert response.models["FinancialReport"].fields["periodStart"].type == "DateTime"
    assert response.models["FinancialReport"].fields["periodEnd"].type == "DateTime"
    assert response.models["FinancialReport"].fields["totalIncome"].type == "Float"
    assert response.models["FinancialReport"].fields["tutor"].type == "User"
    assert (
        response.models["FinancialReport"].fields["tutor"].relation
        == "@relation(fields: [tutorId], references: [id])"
    )
    assert (
        response.models["FinancialReport"].fields["tutor"].relation
        == "@relation(fields: [tutorId], references: [id])"
    )
    assert (
        response.models["FinancialReport"].definition
        == "model FinancialReport {\n    id           Int      @id @default(autoincrement())\n    tutorId      Int\n    periodStart  DateTime\n    periodEnd    DateTime\n    totalIncome  Float\n    tutor        User     @relation(fields: [tutorId], references: [id])\n}"
    )


@pytest.mark.unit
def test_with_datasource():
    schema_text = """
datasource db {
    provider   = "postgresql"
    url        = env("DATABASE_URL")
    extensions = [vector]
}enum UserRole {
    Tutor
    Client
}model User {
    id              Int         @id @default(autoincrement())
    email           String      @unique
    password        String?
    role            UserRole    @default(Client)
    OAuthProviderId String?
    OAuthProvider   String?
    appointments    Appointment[]
    invoices        Invoice[]
    FinancialReport FinancialReport[]
}
    """
    response = parse_prisma_schema(schema_text)

    # DataSource
    assert response.datasource
    assert response.datasource.provider == "postgresql"
    assert response.datasource.url == 'env("DATABASE_URL")'
    assert response.datasource.extensions == ["vector"]
    assert response.datasource.name == "db"

    # UserRole Enum
    assert response.enums["UserRole"]
    assert response.enums["UserRole"].name == "UserRole"
    assert response.enums["UserRole"].values == ["Tutor", "Client"]
    assert (
        response.enums["UserRole"].definition
        == "enum UserRole {\n    Tutor\n    Client\n}"
    )

    # User Object
    assert response.models["User"]
    assert response.models["User"].name == "User"
    assert response.models["User"].fields["id"].type == "Int"
    assert response.models["User"].fields["id"].attributes == [
        "@id",
        "@default(autoincrement())",
    ]
    assert response.models["User"].fields["email"].type == "String"
    assert response.models["User"].fields["email"].attributes == ["@unique"]
    assert response.models["User"].fields["password"].type == "String?"
    assert response.models["User"].fields["role"].type == "UserRole"
    assert response.models["User"].fields["role"].attributes == ["@default(Client)"]
    assert response.models["User"].fields["OAuthProviderId"].type == "String?"
    assert response.models["User"].fields["OAuthProvider"].type == "String?"
    assert response.models["User"].fields["appointments"].type == "Appointment[]"
    assert response.models["User"].fields["invoices"].type == "Invoice[]"
    assert response.models["User"].fields["FinancialReport"].type == "FinancialReport[]"
    assert (
        response.models["User"].definition
        == "model User {\n    id              Int         @id @default(autoincrement())\n    email           String      @unique\n    password        String?\n    role            UserRole    @default(Client)\n    OAuthProviderId String?\n    OAuthProvider   String?\n    appointments    Appointment[]\n    invoices        Invoice[]\n    FinancialReport FinancialReport[]\n}"
    )


@pytest.mark.unit
def test_with_generator():
    schema_text = """
generator client {
    provider             = "prisma-client-py"
    interface            = "asyncio"
    recursive_type_depth = 5
    previewFeatures      = ["postgresqlExtensions"]
}generator docs {
    provider = "prisma-docs"
    output   = "docs"
}enum UserRole {
    Tutor
    Client
}model User {
    id              Int         @id @default(autoincrement())
    email           String      @unique
    password        String?
    role            UserRole    @default(Client)
    OAuthProviderId String?
    OAuthProvider   String?
    appointments    Appointment[]
    invoices        Invoice[]
    FinancialReport FinancialReport[]
}
    """
    response = parse_prisma_schema(schema_text)

    # Generator
    assert response.generators
    assert response.generators[0].name == "client"
    assert response.generators[0].provider == "prisma-client-py"
    assert response.generators[0].config == {
        "interface": "asyncio",
        "recursive_type_depth": "5",
        "previewFeatures": ["postgresqlExtensions"],
    }

    assert response.generators[1].name == "docs"
    assert response.generators[1].provider == "prisma-docs"
    assert response.generators[1].config == {"output": "docs"}

    assert response.enums["UserRole"]
    assert response.enums["UserRole"].values == ["Tutor", "Client"]
    assert (
        response.enums["UserRole"].definition
        == "enum UserRole {\n    Tutor\n    Client\n}"
    )

    assert response.models["User"].fields["id"].type == "Int"
    assert response.models["User"].fields["id"].attributes == [
        "@id",
        "@default(autoincrement())",
    ]
    assert response.models["User"].fields["email"].type == "String"
    assert response.models["User"].fields["email"].attributes == ["@unique"]
    assert response.models["User"].fields["password"].type == "String?"
    assert response.models["User"].fields["role"].type == "UserRole"
    assert response.models["User"].fields["role"].attributes == ["@default(Client)"]
    assert response.models["User"].fields["OAuthProviderId"].type == "String?"
    assert response.models["User"].fields["OAuthProvider"].type == "String?"
    assert response.models["User"].fields["appointments"].type == "Appointment[]"
    assert response.models["User"].fields["invoices"].type == "Invoice[]"
    assert response.models["User"].fields["FinancialReport"].type == "FinancialReport[]"
    assert (
        response.models["User"].definition
        == "model User {\n    id              Int         @id @default(autoincrement())\n    email           String      @unique\n    password        String?\n    role            UserRole    @default(Client)\n    OAuthProviderId String?\n    OAuthProvider   String?\n    appointments    Appointment[]\n    invoices        Invoice[]\n    FinancialReport FinancialReport[]\n}"
    )


def test_with_generator_and_datasource():
    schema_text = """
generator client {
    provider             = "prisma-client-py"
    interface            = "asyncio"
    recursive_type_depth = 5
    previewFeatures      = ["postgresqlExtensions"]
}datasource db {
    provider   = "postgresql"
    url        = env("DATABASE_URL")
    extensions = [vector]
}enum UserRole {
    Tutor
    Client
}model User {
    id              Int         @id @default(autoincrement())
    email           String      @unique
    password        String?
    role            UserRole    @default(Client)
    OAuthProviderId String?
    OAuthProvider   String?
    appointments    Appointment[]
    invoices        Invoice[]
    FinancialReport FinancialReport[]
}
    """
    response = parse_prisma_schema(schema_text)
    assert response.enums["UserRole"]
    assert response.enums["UserRole"].values == ["Tutor", "Client"]
    assert (
        response.enums["UserRole"].definition
        == "enum UserRole {\n    Tutor\n    Client\n}"
    )

    assert response.models["User"].fields["id"].type == "Int"
    assert response.models["User"].fields["id"].attributes == [
        "@id",
        "@default(autoincrement())",
    ]
    assert response.models["User"].fields["email"].type == "String"
    assert response.models["User"].fields["email"].attributes == ["@unique"]
    assert response.models["User"].fields["password"].type == "String?"
    assert response.models["User"].fields["role"].type == "UserRole"
    assert response.models["User"].fields["role"].attributes == ["@default(Client)"]
    assert response.models["User"].fields["OAuthProviderId"].type == "String?"
    assert response.models["User"].fields["OAuthProvider"].type == "String?"
    assert response.models["User"].fields["appointments"].type == "Appointment[]"
    assert response.models["User"].fields["invoices"].type == "Invoice[]"
    assert response.models["User"].fields["FinancialReport"].type == "FinancialReport[]"
    assert (
        response.models["User"].definition
        == "model User {\n    id              Int         @id @default(autoincrement())\n    email           String      @unique\n    password        String?\n    role            UserRole    @default(Client)\n    OAuthProviderId String?\n    OAuthProvider   String?\n    appointments    Appointment[]\n    invoices        Invoice[]\n    FinancialReport FinancialReport[]\n}"
    )

    # assert response.datasource
    # assert response.datasource.provider == "postgresql"
    # assert response.datasource.url == 'env("DATABASE_URL")'
    # assert response.datasource.extensions == ["vector"]

    # assert response.generator
    # assert response.generator.provider == "prisma-client-py"
    # assert response.generator.interface == "asyncio


def test_prisma_code_validation():
    # Models & enum should be replaced with fully qualified name
    db_schema = """
        model User {}
        model UserPost {}
        enum UserRole {}
        enum RoleType {}
    """
    imports = [
        "from prisma import models",
        "from prisma import enums",
        "from prisma.models import User",
        "from prisma.models import UserPost as UserPostDB",
        "from prisma.models import ObjectType",
        "from prisma.enums import UserRole",
        "import pydantic",
    ]
    code = """
        def test():
            return (
                User.select().where(UserPostDB.id == 1),
                models.UserRole.Tutor,
                enums.RoleType.Admin
            )
    """

    func = GeneratedFunctionResponse(
        function_name="test",
        available_objects={},
        available_functions={},
        template="",
        rawCode=code,
        packages=[],
        imports=imports,
        functionCode=code,
        functions=[],
        objects=[],
        db_schema=db_schema,
        compiled_route_id="",
    )

    errors = validate_normalize_prisma(func)
    assert errors == []
    assert set(func.imports) == {
        "import pydantic",
        "import prisma",
        "import prisma.enums",
        "import prisma.models",
    }
    assert (
        func.rawCode
        == """
        def test():
            return (
                prisma.models.User.select().where(prisma.models.UserPost.id == 1),
                prisma.enums.UserRole.Tutor,
                prisma.enums.RoleType.Admin
            )
    """
    )
    # catch validation error without using db_schema
    func.db_schema = ""
    errors = validate_normalize_prisma(func)[0]
    assert "not available in the prisma schema" in str(errors)
