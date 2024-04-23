PRISMA_FILE_HEADER = """
// datasource db defines the database connection settings.
// It is configured for PostgreSQL and uses an environment variable for the connection URL.
// The 'extensions' feature enables the use of PostgreSQL-specific data types.
datasource db {
  provider   = "postgresql"
  url        = env("DATABASE_URL")
}

// generator db configures Prisma Client settings.
// It is set up to use Prisma Client Python with asyncio interface and specific features.
generator db {
  provider                    = "prisma-client-py"
  interface                   = "asyncio"
  recursive_type_depth        = 5
  previewFeatures             = ["postgresqlExtensions"]
  enable_experimental_decimal = true
}

"""

TODO_COMMENT = "# TODO(autogpt):"
