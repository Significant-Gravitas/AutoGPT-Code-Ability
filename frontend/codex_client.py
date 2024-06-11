from typing import Tuple
import logging
import aiohttp
from pydantic import ValidationError
from typing import Optional
from codex_model import (
    ApplicationResponse,
    ApplicationCreate,
    InterviewResponse,
    InterviewNextRequest,
    SpecificationResponse,
    DeliverableResponse,
    DeploymentResponse,
    UserResponse,
)

logger = logging.getLogger(__name__)

CLOUD_SERVICES_ID = "7b3a9e01-4ede-4a56-919b-d7063ba3c6e3"
DISCORD_ID = "6984891672811274234"


class CodexClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        auth_key: Optional[str] = None,
    ):
        """
        Initialize the codex client.

        Args:
            base_url (str, optional): the base url for the codex service. Defaults to None to use the production url.
            auth_key (str, optional): the authorization key for the codex service. Defaults to None.
        """
        # Set the base url for codex
        self.user = None
        if not base_url:
            self.base_url = "http://localhost:8080/api/v1"
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
        cloud_services_user_id: Optional[str] = None,
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
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8080/api/v1/user",
                params={
                    "cloud_services_id": CLOUD_SERVICES_ID,
                    "discord_id": DISCORD_ID,
                },
                headers={"accept": "application/json"},
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    user_response = UserResponse(**data)
                    self.user = user_response
                    self.codex_user_id = self.user.id
                else:
                    # Handle error case
                    raise Exception(f"Failed to fetch/create user: {response.status}")

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

    async def create_app(self, app_name: str, description: str) -> ApplicationResponse:
        """
        Creates a new app for the given user.

        Args:
            app_name (str): The name of the new app to be created.
            description (str): The description of the new app to be created.

        Returns:
            ApplicationResponse: The response from the server after attempting to create the app.
        """

        url = f"{self.base_url}/user/{self.codex_user_id}/apps/"
        data = ApplicationCreate(name=app_name, description=description)

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
        except aiohttp.ClientError as e:
            logger.exception(f"HTTP error occurred: {e}")
            raise e
        except Exception as err:
            logger.exception(f"An error occurred: {err}")
            raise

    @staticmethod
    async def build_codex_client(
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
        Build the codex client without database dependency.

        Returns:
            CodexClient: The codex client.
        """
        codex = CodexClient(
            base_url=base_url,
            auth_key=auth_key,
        )
        await codex.init(
            cloud_services_user_id=cloud_services_user_id,
            codex_user_id=codex_user_id,
        )

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
