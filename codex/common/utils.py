import json
import os
import string
import secrets
from typing import Dict, Any


def generate_db_credentials(username_prefix="user", password_length=16):
    username = f"{username_prefix}{secrets.randbelow(9999)}"
    characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    password = "".join(secrets.choice(characters) for i in range(password_length))
    return username, password

def get_config_from_env() -> Dict[str, Any]:
    config_json = os.getenv('AI_PROVIDER_CONFIG')
    if config_json:
        return json.loads(config_json)

    config = {
        "name": os.getenv('AI_PROVIDER_NAME', 'openai'),
        "client_config": {
            "api_key": os.getenv('AI_PROVIDER_API_KEY'),
        },
        "model": os.getenv('AI_PROVIDER_MODEL', 'gpt-4o'),
    }
    return config