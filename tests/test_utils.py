import unittest.mock as mock

from ecobud.utils import curl, fmt_response


def test_fmt_response_success():
    # Arrange
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"key": "value"}

    # Act
    result = fmt_response(mock_response)

    # Assert
    assert result == {"key": "value"}


def test_fmt_response_failure():
    # Arrange
    mock_response = mock.Mock()
    mock_response.status_code = 404
    mock_response.text = "Not Found"

    # Act
    result = fmt_response(mock_response)

    # Assert
    assert result == "<404>: Not Found"


from unittest.mock import Mock, patch

from ecobud.utils import curl


@patch("ecobud.utils.curlify.to_curl")
def test_curl(mock_to_curl):
    # Arrange
    mock_response = Mock()
    mock_to_curl.return_value = "curl 'http://example.com'"

    # Act
    result = curl(mock_response)

    # Assert
    mock_to_curl.assert_called_once_with(mock_response.request)
    assert result == "curl 'http://example.com'"
