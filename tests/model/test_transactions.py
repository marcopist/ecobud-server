import unittest
from unittest.mock import patch, MagicMock
import pytest
from ecobud.model.transactions import (
    Transaction,
    TransactionDescription,
    TransactionEcoData,
    TinkTransactionData,
    sync_transactions,
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
