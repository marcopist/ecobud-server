import unittest
from unittest.mock import MagicMock, patch

from ecobud.model.transactions import (
    Transaction,
    get_specific_transaction,
    get_transactions,
    update_transaction,
    TinkTransactionData,
    TransactionDescription,
    TransactionEcoData,
)

example_tink_payload = {
    "id": "1",
    "amount": {
        "value": {"unscaledValue": "100", "scale": "2"},
        "currencyCode": "USD",
    },
    "dates": {"booked": "2020-12-15"},
    "status": "BOOKED",
    "accountId": "123",
    "username": "test",
    "descriptions": {
        "detailed": {
            "unstructured": "test",
        },
        "display": "test",
        "original": "test",
    },
}

example_transaction_dict = {
    "username": "test",
    "id": "1",
    "amount": 1.0,
    "currency": "USD",
    "date": "2020-12-15",
    "description": {
        "detailed": "test",
        "display": "test",
        "original": "test",
        "user": "test",
    },
    "ecoData": {"oneOff": True},
    "tinkData": {"status": "BOOKED", "accountId": "123"},
}

example_transaction = Transaction(
    username="test",
    id="1",
    amount=1.0,
    currency="USD",
    date="2020-12-15",
    description=TransactionDescription(
        detailed="test", display="test", original="test", user="test"
    ),
    ecoData=TransactionEcoData(oneOff=True),
    tinkData=TinkTransactionData(
        status="BOOKED",
        accountId="123",
    ),
)


class TestTransaction(unittest.TestCase):
    def test_from_tink(self):
        transaction = Transaction.from_tink(
            "test", example_tink_payload
        )
        assert transaction == example_transaction

    def test_from_dict(self):
        transaction = Transaction.from_dict(example_transaction_dict)
        assert transaction == example_transaction

@patch("ecobud.model.transactions.Process")
@patch("ecobud.model.transactions.sync_transactions")
@patch("ecobud.model.transactions.transactionsdb")
def test_get_transactions(mock_transactionsdb, mock_sync_transactions, mock_process):
    mock_transactionsdb.find.return_value.sort.return_value.limit.return_value = [
        {"username": "test", "id": "1"},
        {"username": "test", "id": "2"},
    ]
    transactions = get_transactions("test")
    assert len(transactions) == 2
    assert transactions[0]["id"] == "1"
    assert transactions[1]["id"] == "2"



@patch("ecobud.model.transactions.transactionsdb")
def test_get_specific_transaction(
    mock_transactionsdb
):
    mock_transactionsdb.find_one.return_value = {
        "username": "test",
        "id": "1",
    }
    transaction = get_specific_transaction("test", "1")
    assert transaction["id"] == "1"
    assert transaction["username"] == "test"


@patch("ecobud.model.transactions.transactionsdb")
def test_update_transaction(mock_transactionsdb):
    resp = update_transaction(
        {
            "username": "test",
            "id": "1",
            "amount": 1.0,
            "currency": "USD",
            "date": "2020-12-15",
            "description": None,
            "ecoData": None,
            "tinkData": None,
        }
    )
    assert resp == True
    assert mock_transactionsdb.find_one_and_replace.called == True
    assert mock_transactionsdb.find_one_and_replace.call_args[0][0] == {
        "id": "1",
        "username": "test",
    }
    assert mock_transactionsdb.find_one_and_replace.call_args[0][1] == {
        "username": "test",
        "id": "1",
        "amount": 1.0,
        "currency": "USD",
        "date": "2020-12-15",
        "description": None,
        "ecoData": None,
        "tinkData": None,
    }
