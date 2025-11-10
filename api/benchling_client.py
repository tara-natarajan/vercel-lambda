"""Benchling client initialization and authentication."""
import os
from benchling_sdk.benchling import Benchling
from benchling_sdk.auth.client_credentials_oauth2 import ClientCredentialsOAuth2


def get_benchling_client() -> Benchling:
    """
    Initialize and return Benchling client with OAuth2 authentication.
    
    Required environment variables:
    - BENCHLING_URL: Your Benchling tenant URL
    - BENCHLING_CLIENT_ID: OAuth2 client ID
    - BENCHLING_CLIENT_SECRET: OAuth2 client secret
    
    Returns:
        Benchling: Authenticated Benchling client instance
    
    Raises:
        ValueError: If required environment variables are not set
    """
    base_url = os.environ.get('BENCHLING_URL')
    client_id = os.environ.get('BENCHLING_CLIENT_ID')
    client_secret = os.environ.get('BENCHLING_CLIENT_SECRET')
    
    if not base_url:
        raise ValueError("BENCHLING_URL must be set in environment variables")
    if not client_id or not client_secret:
        raise ValueError("BENCHLING_CLIENT_ID and BENCHLING_CLIENT_SECRET must be set in environment variables")
    
    token_url = f"{base_url}/api/v2/token"
    
    return Benchling(
        url=base_url,
        auth_method=ClientCredentialsOAuth2(client_id, client_secret, token_url),
    )

