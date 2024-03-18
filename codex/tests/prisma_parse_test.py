import pytest

from codex.common.parse_prisma import parse_prisma_schema


@pytest.mark.unit
def test_valid_prisma_schema():
    schema = """
model User {
    id Int @id @default(autoincrement())
    name String
    email String @unique
    posts Post[]
}

model Post {
    id Int @id @default(autoincrement())
    title String
    content String
    published Boolean @default(false)
    author User @relation(fields: [authorId], references: [id])
    authorId Int
}
    """
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
    assert (
        response.models["User"].definition
        == "model User {\n    id Int @id @default(autoincrement())\n    name String\n    email String @unique\n    posts Post[]\n}"
    )

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
    assert (
        response.models["Post"].definition
        == "model Post {\n    id Int @id @default(autoincrement())\n    title String\n    content String\n    published Boolean @default(false)\n    author User @relation(fields: [authorId], references: [id])\n    authorId Int\n}"
    )

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
    from codex.common.ai_block import ValidationError
    from codex.develop.develop import validate_normalize_prisma_code

    # Models & enum should be replaced with fully qualified name
    db_schema = """
        model User {}
        model UserPost {}
        enum UserRole {}
        enum RoleType {}
    """
    imports = [
        "from prisma import enums",
        "from prisma.models import User",
        "from prisma.models import UserPost as UserPostDB",
        "from prisma.models import ObjectType",
        "from prisma.enums import UserRole",
        "import pydantic",
    ]
    code = (
        "result = "
        "(User.select().where(UserPostDB.id == 1), "
        "UserRole.Tutor, "
        "enums.RoleType.Admin)"
    )

    imports, code = validate_normalize_prisma_code(db_schema, imports, code)

    assert set(imports) == set(
        [
            "import pydantic",
            "import prisma",
        ]
    )
    assert code == (
        "result = "
        "(prisma.models.User.select().where(prisma.models.UserPost.id == 1), "
        "prisma.enums.UserRole.Tutor, "
        "prisma.enums.RoleType.Admin)"
    )

    # catch validation error without using db_schema
    with pytest.raises(ValidationError):
        validate_normalize_prisma_code("", imports, code)
