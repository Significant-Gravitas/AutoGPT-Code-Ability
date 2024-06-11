import uuid
import asyncio
from datetime import datetime, timedelta, timezone
from codex_client import CodexClient
import logging

import streamlit as st


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Streamlit app
if "id" not in st.session_state:
    st.session_state.id = uuid.uuid4()
    st.session_state.file_cache = {}
if "process_complete" not in st.session_state:
    st.session_state.process_complete = False

session_id = st.session_state.id
client = None

st.set_page_config(layout="wide")

if not st.session_state.process_complete:
    st.title("AutoGPT Coding Ability")

    # Input fields
    client_url = "http://localhost:8080/api/v1"
    project_name = st.text_input("Name your project")
    task = st.text_area("Describe your project")
    user_id = ""
    codex_id = ""

    # Initialize session state attributes
    if "progress" not in st.session_state:
        st.session_state.progress = 0
    if "codex_client" not in st.session_state:
        st.session_state.codex_client = None
    if "interview_response" not in st.session_state:
        st.session_state.interview_response = None
    if "user_message" not in st.session_state:
        st.session_state.user_message = ""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    async def init_codex_client(user_id, codex_id, client_url):
        codex_client = CodexClient(base_url=client_url)
        await codex_client.init(cloud_services_user_id=user_id, codex_user_id=codex_id)
        st.session_state.codex_client = codex_client

    async def create_app_and_start_interview(codex_client):
        try:
            app = await codex_client.create_app(app_name=project_name, description=task)
            st.session_state.app_id = app.id
            logger.info(f"Application Created: {app.id}")
            st.session_state.messages.append("App creation started! Let's gooo")

            interview = await codex_client.start_interview(name=project_name, task=task)
            st.session_state.interview_id = interview.id
            st.session_state.progress = 1
            st.session_state.interview_response = interview
            st.session_state.messages.append(interview.say_to_user)
        except Exception as e:
            logger.error(f"Failed to create app: {e}")
            st.error(f"Failed to create app: {e}")

    async def handle_interview(codex_client, interview_response, user_message):
        try:
            interview_response = await codex_client.interview_next(user_message)
            st.session_state.messages.append(interview_response.say_to_user)
            st.session_state.interview_response = interview_response

            if interview_response.phase_completed:
                if interview_response.phase in ["ARCHITECT", "COMPLETED"]:
                    future_time = datetime.now(timezone.utc) + timedelta(minutes=15)
                    future_timestamp = int(future_time.timestamp())
                    st.session_state.messages.append(
                        f"{interview_response.say_to_user}. Expected completion time: {future_timestamp}"
                    )
                    st.session_state.progress = 2
                elif interview_response.phase == "FEATURES":
                    st.session_state.messages.append(interview_response.say_to_user)
                    st.session_state.interview_response = interview_response
                    interview_response = await codex_client.interview_next("")
                    st.session_state.messages.append(interview_response.say_to_user)
        except Exception as e:
            logger.error(f"Failed to handle interview: {e}")
            st.error(f"Failed to handle interview: {e}")

    async def generate_spec(codex_client):
        try:
            spec_response = await codex_client.generate_spec()
            st.session_state.spec_id = spec_response.id
            logger.info(f"Spec Generated: {spec_response.id}")
            st.session_state.messages.append("Specification Generated!")
            st.session_state.progress = 3
            st.experimental_rerun()
            return spec_response
        except Exception as e:
            logger.error(f"Failed to generate spec: {e}")
            st.error(f"Failed to generate spec: {e}")

    async def generate_deliverable(codex_client):
        try:
            deliverable_response = await codex_client.generate_deliverable()
            st.session_state.deliverable_id = deliverable_response.id
            logger.info(f"Deliverable Generated: {deliverable_response.id}")
            st.session_state.messages.append("Deliverable Generated!")
            st.session_state.progress = 4
            st.experimental_rerun()
            return deliverable_response
        except Exception as e:
            logger.error(f"Failed to generate deliverable: {e}")
            st.error(f"Failed to generate deliverable: {e}")

    async def create_deployment(codex_client):
        try:
            deployment_response = await codex_client.create_deployment()
            st.session_state.deployment_id = deployment_response.id
            logger.info(f"Deployment Generated: {deployment_response.id}")
            st.session_state.messages.append("Deployment Created!")
            st.session_state.messages.append(f"GitHub Repo: {deployment_response.repo}")
            st.session_state.progress = 5
            st.session_state.github_repo = deployment_response.repo

            st.experimental_rerun()
            return deployment_response
        except Exception as e:
            logger.error(f"Failed to create deployment: {e}")
            st.error(f"Failed to create deployment: {e}")

    async def main():
        if st.session_state.codex_client is None:
            await init_codex_client(user_id, codex_id, client_url)

        if st.session_state.progress == 0:
            await create_app_and_start_interview(st.session_state.codex_client)

        if st.session_state.progress == 1 and st.session_state.user_message:
            await handle_interview(
                st.session_state.codex_client,
                st.session_state.interview_response,
                st.session_state.user_message,
            )
            st.session_state.user_message = (
                ""  # Reset the user message after handling it
            )

        if st.session_state.progress == 2:
            st.write("Generating Specification...")
            await generate_spec(st.session_state.codex_client)

        if st.session_state.progress == 3:
            st.write("Generating Deliverable...")
            await generate_deliverable(st.session_state.codex_client)

        if st.session_state.progress == 4:
            st.write("Creating Deployment...")
            await create_deployment(st.session_state.codex_client)

    if st.button("Start Building"):
        asyncio.run(main())

    # Display all messages in chronological order
    for message in st.session_state.messages:
        st.write(message)

    if st.session_state.progress == 1:
        user_message = st.text_input("Your response", key="user_response")
        if st.button("Submit Response"):
            st.session_state.user_message = user_message
            asyncio.run(
                handle_interview(
                    st.session_state.codex_client,
                    st.session_state.interview_response,
                    user_message,
                )
            )
            st.experimental_rerun()

    if st.session_state.progress in [2, 3, 4, 5]:
        asyncio.run(main())
