import unittest
import unittest.mock as mock
from dataclasses import asdict
from datetime import datetime

import pytest

from ecobud.model.analytics import (
    AnalysedTransaction,
    Analytics,
    AnalyticsInputData,
    AnalyticsOutputData,
    get_analytics,
)
from ecobud.model.transactions import (
    TinkTransactionData,
    Transaction,
    TransactionDescription,
    TransactionEcoData,
)


@pytest.mark.parametrize(
    "start_date, end_date, expected_days",
    [
        ("2022-01-01", "2022-01-31", 31),
        ("2022-02-01", "2022-02-28", 28),
        ("2022-03-01", "2022-03-31", 31),
    ],
)
def test_days_in_period(start_date, end_date, expected_days):
    transaction = Transaction(
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
        ecoData=TransactionEcoData(startDate=start_date, endDate=end_date),
        tinkData=TinkTransactionData(status="BOOKED", accountId="abc123"),
        ignore=False,
    )
    inputData = AnalyticsInputData(startDate="2022-01-01", endDate="2022-01-31", username="test_user")
    analysedTransaction = AnalysedTransaction(transaction=transaction, inputData=inputData)

    assert analysedTransaction.days_in_period() == expected_days


@pytest.mark.parametrize(
    "transaction_date, one_off, expected_cost",
    [
        ("2022-01-15", True, 10.0),
        ("2022-02-15", True, 0),
        ("2022-01-01", False, 10 / 31 * 15),  # Overlapping 15 days of 31 day period
    ],
)
def test_get_cost_in_analytics_period(transaction_date, one_off, expected_cost):
    transaction = Transaction(
        username="test_user",
        _id="123",
        amount=10.0,
        currency="USD",
        date=transaction_date,
        description=TransactionDescription(
            detailed="PAYMENT *SUBSCRIPTION 123/987",
            display="Tesco",
            original="TESCO STORES 3297",
            user="Tesco",
        ),
        ecoData=TransactionEcoData(startDate="2022-01-01", endDate="2022-01-31", oneOff=one_off),
        tinkData=TinkTransactionData(status="BOOKED", accountId="abc123"),
        ignore=False,
    )
    inputData = AnalyticsInputData(startDate="2022-01-01", endDate="2022-01-15", username="test_user")
    analysedTransaction = AnalysedTransaction(transaction=transaction, inputData=inputData)

    assert analysedTransaction.get_cost_in_analytics_period() == expected_cost


@pytest.mark.parametrize(
    "username, start_date, end_date, transactions",
    [
        (
            "test_user",
            "2022-01-01",
            "2022-01-15",
            [
                AnalysedTransaction(
                    transaction=Transaction(
                        _id="123",
                        username="test_user",
                        amount=10.0,
                        currency="USD",
                        date="2022-01-01",
                        description=TransactionDescription(
                            detailed="PAYMENT *SUBSCRIPTION 123/987",
                            display="Tesco",
                            original="TESCO STORES 3297",
                            user="Tesco",
                        ),
                        ecoData=TransactionEcoData(startDate="2022-01-01", endDate="2022-01-31", oneOff=False),
                        tinkData=TinkTransactionData(status="BOOKED", accountId="abc123"),
                        ignore=False,
                    ),
                    inputData=AnalyticsInputData(username="test_user", startDate="2022-01-01", endDate="2022-01-15"),
                ),
            ],
        ),
    ],
)
@mock.patch("ecobud.model.analytics.transactionsdb.find")
def test_get_transactions_in_period(mock_find, username, start_date, end_date, transactions):
    # Arrange
    mock_find.return_value = []
    analytics = Analytics(inputData=AnalyticsInputData(username=username, startDate=start_date, endDate=end_date))
    analytics.outputData.transactions = transactions

    # Assert
    assert analytics.outputData.transactions == transactions


@pytest.mark.parametrize(
    "username, start_date, end_date, transactions, expected_cost",
    [
        (
            "test_user",
            "2022-01-01",
            "2022-01-15",
            [
                AnalysedTransaction(
                    transaction=Transaction(
                        _id="123",
                        username="test_user",
                        amount=10.0,
                        currency="USD",
                        date="2022-01-01",
                        description=TransactionDescription(
                            detailed="PAYMENT *SUBSCRIPTION 123/987",
                            display="Tesco",
                            original="TESCO STORES 3297",
                            user="Tesco",
                        ),
                        ecoData=TransactionEcoData(startDate="2022-01-01", endDate="2022-01-31", oneOff=False),
                        tinkData=TinkTransactionData(status="BOOKED", accountId="abc123"),
                        ignore=False,
                    ),
                    inputData=AnalyticsInputData(username="test_user", startDate="2022-01-01", endDate="2022-01-15"),
                ),
            ],
            10 / 31 * 15,
        ),
    ],
)
@mock.patch("ecobud.model.analytics.transactionsdb.find")
def test_get_cost_in_period(mock_find, username, start_date, end_date, transactions, expected_cost):
    # Arrange
    mock_find.return_value = []
    analytics = Analytics(inputData=AnalyticsInputData(username=username, startDate=start_date, endDate=end_date))
    analytics.outputData.transactions = transactions

    # Act
    actual_cost = analytics.get_cost_in_period()

    # Assert
    assert actual_cost == expected_cost


@pytest.mark.parametrize(
    "start_date, end_date, username",
    [
        ("2022-01-01", "2022-01-31", "test_user"),
        ("2022-02-01", "2022-02-28", "test_user"),
        ("2022-03-01", "2022-03-31", "test_user"),
    ],
)
@mock.patch("ecobud.model.analytics.Analytics")
def test_get_analytics(mock_Analytics, start_date, end_date, username):
    # Arrange
    transactions = [
        Transaction(
            _id="123",
            username=username,
            amount=10.0,
            currency="USD",
            date="2022-01-01",
            description=TransactionDescription(
                detailed="PAYMENT *SUBSCRIPTION 123/987",
                display="Tesco",
                original="TESCO STORES 3297",
                user="Tesco",
            ),
            ecoData=TransactionEcoData(startDate="2022-01-01", endDate="2022-01-31", oneOff=False),
            tinkData=TinkTransactionData(status="BOOKED", accountId="abc123"),
            ignore=False,
        ),
        # Add more transactions as needed
    ]
    expected_output_data = AnalyticsOutputData(periodCost=10.0, transactions=transactions)
    mock_Analytics.return_value.outputData = expected_output_data

    # Act
    actual_output_data = get_analytics(start_date, end_date, username)

    # Assert
    mock_Analytics.assert_called_once_with(
        AnalyticsInputData(username=username, startDate=start_date, endDate=end_date)
    )
    assert actual_output_data == asdict(expected_output_data)
