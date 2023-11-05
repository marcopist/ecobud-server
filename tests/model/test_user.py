import unittest
from unittest.mock import MagicMock, patch

import pytest

from ecobud.model.user import (
    TinkUserAlreadyExists,
    UserAlreadyExists,
    UserNotFound,
    WrongPassword,
    _get_user,
    create_user,
    login_user,
)


@patch("ecobud.model.user.usersdb")
@patch("ecobud.model.user.tink")
@patch("ecobud.model.user.bcrypt")
@patch("ecobud.model.user._get_user")
@patch("ecobud.model.user.tink.create_user")
def test_create_user_success(mock_create_user, mock_get_user, mock_bcrypt, mock_tink, mock_usersdb):
    # Arrange
    username = "test_user"
    email = "test_user@example.com"
    password = "password"
    mock_get_user.side_effect = UserNotFound
    mock_tink.create_user.return_value = "tink_user_id"
    mock_bcrypt.gensalt.return_value = b"salt"
    mock_bcrypt.hashpw.return_value = b"encrypted_password"

    # Act
    result = create_user(username, email, password)

    # Assert
    mock_get_user.assert_called_once_with(username)
    mock_tink.create_user.assert_called_once_with(username)
    mock_bcrypt.gensalt.assert_called_once()
    mock_bcrypt.hashpw.assert_called_once_with(password.encode("utf-8"), b"salt")
    mock_usersdb.insert_one.assert_called_once_with(
        {
            "username": username,
            "email": email,
            "password": "encrypted_password",
            "tink_user_id": "tink_user_id",
            "credentials": [],
        }
    )
    assert result is True


@patch("ecobud.model.user.usersdb")
@patch("ecobud.model.user._get_user")
def test_create_user_failure_user_exists(mock_get_user, mock_usersdb):
    # Arrange
    username = "test_user"
    email = "test_user@example.com"
    password = "password"
    mock_get_user.return_value = {"username": username, "email": email, "password": password}

    # Act & Assert
    with pytest.raises(UserAlreadyExists) as exc_info:
        create_user(username, email, password)
    assert str(exc_info.value) == f"User {username} already exists"


@patch("ecobud.model.user.usersdb")
@patch("ecobud.model.user._get_user")
@patch("ecobud.model.user.tink.create_user")
@patch("ecobud.model.user.tink.get_user")
@patch("ecobud.model.user.bcrypt.gensalt")
@patch("ecobud.model.user.bcrypt.hashpw")
def test_create_user_failure_tink_user_exists(
    mock_hashpw, mock_gensalt, mock_get_user_tink, mock_create_user_tink, mock_get_user, mock_usersdb
):
    # Arrange
    username = "test_user"
    email = "test_user@example.com"
    password = "password"
    mock_get_user.side_effect = UserNotFound
    mock_create_user_tink.side_effect = TinkUserAlreadyExists
    mock_get_user_tink.return_value = {"id": "tink_user_id"}
    mock_gensalt.return_value = b"salt"
    mock_hashpw.return_value = b"encrypted_password"

    # Act
    result = create_user(username, email, password)

    # Assert
    mock_get_user.assert_called_once_with(username)
    mock_create_user_tink.assert_called_once_with(username)
    mock_get_user_tink.assert_called_once_with(username)
    mock_gensalt.assert_called_once()
    mock_hashpw.assert_called_once_with(password.encode("utf-8"), b"salt")
    mock_usersdb.insert_one.assert_called_once_with(
        {
            "username": username,
            "email": email,
            "password": "encrypted_password",
            "tink_user_id": "tink_user_id",
            "credentials": [],
        }
    )
    assert result is True


@patch("ecobud.model.user._get_user")
@patch("ecobud.model.user.bcrypt.checkpw")
def test_login_user_success(mock_checkpw, mock_get_user):
    # Arrange
    username = "test_user"
    password = "password"
    mock_get_user.return_value = {"username": username, "password": password}
    mock_checkpw.return_value = True

    # Act
    result = login_user(username, password)

    # Assert
    mock_get_user.assert_called_once_with(username)
    mock_checkpw.assert_called_once_with(password.encode("utf-8"), password.encode("utf-8"))
    assert result is True


@patch("ecobud.model.user._get_user")
@patch("ecobud.model.user.bcrypt.checkpw")
def test_login_user_failure_wrong_password(mock_checkpw, mock_get_user):
    # Arrange
    username = "test_user"
    password = "password"
    mock_get_user.return_value = {"username": username, "password": password}
    mock_checkpw.return_value = False

    # Act & Assert
    with pytest.raises(WrongPassword) as exc_info:
        login_user(username, password)
    assert str(exc_info.value) == f"Wrong password for user {username}"


@patch("ecobud.model.user._get_user")
def test_login_user_failure_user_not_found(mock_get_user):
    # Arrange
    username = "test_user"
    password = "password"
    mock_get_user.side_effect = UserNotFound

    # Act & Assert
    with pytest.raises(UserNotFound):
        login_user(username, password)


@patch("ecobud.model.user.usersdb.find_one")
def test_get_user_success(mock_find_one):
    # Arrange
    username = "test_user"
    mock_find_one.return_value = {"username": username}

    # Act
    result = _get_user(username)

    # Assert
    mock_find_one.assert_called_once_with({"username": username})
    assert result == {"username": username}


@patch("ecobud.model.user.usersdb.find_one")
def test_get_user_failure_user_not_found(mock_find_one):
    # Arrange
    username = "test_user"
    mock_find_one.return_value = None

    # Act & Assert
    with pytest.raises(UserNotFound) as exc_info:
        _get_user(username)
    assert str(exc_info.value) == f"User {username} not found"
