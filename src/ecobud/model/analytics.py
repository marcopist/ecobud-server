from ecobud.connections.mongo import collections
import logging
from typing import Iterable, Optional
import datetime

from ecobud.model.transactions import (
    transactionsdb,
    Transaction,
)


logger = logging.getLogger(__name__)


def get_transactions_effective_on_date(
    date: str, username: str
) -> Iterable[Transaction]:
    """Get all transactions effective on a given date"""
    query = {
        "$and": [
            {
                "username": username,
            },
            {
                "$or": [
                    {"ecoData.oneOff": True, "date": date},
                    {
                        "ecoData.oneOff": False,
                        "ecoData.startDate": {"$lte": date},
                        "ecoData.endDate": {"$gte": date},
                    },
                ]
            },
        ]
    }

    return map(Transaction.from_dict, transactionsdb.find(query))


def get_transactions_effective_between_dates(
    start_date: str, end_date: str, username: str
) -> Iterable[Transaction]:
    """Get all transactions effective between two dates"""
    query = {
        "$and": [
            {
                "username": username,
            },
            {
                "$or": [
                    {
                        "ecoData.oneOff": True,
                        "date": {
                            "$gte": start_date,
                            "$lte": end_date,
                        },
                    },
                    {
                        "ecoData.oneOff": False,
                        "ecoData.startDate": {"$lte": end_date},
                        "ecoData.endDate": {"$gte": start_date},
                    },
                ]
            },
        ]
    }

    return map(Transaction.from_dict, transactionsdb.find(query))


def get_total_cost_of_transactions_effective_between_dates(
    start_date: str, end_date: str, username: str
) -> float:
    transactions = get_transactions_effective_between_dates(
        start_date, end_date, username
    )

    return sum(
        transaction.get_cost_in_period(
            datetime.fromisoformat(start_date),
            datetime.fromisoformat(end_date),
        )
        for transaction in transactions
    )


def get_total_cost(transactions: Iterable[Transaction]) -> float:
    """Get total cost of transactions"""
    return sum(
        transaction.daily_cost() for transaction in transactions
    )
