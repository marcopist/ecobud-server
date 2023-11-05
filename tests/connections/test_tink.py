from unittest.mock import MagicMock, patch

from ecobud.connections.tink import (
    create_user,
    delete_user,
    get_bank_connection_url,
    get_client_token,
    get_user,
    get_user_authorization_code,
    get_user_token,
    get_user_transactions,
    register_transaction_webhook,
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
@patch("ecobud.connections.tink.get_client_token")
@patch("ecobud.connections.tink.re.post")
def test_get_user_authorization_code_with_delegate(mock_post, mock_get_client_token):
    # Arrange
    mock_get_client_token.return_value = "test_token"
    mock_response = mock_post.return_value
    mock_response.json.return_value = {"code": "test_code"}

    expected_url = "https://api.tink.com/api/v1/oauth/authorization-grant/delegate"
    expected_headers = {
        "Authorization": "Bearer test_token",
    }
    expected_data = {
        "external_user_id": "test_user",
        "scope": "authorization:grant",
        "actor_client_id": "actor_client_id",
        "id_hint": "hint",
    }

    kwargs = {
        "actor_client_id": "actor_client_id",
        "id_hint": "hint",
    }

    # Act
    actual_code = get_user_authorization_code(
        username="test_user", scope="authorization:grant", delegate=True, **kwargs
    )

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


@patch("ecobud.connections.tink.get_user_authorization_code")
def test_get_bank_connection_url(mock_get_user_authorization_code):
    # Arrange
    mock_get_user_authorization_code.return_value = "test_code"
    expected_url = (
        "https://link.tink.com/1.0/transactions/connect-accounts"
        "?client_id=tink-client-id"  # see pyproject.toml
        "&redirect_uri=https://console.tink.com/callback"
        "&authorization_code=test_code"
        "&market=GB"
        "&locale=en_US"
    )

    # Act
    actual_url = get_bank_connection_url(username="test_user")

    # Assert
    mock_get_user_authorization_code.assert_called_once_with(
        "test_user",
        scope=(
            "authorization:read,"
            "authorization:grant,"
            "credentials:refresh,"
            "credentials:read,"
            "credentials:write,"
            "providers:read,"
            "user:read"
        ),
        delegate=True,
        actor_client_id="df05e4b379934cd09963197cc855bfe9",
        id_hint="hint",
    )
    assert actual_url == expected_url


@patch("ecobud.connections.tink.fmt_response", MagicMock())
@patch("ecobud.connections.tink.curl", MagicMock())
@patch("ecobud.connections.tink.get_client_token")
@patch("ecobud.connections.tink.re.post")
def test_register_transaction_webhook(mock_post, mock_get_client_token):
    # Arrange
    mock_get_client_token.return_value = "test_token"
    mock_response = mock_post.return_value
    mock_response.json.return_value = {"status": "registered"}

    expected_url = "https://api.tink.com/events/v2/webhook-endpoints"
    expected_headers = {
        "Authorization": "Bearer test_token",
        "Content-Type": "application/json",
    }
    expected_data = {
        "description": "webhook",
        "disabled": False,
        "enabledEvents": ["account-transactions:modified"],
        "url": "self-url/tink/webhook",
    }

    # Act
    actual_response = register_transaction_webhook()

    # Assert
    mock_get_client_token.assert_called_once_with("webhook-endpoints")
    mock_post.assert_called_once_with(url=expected_url, json=expected_data, headers=expected_headers)
    assert actual_response == {"status": "registered"}


@patch("ecobud.connections.tink.fmt_response", MagicMock())
@patch("ecobud.connections.tink.curl", MagicMock())
@patch("ecobud.connections.tink.get_client_token")
@patch("ecobud.connections.tink.re.post")
def test_register_transaction_webhook_with_url(mock_post, mock_get_client_token):
    # Arrange
    mock_get_client_token.return_value = "test_token"
    mock_response = mock_post.return_value
    mock_response.json.return_value = {"status": "registered"}

    expected_url = "https://api.tink.com/events/v2/webhook-endpoints"
    expected_headers = {
        "Authorization": "Bearer test_token",
        "Content-Type": "application/json",
    }
    expected_data = {
        "description": "webhook",
        "disabled": False,
        "enabledEvents": ["account-transactions:modified"],
        "url": "http://example.com/webhook",
    }

    # Act
    actual_response = register_transaction_webhook(webhook_url="http://example.com/webhook")

    # Assert
    mock_get_client_token.assert_called_once_with("webhook-endpoints")
    mock_post.assert_called_once_with(url=expected_url, json=expected_data, headers=expected_headers)
    assert actual_response == {"status": "registered"}
