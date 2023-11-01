import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, Optional, Tuple

from ecobud.model.transactions import Transaction, transactionsdb

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsInputData:
    """Data used as input for analytics"""

    username: str
    startDate: str
    endDate: str


@dataclass
class AnalyticsOutputData:
    transactions: Optional[Iterable[Transaction]] = None
    periodCost: Optional[float] = None


@dataclass
class TransactionAnalyticsOutputData:
    """Data used as output for analytics"""

    periodCost: Optional[float] = None


@dataclass
class AnalysedTransaction:
    """A transaction with additional analytics data"""

    transaction: Transaction
    inputData: AnalyticsInputData
    outputData: Optional[TransactionAnalyticsOutputData] = None

    def __post_init__(self):
        self.outputData = TransactionAnalyticsOutputData()
        self.outputData.periodCost = self.get_cost_in_analytics_period()

    def days_in_period(self) -> float:
        start = datetime.fromisoformat(self.transaction.ecoData.startDate)
        end = datetime.fromisoformat(self.transaction.ecoData.endDate)
        return (end - start).days + 1

    def get_cost_in_analytics_period(
        self,
    ) -> float:
        analyticsStartDate = datetime.fromisoformat(self.inputData.startDate)
        analyticsEndDate = datetime.fromisoformat(self.inputData.endDate)
        datetimeTransactionDate = datetime.fromisoformat(self.transaction.date)

        if self.transaction.ecoData.oneOff:
            if analyticsStartDate <= datetimeTransactionDate <= analyticsEndDate:
                return self.transaction.amount
            else:
                return 0
        else:
            overlappingDays = (
                max(
                    0,
                    (
                        min(analyticsEndDate, datetimeTransactionDate)
                        - max(
                            analyticsStartDate,
                            datetimeTransactionDate,
                        )
                    ).days,
                )
                + 1
            )
            return self.transaction.amount * overlappingDays / self.days_in_period()


@dataclass
class Analytics:
    inputData: AnalyticsInputData
    outputData: Optional[AnalyticsOutputData] = None

    def __post_init__(self):
        self.outputData = AnalyticsOutputData()
        self.outputData.transactions = list(self.get_transactions_in_period())
        self.outputData.periodCost = self.get_cost_in_period()

    def get_transactions_in_period(self) -> Iterable[Transaction]:
        """Get all transactions effective between two dates"""
        query = {
            "$and": [
                {
                    "username": self.inputData.username,
                },
                {
                    "$or": [
                        {
                            "ecoData.oneOff": True,
                            "date": {
                                "$gte": self.inputData.startDate,
                                "$lte": self.inputData.endDate,
                            },
                        },
                        {
                            "ecoData.oneOff": False,
                            "ecoData.startDate": {"$lte": self.inputData.endDate},
                            "ecoData.endDate": {"$gte": self.inputData.startDate},
                        },
                    ]
                },
            ]
        }

        result = list(transactionsdb.find(query))

        return map(
            lambda trans: AnalysedTransaction(Transaction.from_dict(trans), self.inputData),
            result,
        )

    def get_cost_in_period(self) -> float:
        """Get total cost of transactions"""
        return sum(transaction.outputData.periodCost for transaction in self.outputData.transactions)


def get_analytics(startDate, endDate, username):
    logger.debug(
        "The get_analytics function was called with: startDate: {}, endDate: {}, username: {}".format(
            startDate, endDate, username
        )
    )
    inputData = AnalyticsInputData(
        username=username,
        startDate=startDate,
        endDate=endDate,
    )
    analytics = Analytics(inputData)
    return asdict(analytics.outputData)


if __name__ == "__main__":
    print(
        get_analytics(
            "2023-10-02",
            "2023-10-31",
            "test0",
        )
    )
