script = """
#!/bin/bash

# Prompt user for necessary arguments
read -p "What's your github repo name: " repo_name
read -p "What's your github URL: " user_repo_url


# Check if tag is empty and set default
if [ -z "$tag" ]; then
    tag="latest"
fi

# Pull the Docker image
echo "Pulling the Docker image..."
docker pull ghcr.io/autogpt-agent/backend-chat:latest

# Run the Docker container with user-provided arguments
echo "Running the Docker container..."
docker run -p 8501:8501 \
  -e REPO_URL=$user_repo_url \
  -e PERSIST_DIRECTORY="db/$repo_name" \
  ghcr.io/autogpt-agent/backend-chat:latest

echo "Chat is running on http://localhost:8501"
""".lstrip()
