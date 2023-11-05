from unittest.mock import MagicMock, patch

import pytest

from ecobud.connections.tink import get_client_token, get_user_authorization_code


@patch("ecobud.connections.tink.fmt_response")
@patch("ecobud.connections.tink.curl")
@patch("ecobud.connections.tink.re.post")
def test_get_client_token(mock_post, mock_curl, mock_fmt_response):
    # Arrange
    mock_response = mock_post.return_value
    mock_response.json.return_value = {"access_token": "test_token"}

    expected_url = "https://api.tink.com/api/v1/oauth/token"
    expected_data = {
        "client_id": "tink-client-id",  # see pyproject.toml
        "client_secret": "tink-client-secret",  # see pyproject.toml
        "grant_type": "client_credentials",
        "scope": "accounts:read",
    }

    # Act
    actual_token = get_client_token(scope="accounts:read")

    # Assert
    mock_post.assert_called_once_with(url=expected_url, data=expected_data)
    assert actual_token == "test_token"


@patch("ecobud.connections.tink.fmt_response")
@patch("ecobud.connections.tink.curl")
@patch("ecobud.connections.tink.get_client_token")
@patch("ecobud.connections.tink.re.post")
def test_get_user_authorization_code(mock_post, mock_get_client_token, mock_curl, mock_fmt_response):
    # Arrange
    mock_get_client_token.return_value = "test_token"
    mock_response = mock_post.return_value
    mock_response.json.return_value = {"code": "test_code"}

    expected_url = "https://api.tink.com/api/v1/oauth/authorization-grant"
    expected_headers = {"Authorization": "Bearer test_token"}
    expected_data = {
        "external_user_id": "test_user",
        "scope": "test_scope",
    }

    # Act
    actual_code = get_user_authorization_code(username="test_user", scope="test_scope")

    # Assert
    mock_get_client_token.assert_called_once_with(scope="authorization:grant", grant_type="client_credentials")
    mock_post.assert_called_once_with(url=expected_url, data=expected_data, headers=expected_headers)
    assert actual_code == "test_code"
