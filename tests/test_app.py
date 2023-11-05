from unittest.mock import Mock, patch

from flask import json

from ecobud.app import UserAlreadyExists, UserNotFound, WrongPassword, app


@patch("ecobud.app.create_user")
def test_user_post_success(mock_create_user):
    # Arrange
    test_client = app.test_client()
    request_data = {"username": "test_user", "email": "test@example.com", "password": "test_password"}

    # Act
    response = test_client.post("/user", data=json.dumps(request_data), content_type="application/json")

    # Assert
    mock_create_user.assert_called_once_with("test_user", "test@example.com", "test_password")
    assert response.status_code == 201
    assert response.get_json() == {"username": "test_user"}


@patch("ecobud.app.create_user")
def test_user_post_user_already_exists(mock_create_user):
    # Arrange
    test_client = app.test_client()
    request_data = {"username": "test_user", "email": "test@example.com", "password": "test_password"}
    mock_create_user.side_effect = UserAlreadyExists

    # Act
    response = test_client.post("/user", data=json.dumps(request_data), content_type="application/json")

    # Assert
    mock_create_user.assert_called_once_with("test_user", "test@example.com", "test_password")
    assert response.status_code == 409
    assert response.get_json() == {"error": "User already exists"}


@patch("ecobud.app.login_user")
def test_login_post_success(mock_login_user):
    # Arrange
    test_client = app.test_client()
    request_data = {"username": "test_user", "password": "test_password"}

    # Act
    response = test_client.post("/login", data=json.dumps(request_data), content_type="application/json")

    # Assert
    mock_login_user.assert_called_once_with("test_user", "test_password")
    assert response.status_code == 200
    assert response.get_json() == {"username": "test_user"}


@patch("ecobud.app.login_user")
def test_login_post_user_not_found(mock_login_user):
    # Arrange
    test_client = app.test_client()
    request_data = {"username": "test_user", "password": "test_password"}
    mock_login_user.side_effect = UserNotFound

    # Act
    response = test_client.post("/login", data=json.dumps(request_data), content_type="application/json")

    # Assert
    mock_login_user.assert_called_once_with("test_user", "test_password")
    assert response.status_code == 404
    assert response.get_json() == {"error": "User not found"}


@patch("ecobud.app.login_user")
def test_login_post_wrong_password(mock_login_user):
    # Arrange
    test_client = app.test_client()
    request_data = {"username": "test_user", "password": "test_password"}
    mock_login_user.side_effect = WrongPassword

    # Act
    response = test_client.post("/login", data=json.dumps(request_data), content_type="application/json")

    # Assert
    mock_login_user.assert_called_once_with("test_user", "test_password")
    assert response.status_code == 401
    assert response.get_json() == {"error": "Wrong password"}


@patch("ecobud.app.get_bank_connection_url")
def test_bank_post_logged_in(mock_get_bank_connection_url):
    # Arrange
    test_client = app.test_client()
    with test_client.session_transaction() as sess:
        sess["username"] = "test_user"
    mock_get_bank_connection_url.return_value = "http://bank.com/connect"

    # Act
    response = test_client.get("/bank/link")

    # Assert
    mock_get_bank_connection_url.assert_called_once_with("test_user")
    assert response.status_code == 200
    assert response.get_json() == {"url": "http://bank.com/connect"}


def test_bank_post_not_logged_in():
    # Arrange
    test_client = app.test_client()

    # Act
    response = test_client.get("/bank/link")

    # Assert
    assert response.status_code == 401
    assert response.get_json() == {"error": "Not logged in"}


@patch("ecobud.app.get_user_transactions")
def test_transactions_get_logged_in(mock_get_user_transactions):
    # Arrange
    test_client = app.test_client()
    with test_client.session_transaction() as sess:
        sess["username"] = "test_user"
    mock_get_user_transactions.return_value = [{"id": "1", "amount": 100}]

    # Act
    response = test_client.get("/tink/transactions")

    # Assert
    mock_get_user_transactions.assert_called_once_with("test_user")
    assert response.status_code == 200
    assert response.get_json() == {"transactions": [{"id": "1", "amount": 100}]}


def test_transactions_get_not_logged_in():
    # Arrange
    test_client = app.test_client()

    # Act
    response = test_client.get("/tink/transactions")

    # Assert
    assert response.status_code == 401
    assert response.get_json() == {"error": "Not logged in"}


@patch("ecobud.app.logger")
def test_webhook_post(mock_logger):
    # Arrange
    test_client = app.test_client()
    request_data = {"key": "value"}

    # Act
    response = test_client.post("/tink/webhook", data=json.dumps(request_data), content_type="application/json")

    # Assert
    mock_logger.debug.assert_called_once_with("Got webhook {'key': 'value'}")
    assert response.status_code == 200
    assert response.get_json() == {"success": True}


@patch("ecobud.app.get_transactions")
def test_transactions_get_logged_in(mock_get_transactions):
    # Arrange
    test_client = app.test_client()
    with test_client.session_transaction() as sess:
        sess["username"] = "test_user"
    mock_get_transactions.return_value = [{"id": "1", "amount": 100}]

    # Act
    response = test_client.get("/transactions")

    # Assert
    mock_get_transactions.assert_called_once_with("test_user")
    assert response.status_code == 200
    assert response.get_json() == {"transactions": [{"id": "1", "amount": 100}]}


def test_transactions_get_not_logged_in():
    # Arrange
    test_client = app.test_client()

    # Act
    response = test_client.get("/transactions")

    # Assert
    assert response.status_code == 401
    assert response.get_json() == {"error": "Not logged in"}


@patch("ecobud.app.get_specific_transaction")
def test_transaction_get_logged_in(mock_get_specific_transaction):
    # Arrange
    test_client = app.test_client()
    with test_client.session_transaction() as sess:
        sess["username"] = "test_user"
    mock_get_specific_transaction.return_value = {"id": "1", "amount": 100}

    # Act
    response = test_client.get("/transactions/1")

    # Assert
    mock_get_specific_transaction.assert_called_once_with("test_user", "1")
    assert response.status_code == 200
    assert response.get_json() == {"transaction": {"id": "1", "amount": 100}}


def test_transaction_get_not_logged_in():
    # Arrange
    test_client = app.test_client()

    # Act
    response = test_client.get("/transactions/1")

    # Assert
    assert response.status_code == 401
    assert response.get_json() == {"error": "Not logged in"}


@patch("ecobud.app.update_transaction")
def test_transaction_put_success(mock_update_transaction):
    # Arrange
    test_client = app.test_client()
    with test_client.session_transaction() as sess:
        sess["username"] = "test_user"
    data = {"transaction": {"username": "test_user", "_id": "1"}}

    # Act
    with app.test_request_context("/transactions/1", method="PUT", json=data):
        response = test_client.put("/transactions/1", json=data)

    # Assert
    mock_update_transaction.assert_called_once_with(data["transaction"])
    assert response.status_code == 200
    assert response.get_json() == {"success": True}


@patch("ecobud.app.update_transaction")
def test_transaction_put_failure_other_user(mock_update_transaction):
    # Arrange
    test_client = app.test_client()
    with test_client.session_transaction() as sess:
        sess["username"] = "test_user"
    data = {"transaction": {"username": "other_user", "_id": "1"}}

    # Act
    with app.test_request_context("/transactions/1", method="PUT", json=data):
        response = test_client.put("/transactions/1", json=data)

    # Assert
    assert response.status_code == 401
    assert "error" in response.get_json()


@patch("ecobud.app.update_transaction")
def test_transaction_put_failure_not_logged_in(mock_update_transaction):
    # Arrange
    test_client = app.test_client()
    data = {"transaction": {"username": "test_user", "_id": "1"}}

    # Act
    with app.test_request_context("/transactions/1", method="PUT", json=data):
        response = test_client.put("/transactions/1", json=data)

    # Assert
    assert response.status_code == 401
    assert response.get_json() == {"error": "Not logged in"}


@patch("ecobud.app.update_transaction")
def test_transaction_put_mismatch_id(mock_update_transaction):
    # Arrange
    test_client = app.test_client()
    with test_client.session_transaction() as sess:
        sess["username"] = "test_user"
    data = {"transaction": {"username": "test_user", "_id": "id1"}}
    mock_update_transaction.return_value = None

    # Act
    with app.test_request_context("/transactions/id2", method="PUT", json=data):
        response = test_client.put("/transactions/id2", json=data)

    # Assert
    assert response.status_code == 401
    assert response.get_json() == {"error": "Wrong transaction id"}


@patch("ecobud.app.get_analytics")
@patch("ecobud.app.logger")
def test_analytics_get_logged_in(mock_logger, mock_get_analytics):
    # Arrange
    test_client = app.test_client()
    with test_client.session_transaction() as sess:
        sess["username"] = "test_user"
    mock_get_analytics.return_value = {"data": "analytics_data"}

    # Act
    response = test_client.get("/analytics/2022-01-01/2022-01-31")

    # Assert
    mock_get_analytics.assert_called_once_with("2022-01-01", "2022-01-31", "test_user")
    assert response.status_code == 200
    assert response.get_json() == {"analytics": {"data": "analytics_data"}}


def test_analytics_get_not_logged_in():
    # Arrange
    test_client = app.test_client()

    # Act
    response = test_client.get("/analytics/2022-01-01/2022-01-31")

    # Assert
    assert response.status_code == 401
    assert response.get_json() == {"error": "Not logged in"}


def test_logout_post_logged_in():
    # Arrange
    test_client = app.test_client()
    with test_client.session_transaction() as sess:
        sess["username"] = "test_user"

    # Act
    response = test_client.post("/logout")

    # Assert
    assert response.status_code == 200
    assert response.get_json() == {"success": True}
    with test_client.session_transaction() as sess:
        assert "username" not in sess


def test_logout_post_not_logged_in():
    # Arrange
    test_client = app.test_client()

    # Act
    response = test_client.post("/logout")

    # Assert
    assert response.status_code == 200
    assert response.get_json() == {"success": True}


@patch("ecobud.app.get_user_transactions")
def test_tink_transactions_get_logged_in(mock_get_user_transactions):
    # Arrange
    test_client = app.test_client()
    with test_client.session_transaction() as sess:
        sess["username"] = "test_user"
    mock_get_user_transactions.return_value = [{"id": "1", "amount": 100}]

    # Act
    response = test_client.get("/tink/transactions")

    # Assert
    mock_get_user_transactions.assert_called_once_with("test_user")
    assert response.status_code == 200
    assert response.get_json() == {"transactions": [{"id": "1", "amount": 100}]}


def test_tink_transactions_get_not_logged_in():
    # Arrange
    test_client = app.test_client()

    # Act
    response = test_client.get("/tink/transactions")

    # Assert
    assert response.status_code == 401
    assert response.get_json() == {"error": "Not logged in"}