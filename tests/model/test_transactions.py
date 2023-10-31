import unittest
from unittest.mock import patch, MagicMock
from ecobud.model.transactions import Transaction

class TestTransaction(unittest.TestCase):
    def setUp(self):
        self.tink_payload = {
            "id": "1",
            "amount": {"value": {"unscaledValue": "100", "scale": "2"}, "currencyCode": "USD"},
            "dates": {"booked": "2020-12-15"},
            "status": "BOOKED",
            "accountId": "123",
            "username": "test"
        }

        self.dict_payload = {
            "username": "test",
            "id": "1",
            "amount": 1.0,
            "currency": "USD",
            "date": "2020-12-15",
            "description": None,
            "ecoData": None,
            "tinkData": None
        }

        self.transaction = Transaction(
            username="test",
            id="1",
            amount=1.0,
            currency="USD",
            date="2020-12-15",
            description=None,
            ecoData=None,
            tinkData=None
        )

    def test_from_tink(self):
        transaction = Transaction.from_tink("test", self.tink_payload)
        self.assertEqual(transaction.username, "test")
        self.assertEqual(transaction.id, "1")
        self.assertEqual(transaction.amount, 1.0)
        self.assertEqual(transaction.currency, "USD")
        self.assertEqual(transaction.date, "2020-12-15")

    def test_from_dict(self):
        transaction = Transaction.from_dict(self.dict_payload)
        self.assertEqual(transaction.username, "test")
        self.assertEqual(transaction.id, "1")
        self.assertEqual(transaction.amount, 1.0)
        self.assertEqual(transaction.currency, "USD")
        self.assertEqual(transaction.date, "2020-12-15")
