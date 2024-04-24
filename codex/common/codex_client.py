import logging
from datetime import datetime
from typing import Optional, Tuple

import aiohttp
from prisma import Prisma
from pydantic import BaseModel, ValidationError

from codex.api_model import (
    ApplicationCreate,
    ApplicationResponse,
    DeliverableResponse,
    DeploymentResponse,
    Identifiers,
    InterviewNextRequest,
    SpecificationResponse,
    UserCreate,
    UserResponse,
)
from codex.common.logging_config import setup_logging
from codex.interview.model import InterviewResponse

logger = logging.getLogger(__name__)


class CodexClient:
    def __init__(
        self,
        client: Prisma,
        base_url: Optional[str] = None,
        auth_key: Optional[str] = None,
    ):
        """
        Initialize the codex client.

        Args:
            client (Prisma): the prisma client
            base_url (str, optional): the base url for the codex service. Defaults to None to use the production url.
            auth_key (str, optional): the authorization key for the codex service. Defaults to None.
        """
        # Set the DB Client
        self.client = client

        # Set the base url for codex
        if not base_url:
            self.base_url = "https://codegen-xca4qjgx4a-uc.a.run.app/api/v1"
        else:
            self.base_url = base_url

        # Set the headers
        self.headers: dict[str, str] = {"accept": "application/json"}
        if auth_key:
            self.headers["Authorization"] = f"Bearer {auth_key}"

        self.app_id: Optional[str] = None
        self.interview_id: Optional[str] = None
        self.specification_id: Optional[str] = None
        self.deliverable_id: Optional[str] = None
        self.deployment_id: Optional[str] = None

    async def init(
        self,
        codex_user_id: Optional[str] = None,
        app_id: Optional[str] = None,
        interview_id: Optional[str] = None,
        specification_id: Optional[str] = None,
        deliverable_id: Optional[str] = None,
        deployment_id: Optional[str] = None,
    ):
        """
        Initialize the async part of the codex client.

        Sets the user and the codex_user_id.

        Args:
            cloud_services_user_id (str): the id of the user in the cloud services
            codex_user_id (str): the id of the user in the codex service
        """
        # require either cloud_services_user_id or discord_user_id
        if not codex_user_id:
            raise ValueError("You must provide a codex_user_id")
        self.codex_user_id = codex_user_id
        if app_id:
            self.app_id = app_id
        if interview_id:
            self.interview_id = interview_id
        if specification_id:
            self.specification_id = specification_id
        if deliverable_id:
            self.deliverable_id = deliverable_id
        if deployment_id:
            self.deployment_id = deployment_id

    async def create_or_get_codex_user(
        self, discord_id: str, cloud_services_id: str = ""
    ) -> UserResponse:
        """
        Get or create the user from the codex service.

        This is used in the __init__ so be weary of what self.<attribute> are available.

        Args:
            discord_id (str): the discord id of the user
        """
        url = f"{self.base_url}/user"
        obj = UserCreate(cloud_services_id=cloud_services_id, discord_id=discord_id)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, headers=self.headers, params=obj.model_dump()
                ) as response:
                    response.raise_for_status()
                    user_response = UserResponse(**await response.json())
                    return user_response

        except aiohttp.ClientError as e:
            logger.exception(f"Error getting user: {e}")
            raise e
        except ValidationError as e:
            logger.exception(f"Error parsing user: {e}")
            raise e
        except Exception as e:
            logger.exception(f"Unknown Error when trying to get user: {e}")
            raise e

    async def create_app(
        self, app_name: str, app_description: str
    ) -> ApplicationResponse:
        """
        Creates a new app for the given user.

        Args:
            user_id (int): The ID of the user for whom the app is being created.
            app_name (str): The name of the new app to be created.
            description (str): The description of the new app to be created.

        Returns:
            ApplicationResponse: The response from the server after attempting to create the app.
        """
        url = f"{self.base_url}/user/{self.codex_user_id}/apps/"
        # headers = {"accept": "application/json", "Content-Type": "application/json"}

        data = ApplicationCreate(name=app_name, description=app_description)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, headers=self.headers, json=data.model_dump()
                ) as response:
                    response.raise_for_status()
                    app_response = ApplicationResponse(**await response.json())
                    self.app_id = app_response.id
                    return app_response

        except aiohttp.ClientError as e:
            logger.exception(f"Error creating app: {e}")
            raise e
        except ValidationError as e:
            logger.exception(f"Error parsing app: {e}")
            raise e
        except Exception as e:
            logger.exception(f"Unknown Error when trying to create an app: {e}")
            raise e

    async def get_app(self, app_id: Optional[str] = None) -> ApplicationResponse:
        """
        Get the app from the codex service.

        Args:
            app_id (str): the id of the app

        Returns:
            ApplicationResponse: the response from the server after attempting to get the app.
        """
        if not app_id and not self.app_id:
            raise ValueError("You must provide an app_id to get the app")
        url = f"{self.base_url}/user/{self.codex_user_id}/apps/{app_id or self.app_id}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    response.raise_for_status()
                    app_response = ApplicationResponse(**await response.json())
                    return app_response

        except aiohttp.ClientError as e:
            logger.exception(f"Error getting app: {e}")
            raise e
        except ValidationError as e:
            logger.exception(f"Error parsing app: {e}")
            raise e
        except Exception as e:
            logger.exception(f"Unknown Error when trying to get app: {e}")
            raise e

    async def start_interview(
        self,
        name: str,
        task: str,
    ) -> InterviewResponse:
        """
        Start an interview for the app.
        """
        if not self.app_id:
            raise ValueError("You must create an app before starting an interview")
        url = f"{self.base_url}/user/{self.codex_user_id}/apps/{self.app_id}/interview/"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers) as response:
                    if response.status != 200:
                        logger.error(f"Error starting interview: {response.status}")
                        logger.error(await response.text())
                    response.raise_for_status()
                    interview_response = InterviewResponse(**await response.json())
                    self.interview_id = interview_response.id
                    return interview_response
        except aiohttp.ClientError as e:
            logger.exception(f"Error starting interview: {e}")
            raise e
        except ValidationError as e:
            logger.exception(f"Error parsing interview: {e}")
            raise e
        except Exception as e:
            logger.exception(f"Unknown Error when trying to start the interview: {e}")
            raise e

    async def interview_next(self, user_message: str) -> InterviewResponse:
        """
        Answer the next question in the interview.

        Args:
            user_id (int): The ID of the user for whom the interview is being answered.
            app_id (int): The ID of the app for which the interview is being answered.
            interview_id (int): The ID of the interview for which the question is being answered.
            user_message (str): A message from the user
        Returns:
            InterviewResponse: The response from the server after attempting to answer the next question in the interview.
        """
        if not self.app_id or not self.interview_id:
            raise ValueError(
                "You must create an app and participate in an interview before answering the next question"
            )
        url = f"{self.base_url}/user/{self.codex_user_id}/apps/{self.app_id}/interview/{self.interview_id}/next"

        obj = InterviewNextRequest(msg=user_message)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, headers=self.headers, json=obj.model_dump()
                ) as response:
                    response.raise_for_status()
                    interview_response = InterviewResponse(**await response.json())
                    return interview_response
        except aiohttp.ClientError as e:
            logger.exception(f"Error answering next question: {e}")
            raise e
        except ValidationError as e:
            logger.exception(f"Error parsing next question: {e}")
            raise e
        except Exception as e:
            logger.exception(
                f"Unknown Error when trying to answer the next question: {e}"
            )
            raise e

    async def generate_spec(self) -> SpecificationResponse:
        """
        Generate the requirements for the app based on the given description.

         Args:
             user_id (int): The ID of the user for whom the spec is being generated.
             app_id (int): The ID of the app for which the spec is being generated.
             description (str): The description of the requirements for the app.

         Returns:
             SpecificationResponse: The response from the server after attempting to generate the app specifications.
        """
        if not self.app_id and not self.interview_id:
            raise ValueError(
                "You must create an app and participate in an interview before generating a spec"
            )
        url = f"{self.base_url}/user/{self.codex_user_id}/apps/{self.app_id}/specs/"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self.headers,
                    timeout=3000,
                    params={"interview_id": self.interview_id},
                ) as response:
                    response.raise_for_status()
                    spec_response = SpecificationResponse(**await response.json())
                    self.specification_id = spec_response.id
                    return spec_response

        except aiohttp.ClientError as e:
            logger.exception(f"Error generating app spec: {e}")
            raise e
        except ValidationError as e:
            logger.exception(f"Error parsing app spec: {e}")
            raise e
        except Exception as e:
            logger.exception(f"Unknown Error when trying to generate the spec: {e}")
            raise e

    async def generate_deliverable(self) -> DeliverableResponse:
        """
        Generate the deliverable for the app based on a specific specification.

        Returns:
            DeliverableResponse: The response from the server after attempting to generate the app deliverable.
        """
        if not self.app_id or not self.specification_id:
            raise ValueError(
                "You must create an app and generate a spec before generating a deliverable"
            )
        url = f"{self.base_url}/user/{self.codex_user_id}/apps/{self.app_id}/specs/{self.specification_id}/deliverables/"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, headers=self.headers, timeout=3000
                ) as response:
                    response.raise_for_status()
                    deliverable_response = DeliverableResponse(**await response.json())
                    self.deliverable_id = deliverable_response.id
                    return deliverable_response

        except aiohttp.ClientError as e:
            logger.exception(f"Error generating app deliverable: {e}")
            raise e
        except ValidationError as e:
            logger.exception(f"Error parsing app deliverable: {e}")
            raise e

        except Exception as e:
            logger.exception(
                f"Unknown Error when trying to generate the deliverable: {e}"
            )
            raise e

    async def create_deployment(self) -> DeploymentResponse:
        """
        Create a deployment for the app based on the deliverable.

        Args:
            user_id (int): The ID of the user for whom the deployment is being created.
            app_id (int): The ID of the app for which the deployment is being created.
            spec_id (int): The ID of the specification based on which the deployment is created.
            deliverable_id (int): The ID of the deliverable based on which the deployment is created.

        Returns:
            DeploymentResponse: The response from the server after attempting to create the app deployment.
        """
        if not self.app_id or not self.specification_id or not self.deliverable_id:
            raise ValueError(
                "You must create an app, generate a spec, and generate a deliverable before creating a deployment"
            )
        url = f"{self.base_url}/user/{self.codex_user_id}/apps/{self.app_id}/specs/{self.specification_id}/deliverables/{self.deliverable_id}/deployments/"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers) as response:
                    if response.status != 200:
                        logger.error(f"Error creating deployment: {response.status}")
                        logger.error(await response.text())
                    response.raise_for_status()
                    deployment_response = DeploymentResponse(**await response.json())
                    self.deployment_id = deployment_response.id
                    return deployment_response
        except aiohttp.ClientError as e:
            logger.exception(f"Error creating app deployment: {e}")
            raise e
        except ValidationError as e:
            logger.exception(f"Error parsing app deployment: {e}")
            raise e
        except Exception as e:
            logger.exception(f"Unknown Error when trying to create the deployment: {e}")
            raise e

    async def download_zip(self) -> Tuple[bytes, str]:
        """
        Step 6: Download the deployment zip file.

        Note: The request returns a FastAPI streaming response.

        Returns:
            Tuple[bytes, str]: The bytes of the zip file and the name of the file.
        """
        if not self.deployment_id:
            raise ValueError("You must create a deployment before downloading a zip")
        url = f"{self.base_url}/deployments/{self.deployment_id}/download"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    response.raise_for_status()
                    content = await response.read()
                    filename = response.headers.get("Content-Disposition", "").split(
                        "filename="
                    )[1]
                    return content, filename
            # with requests.get(url, stream=True) as response:
            #     response.raise_for_status()  # Raises stored HTTPError, if one occurred.

            #     # Extract filename from Content-Disposition header if available.
            #     filename = "deployment.zip"  # Default filename if not found in headers.
            #     cd = response.headers.get("Content-Disposition")
            #     if cd:
            #         filenames = [
            #             fn.strip().split("=")[1] if "filename=" in fn else None
            #             for fn in cd.split(";")
            #         ]
            #         filename = next((fn.strip('"') for fn in filenames if fn), filename)

            #     # Download the content.
            #     content = response.content

            #     return content, filename
        except aiohttp.ClientError as e:
            logger.exception(f"HTTP error occurred: {e}")
            raise e
        except Exception as err:
            logger.exception(f"An error occurred: {err}")
            raise

    @staticmethod
    async def build_codex_client(
        client: "Prisma",
        cloud_services_user_id: str,
        codex_user_id: str,
        base_url: Optional[str] = None,
        auth_key: Optional[str] = None,
        app_id: Optional[str] = None,
        interview_id: Optional[str] = None,
        spec_id: Optional[str] = None,
        deliverable_id: Optional[str] = None,
        deployment_id: Optional[str] = None,
    ) -> "CodexClient":
        """
        Build the codex client from the database.

        Returns:
            CodexClient: The codex client.
        """
        codex = CodexClient(
            client=client,
            base_url=base_url,
            auth_key=auth_key,
        )
        await codex.init(
            codex_user_id=codex_user_id,
        )

        # throw an error if app -> spec -> deliverable -> deployment is not followed
        if interview_id and not app_id:
            raise ValueError(
                "You must provide an app_id if you provide an interview_id"
            )
        if spec_id and not interview_id and not app_id:
            raise ValueError(
                "You must provide an app_id and interview_id if you provide a spec_id"
            )
        if deliverable_id and not spec_id and not app_id:
            raise ValueError(
                "You must provide an app_id and a spec_id if you provide a deliverable_id"
            )
        if deployment_id and not deliverable_id and not spec_id and not app_id:
            raise ValueError(
                "You must provide an app_id, a spec_id, and a deliverable_id if you provide a deployment_id"
            )

        codex.app_id = app_id
        codex.interview_id = interview_id
        codex.specification_id = spec_id
        codex.deliverable_id = deliverable_id
        codex.deployment_id = deployment_id

        return codex


class TestModel(BaseModel):
    content: bytes
    filename: str
    deployment: DeploymentResponse
    deliverable: DeliverableResponse
    spec: SpecificationResponse
    interview: InterviewResponse
    app: ApplicationResponse


async def from_existing(db_client: Prisma, identifier: Identifiers) -> TestModel:
    await db_client.connect()

    if not identifier.cloud_services_id:
        raise ValueError("Cloud Services ID not found")
    if not identifier.user_id:
        raise ValueError("User ID not found")

    codex_client = await CodexClient.build_codex_client(
        client=db_client,
        cloud_services_user_id=identifier.cloud_services_id,
        codex_user_id=identifier.user_id,
        base_url="http://localhost:8007/api/v1",
        app_id=identifier.app_id,
        interview_id=identifier.spec_id,
        spec_id=identifier.spec_id,
        deliverable_id=identifier.completed_app_id,
    )
    logger.info(f"User: {codex_client.codex_user_id}")
    app = await codex_client.get_app()
    logger.info(f"App: {app.id}")
    # spec = await codex_client.get_spec()
    deliverable = await codex_client.generate_deliverable()
    logger.info(f"Deliverable: {deliverable.id}")
    deployment = await codex_client.create_deployment()
    logger.info(f"Deployment: {deployment.id}")
    content, filename = await codex_client.download_zip()
    await db_client.disconnect()
    return TestModel(
        content=content,
        filename=filename,
        deployment=deployment,
        deliverable=deliverable,
        interview=InterviewResponse(
            id=identifier.interview_id or "",
            say_to_user="Test Interview",
            features=[],
            phase_completed=True,
        ),
        spec=SpecificationResponse(
            id=identifier.spec_id or "",
            name="Test Spec",
            createdAt=datetime.now(),
            context="",
        ),
        app=app,
    )


async def partial(db_client: Prisma, identifier: Identifiers) -> TestModel:
    await db_client.connect()
    if not identifier.cloud_services_id:
        raise ValueError("Cloud Services ID not found")
    if not identifier.user_id:
        raise ValueError("User ID not found")

    codex_client = await CodexClient.build_codex_client(
        client=db_client,
        cloud_services_user_id=identifier.cloud_services_id,
        codex_user_id=identifier.user_id,
        base_url="http://localhost:8007/api/v1",
        app_id=identifier.app_id,
    )
    print(f"User: {codex_client.codex_user_id}")
    app = await codex_client.get_app()
    logger.info(f"App: {app.id}")
    interview = await codex_client.start_interview(
        "Test Interview", "Create a calulator api"
    )
    logger.info(f"Interview: {interview.id}")
    while True:
        interview_next = await codex_client.interview_next("Make it please")
        if interview_next.phase_completed:
            break
    spec = await codex_client.generate_spec()
    logger.info(f"Spec: {spec.id}")
    deliverable = await codex_client.generate_deliverable()
    logger.info(f"Deliverable: {deliverable.id}")
    deployment = await codex_client.create_deployment()
    logger.info(f"Deployment: {deployment.id}")
    content, filename = await codex_client.download_zip()

    await db_client.disconnect()
    return TestModel(
        content=content,
        filename=filename,
        deployment=deployment,
        deliverable=deliverable,
        spec=spec,
        interview=interview,
        app=app,
    )


if __name__ == "__main__":
    from asyncio import run

    from common.test_const import identifier_1

    setup_logging()

    db_client = Prisma(auto_register=True)

    response = run(
        from_existing(
            db_client,
            Identifiers(
                user_id=identifier_1.user_id,
                cloud_services_id=identifier_1.cloud_services_id,
                app_id=identifier_1.app_id,
                spec_id="814c2c78-fa4f-4162-9f25-aa1b947e9874",
            ),
        )
    )
    with open(response.filename, "wb") as f:
        f.write(response.content)
    logger.info(f"Downloaded {response.filename}")
    logger.info(f"{response!r}")
    logger.info("Done")

    response = run(partial(db_client, identifier_1))
    with open(response.filename, "wb") as f:
        f.write(response.content)
    logger.info(f"Downloaded {response.filename}")
    logger.info(f"{response!r}")
    logger.info("Done")
