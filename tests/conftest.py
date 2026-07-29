import pytest
import os
import jwt
import time
from unittest.mock import patch
from postgrest import SyncPostgrestClient


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    # Mock de secrets usando patch para evitar TypeError: 'Secrets' object does not support item assignment
    mock_secrets = {"use_local_db": True}

    # PostgREST local (docker-compose) publica en host :3001
    if not os.getenv("API_URL"):
        os.environ["API_URL"] = "http://localhost:3001"

    with patch('streamlit.secrets', mock_secrets):
        os.environ['SUPABASE_URL'] = os.environ["API_URL"]
        os.environ['SUPABASE_KEY'] = 'super-secret-jwt-token-with-at-least-32-characters-long'
        yield


@pytest.fixture(scope="module")
def db_client():
    """Cliente PostgREST contra Docker local (API_URL)."""
    api_url = os.getenv("API_URL", "http://localhost:3001")
    secret = "super-secret-jwt-token-with-at-least-32-characters-long"
    payload = {
        "role": "admin",
        "iss": "supabase",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    api_key = jwt.encode(payload, secret, algorithm="HS256")
    return SyncPostgrestClient(
        api_url,
        headers={"apikey": api_key, "Authorization": f"Bearer {api_key}"},
    )
