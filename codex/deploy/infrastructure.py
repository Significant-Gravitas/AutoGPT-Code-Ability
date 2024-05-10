import logging
import os

import psycopg2
from dotenv import load_dotenv
from google.auth import default
from googleapiclient.discovery import build
from psycopg2 import sql

import codex.common.utils

load_dotenv()
logger = logging.getLogger(__name__)


def create_postgres_database(db_name):
    logger.info(f"Attempting to create database {db_name}")

    USER_DB_ADMIN: str | None = os.getenv("USER_DB_ADMIN")
    if not USER_DB_ADMIN:
        raise EnvironmentError("USER_DB_ADMIN not found in environment variables.")

    USER_DB_PASS = os.getenv("USER_DB_PASS")
    if not USER_DB_PASS:
        raise EnvironmentError("USER_DB_PASS not found in environment variables.")

    USER_CONN_NAME = os.getenv("USER_CONN_NAME")
    if not USER_CONN_NAME:
        raise EnvironmentError("USER_CONN_NAME not found in environment variables.")

    conn = psycopg2.connect(
        dbname="postgres",
        user=USER_DB_ADMIN,
        password=USER_DB_PASS,
        host=USER_CONN_NAME,
    )
    conn.autocommit = True  # Necessary to execute a create database command
    cur = conn.cursor()

    # Create database
    cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))

    cur.close()
    conn.close()
    logger.info(f"Database {db_name} created successfully.")


def setup_cloudsql_db(db_username, db_password):
    logger.info(f"Attempting to create user {db_username}")
    PROJECT_ID = os.getenv("GCP_PROJECT_ID", default="codex-user-deployments-dev")
    if not PROJECT_ID:
        raise EnvironmentError("GCP project ID not found in environment variables.")
    INSTANCE_ID = os.getenv("CLOUD_SQL_INSTANCE_ID", default="codex-user-db-dev")
    if not INSTANCE_ID:
        raise EnvironmentError(
            "Cloud SQL instance ID not found in environment variables."
        )

    credentials, _ = default()

    service = build("sqladmin", "v1beta4", credentials=credentials)
    user_body = {"name": db_username, "password": db_password}

    response = (
        service.users()
        .insert(project=PROJECT_ID, instance=INSTANCE_ID, body=user_body)
        .execute()
    )

    logger.info(f"User creation response: {response}")


def grant_permissions_postgres(db_name, new_user):
    logger.info(f"Attempting to grant user {new_user} permissions on {db_name}")

    DB_USER: str | None = os.getenv("USER_DB_ADMIN", default="postgres")
    if not DB_USER:
        raise EnvironmentError("USER_DB_ADMIN not found in environment variables.")

    DB_PASS = os.getenv("USER_DB_PASS")
    if not DB_PASS:
        raise EnvironmentError("USER_DB_PASS not found in environment variables.")

    DB_CONN = os.getenv("USER_CONN_NAME")
    if not DB_CONN:
        raise EnvironmentError("USER_CONN_NAME not found in environment variables.")

    conn = psycopg2.connect(
        dbname="postgres",
        user=DB_USER,
        password=DB_PASS,
        host=DB_CONN,
    )

    conn.autocommit = (
        True  # Ensure commands are committed without a separate commit statement
    )
    cur = conn.cursor()

    # Grant permissions
    cur.execute(
        sql.SQL(
            """
        GRANT CONNECT ON DATABASE {db} TO {user};
        GRANT USAGE, CREATE ON SCHEMA public TO {user};
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {user};
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO {user};
        """
        ).format(db=sql.Identifier(db_name), user=sql.Identifier(new_user))
    )
    logger.info(f"Permissions successfully granted to {new_user} on {db_name}.")

    cur.close()
    conn.close()


def add_secret_to_repo(repo_name: str, secret_name: str, secret_value: str):
    from github import Github  # noqa

    """Add a secret to the GitHub repository."""

    logger.info(f"Attempting to add secret {secret_name} on {repo_name}")
    GIT_TOKEN: str | None = os.environ.get("GIT_TOKEN")
    if not GIT_TOKEN:
        raise EnvironmentError("GitHub token not found in environment variables.")

    g = Github(GIT_TOKEN)
    repo = g.get_repo(repo_name)
    repo.create_secret(secret_name, secret_value, secret_type="actions")

    logger.info(
        f"Secret {secret_name} of value {secret_value} successfully added to {repo_name}"
    )


async def create_cloud_db(repo_url: str) -> tuple[str, str]:
    """
    Creates CloudSQL DB for users
    Args:
        repo_url (str): The repository URL

    Returns:
        str, str: Database username and name
    """
    logger.info("Starting DB processes.")

    try:
        # create database
        repo_name = repo_url.split("/")[-1]
        db_name = repo_name + "_db"
        create_postgres_database(db_name)

        # create db credentials
        user, password = codex.common.utils.generate_db_credentials()

        # create user in cloudsql
        setup_cloudsql_db(user, password)

        # grant user permissions to db
        grant_permissions_postgres(db_name, user)

        # update secrets
        org_repo_name = "agpt-coder/" + repo_name
        add_secret_to_repo(org_repo_name, "DB_USER", user)
        add_secret_to_repo(org_repo_name, "DB_PASS", password)
        add_secret_to_repo(org_repo_name, "DB_NAME", db_name)

        return db_name, user
    except Exception as e:
        logger.exception(e)
        raise e
