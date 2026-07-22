import pytest
import os
import streamlit as st
from unittest.mock import patch

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    # Mock de secrets usando patch para evitar TypeError: 'Secrets' object does not support item assignment
    mock_secrets = {"use_local_db": True}
    
    with patch('streamlit.secrets', mock_secrets):
        os.environ['SUPABASE_URL'] = 'http://localhost:3000'
        os.environ['SUPABASE_KEY'] = 'super-secret-jwt-token-with-at-least-32-characters-long'
        yield
