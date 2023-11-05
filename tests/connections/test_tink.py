from unittest.mock import MagicMock, patch

import pytest

from ecobud.connections.tink import (
    create_user,
    delete_user,
    get_client_token,
    get_user,
    get_user_authorization_code,
    get_user_token,
    get_user_transactions,
)


@patch("ecobud.connections.tink.fmt_response", MagicMock())
@patch("ecobud.connections.tink.curl", MagicMock())
@patch("ecobud.connections.tink.re.post")
def test_get_client_token(mock_post):
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


@patch("ecobud.connections.tink.fmt_response", MagicMock())
@patch("ecobud.connections.tink.curl", MagicMock())
@patch("ecobud.connections.tink.get_client_token")
@patch("ecobud.connections.tink.re.post")
def test_get_user_authorization_code(mock_post, mock_get_client_token):
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


@patch("ecobud.connections.tink.fmt_response", MagicMock())
@patch("ecobud.connections.tink.curl", MagicMock())
@patch("ecobud.connections.tink.get_user_authorization_code")
@patch("ecobud.connections.tink.re.post")
def test_get_user_token(mock_post, mock_get_user_authorization_code):
    # Arrange
    mock_get_user_authorization_code.return_value = "test_code"
    mock_response = mock_post.return_value
    mock_response.json.return_value = {"access_token": "test_token"}

    expected_url = "https://api.tink.com/api/v1/oauth/token"
    expected_data = {
        "client_id": "tink-client-id",  # see pyproject.toml
        "client_secret": "tink-client-secret",  # see pyproject.toml
        "grant_type": "authorization_code",
        "code": "test_code",
    }

    # Act
    actual_token = get_user_token(username="test_user", scope="test_scope")

    # Assert
    mock_get_user_authorization_code.assert_called_once_with("test_user", "test_scope")
    mock_post.assert_called_once_with(url=expected_url, data=expected_data)
    assert actual_token == "test_token"


@patch("ecobud.connections.tink.fmt_response", MagicMock())
@patch("ecobud.connections.tink.curl", MagicMock())
@patch("ecobud.connections.tink.get_client_token")
@patch("ecobud.connections.tink.re.post")
def test_create_user(mock_post, mock_get_client_token):
    # Arrange
    mock_get_client_token.return_value = "test_token"
    mock_response = mock_post.return_value
    mock_response.json.return_value = {"user": "test_user"}

    expected_url = "https://api.tink.com/api/v1/user/create"
    expected_headers = {
        "Authorization": "Bearer test_token",
        "Content-Type": "application/json",
    }
    expected_data = {
        "external_user_id": "test_user",
        "market": "GB",
        "locale": "en_US",
        "retention_class": "permanent",
    }

    # Act
    actual_response = create_user(username="test_user")

    # Assert
    mock_get_client_token.assert_called_once_with("user:create")
    mock_post.assert_called_once_with(url=expected_url, json=expected_data, headers=expected_headers)
    assert actual_response == {"user": "test_user"}


@patch("ecobud.connections.tink.fmt_response", MagicMock())
@patch("ecobud.connections.tink.curl", MagicMock())
@patch("ecobud.connections.tink.get_user_token")
@patch("ecobud.connections.tink.re.get")
def test_get_user(mock_get, mock_get_user_token):
    # Arrange
    mock_get_user_token.return_value = "test_token"
    mock_response = mock_get.return_value
    mock_response.json.return_value = {"user": "test_user"}

    expected_url = "https://api.tink.com/api/v1/user"
    expected_headers = {"Authorization": "Bearer test_token"}

    # Act
    actual_user = get_user(username="test_user")

    # Assert
    mock_get_user_token.assert_called_once_with("test_user", "user:read")
    mock_get.assert_called_once_with(url=expected_url, headers=expected_headers)
    assert actual_user == {"user": "test_user"}


@patch("ecobud.connections.tink.fmt_response", MagicMock())
@patch("ecobud.connections.tink.curl", MagicMock())
@patch("ecobud.connections.tink.get_user_token")
@patch("ecobud.connections.tink.re.post")
def test_delete_user(mock_post, mock_get_user_token):
    # Arrange
    mock_get_user_token.return_value = "test_token"
    mock_response = mock_post.return_value
    mock_response.json.return_value = {"status": "deleted"}

    expected_url = "https://api.tink.com/api/v1/user/delete"
    expected_headers = {"Authorization": "Bearer test_token"}

    # Act
    actual_response = delete_user(username="test_user")

    # Assert
    mock_get_user_token.assert_called_once_with("test_user", "user:delete")
    mock_post.assert_called_once_with(url=expected_url, headers=expected_headers)
    assert actual_response == {"status": "deleted"}


@patch("ecobud.connections.tink.fmt_response", MagicMock())
@patch("ecobud.connections.tink.curl", MagicMock())
@patch("ecobud.connections.tink.get_user_token")
@patch("ecobud.connections.tink.re.get")
def test_get_user_transactions(mock_get, mock_get_user_token):
    # Arrange
    mock_get_user_token.return_value = "test_token"
    mock_response = mock_get.return_value
    mock_response.json.return_value = {
        "transactions": [{"id": "1", "amount": 100}, {"id": "2", "amount": 200}],
        "nextPageToken": None,
    }

    expected_url = "https://api.tink.com/data/v2/transactions"
    expected_headers = {"Authorization": "Bearer test_token"}

    # Act
    actual_transactions = get_user_transactions(username="test_user", noPages=1)

    # Assert
    mock_get_user_token.assert_called_once_with("test_user", "transactions:read")
    mock_get.assert_called_once_with(url=expected_url, headers=expected_headers, params={})
    assert actual_transactions == [{"id": "1", "amount": 100}, {"id": "2", "amount": 200}]
