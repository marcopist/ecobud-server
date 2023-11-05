import unittest
from unittest.mock import MagicMock, patch

import pytest

from ecobud.model.transactions import (
    TinkTransactionData,
    Transaction,
    TransactionDescription,
    TransactionEcoData,
    get_specific_transaction,
    get_transactions,
    sync_transactions,
    update_transaction,
)


class TestTransactionDescription(unittest.TestCase):
    def test_from_tink(self):
        tink_payload = {
            "descriptions": {
                "detailed": {"unstructured": "PAYMENT *SUBSCRIPTION 123/987"},
                "display": "Tesco",
                "original": "TESCO STORES 3297",
            }
        }

        expected_transaction_description = TransactionDescription(
            detailed="PAYMENT *SUBSCRIPTION 123/987",
            display="Tesco",
            original="TESCO STORES 3297",
            user="Tesco",
        )

        actual_transaction_description = TransactionDescription.from_tink(tink_payload)

        self.assertEqual(actual_transaction_description, expected_transaction_description)


class TestTransaction(unittest.TestCase):
    def test_from_tink(self):
        tink_payload = {
            "id": "123",
            "amount": {"value": {"unscaledValue": 1000, "scale": 2}, "currencyCode": "USD"},
            "dates": {"booked": "2022-01-01"},
            "status": "BOOKED",
            "accountId": "abc123",
            "descriptions": {
                "detailed": {"unstructured": "PAYMENT *SUBSCRIPTION 123/987"},
                "display": "Tesco",
                "original": "TESCO STORES 3297",
            },
        }

        expected_transaction = Transaction(
            username="test_user",
            _id="123",
            amount=10.0,
            currency="USD",
            date="2022-01-01",
            description=TransactionDescription.from_tink(tink_payload),
            ecoData=TransactionEcoData(),
            tinkData=TinkTransactionData(status="BOOKED", accountId="abc123"),
        )

        actual_transaction = Transaction.from_tink("test_user", tink_payload)

        self.assertEqual(actual_transaction, expected_transaction)

    def test_from_dict(self):
        transaction_dict = {
            "username": "test_user",
            "_id": "123",
            "amount": 10.0,
            "currency": "USD",
            "date": "2022-01-01",
            "description": {
                "detailed": "PAYMENT *SUBSCRIPTION 123/987",
                "display": "Tesco",
                "original": "TESCO STORES 3297",
                "user": "Tesco",
            },
            "ecoData": {},
            "tinkData": {"status": "BOOKED", "accountId": "abc123"},
            "ignore": False,
        }

        expected_transaction = Transaction(
            username="test_user",
            _id="123",
            amount=10.0,
            currency="USD",
            date="2022-01-01",
            description=TransactionDescription(
                detailed="PAYMENT *SUBSCRIPTION 123/987",
                display="Tesco",
                original="TESCO STORES 3297",
                user="Tesco",
            ),
            ecoData=TransactionEcoData(),
            tinkData=TinkTransactionData(status="BOOKED", accountId="abc123"),
            ignore=False,
        )

        actual_transaction = Transaction.from_dict(transaction_dict)

        self.assertEqual(actual_transaction, expected_transaction)


@pytest.mark.parametrize("transaction_exists_in_db", [True, False])
@patch("ecobud.model.transactions.get_user_transactions")
@patch("ecobud.model.transactions.transactionsdb")
def test_sync_transactions(mock_transactionsdb, mock_get_user_transactions, transaction_exists_in_db):
    # Arrange
    username = "test_user"
    noPages = 1
    mock_get_user_transactions.return_value = [
        {
            "id": "123",
            "username": username,
            "amount": {"value": {"unscaledValue": 1000, "scale": 2}, "currencyCode": "USD"},
            "dates": {"booked": "2022-01-01"},
            "status": "BOOKED",
            "accountId": "abc123",
            "descriptions": {
                "detailed": {"unstructured": "PAYMENT *SUBSCRIPTION 123/987"},
                "display": "Tesco",
                "original": "TESCO STORES 3297",
            },
        }
    ]

    existing = {
        "_id": "123",
        "username": username,
        "amount": 10.0,
        "currency": "USD",
        "date": "2022-01-01",
        "description": {
            "detailed": "PAYMENT *SUBSCRIPTION 123/987",
            "display": "Tesco",
            "original": "TESCO STORES 3297",
            "user": "Tesco",
        },
        "ecoData": {},
        "tinkData": {"status": "BOOKED", "accountId": "abc123"},
        "ignore": False,
    }

    mock_transactionsdb.find_one.return_value = existing if transaction_exists_in_db else None

    # Act
    result = sync_transactions(username, noPages)

    # Assert
    assert result
    mock_get_user_transactions.assert_called_once_with(username, noPages=noPages)
    mock_transactionsdb.find_one.assert_called_once()
    if transaction_exists_in_db:
        mock_transactionsdb.find_one_and_replace.assert_called_once()
    else:
        mock_transactionsdb.insert_one.assert_called_once()


@patch("ecobud.model.transactions.Process")
@patch("ecobud.model.transactions.transactionsdb")
def test_get_transactions(mock_transactionsdb, mock_process):
    # Arrange
    username = "test_user"
    mock_transactionsdb.find.return_value.sort.return_value.limit.return_value = [
        {
            "_id": "123",
            "username": username,
            "amount": 10.0,
            "currency": "USD",
            "date": "2022-01-01",
            "description": {
                "detailed": "PAYMENT *SUBSCRIPTION 123/987",
                "display": "Tesco",
                "original": "TESCO STORES 3297",
                "user": "Tesco",
            },
            "ecoData": {},
            "tinkData": {"status": "BOOKED", "accountId": "abc123"},
            "ignore": False,
        }
    ]

    # Act
    result = get_transactions(username)

    # Assert
    mock_process.assert_called_once_with(
        target=sync_transactions,
        args=(username,),
        daemon=True,
    )
    mock_process.return_value.start.assert_called_once()
    mock_transactionsdb.find.assert_called_once_with({"username": username, "ignore": False})
    assert result == mock_transactionsdb.find.return_value.sort.return_value.limit.return_value


@patch("ecobud.model.transactions.transactionsdb")
def test_get_specific_transaction(mock_transactionsdb):
    # Arrange
    username = "test_user"
    _id = "123"
    expected_transaction = {
        "_id": _id,
        "username": username,
        "amount": 10.0,
        "currency": "USD",
        "date": "2022-01-01",
        "description": {
            "detailed": "PAYMENT *SUBSCRIPTION 123/987",
            "display": "Tesco",
            "original": "TESCO STORES 3297",
            "user": "Tesco",
        },
        "ecoData": {},
        "tinkData": {"status": "BOOKED", "accountId": "abc123"},
        "ignore": False,
    }
    mock_transactionsdb.find_one.return_value = expected_transaction

    # Act
    actual_transaction = get_specific_transaction(username, _id)

    # Assert
    mock_transactionsdb.find_one.assert_called_once_with({"username": username, "_id": _id})
    assert actual_transaction == expected_transaction


@patch("ecobud.model.transactions.transactionsdb")
def test_update_transaction_success(mock_transactionsdb):
    # Arrange
    transaction = {
        "_id": "123",
        "username": "test_user",
        "amount": 10.0,
        "currency": "USD",
        "date": "2022-01-01",
        "description": {
            "detailed": "PAYMENT *SUBSCRIPTION 123/987",
            "display": "Tesco",
            "original": "TESCO STORES 3297",
            "user": "Tesco",
        },
        "ecoData": {},
        "tinkData": {"status": "BOOKED", "accountId": "abc123"},
        "ignore": False,
    }

    # Act
    result = update_transaction(transaction)

    # Assert
    mock_transactionsdb.find_one_and_replace.assert_called_once_with(
        {
            "_id": transaction["_id"],
            "username": transaction["username"],
        },
        transaction,
        upsert=False,
    )
    assert result is True
