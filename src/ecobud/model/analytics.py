import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Iterable, Optional

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


class AnalysedTransaction(Transaction):
    """A transaction with additional analytics data"""

    def __init__(
        self, transaction: Transaction, input_data: AnalyticsInputData
    ):
        super().__init__(**transaction.__dict__)
        self.inputData = input_data
        self.outputData = TransactionAnalyticsOutputData()
        self.outputData.periodCost = (
            self.get_cost_in_analytics_period()
        )

    def days_in_period(self) -> float:
        start = datetime.fromisoformat(self.ecoData.startDate)
        end = datetime.fromisoformat(self.ecoData.endDate)
        return (end - start).days + 1

    def get_cost_in_analytics_period(
        self,
    ) -> float:
        analyticsStartDate = datetime.fromisoformat(
            self.inputData.startDate
        )
        analyticsEndDate = datetime.fromisoformat(
            self.inputData.endDate
        )
        datetimeTransactionDate = datetime.fromisoformat(self.date)

        if self.ecoData.oneOff:
            if (
                analyticsStartDate
                <= datetimeTransactionDate
                <= analyticsEndDate
            ):
                return self.amount
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
            return (
                self.amount * overlappingDays / self.days_in_period()
            )


class Analytics:
    def __init__(self, inputData: AnalyticsInputData):
        self.inputData = inputData
        self.outputData = AnalyticsOutputData()
        self.outputData.transactions = (
            self.get_transactions_in_period()
        )

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
                            "ecoData.startDate": {
                                "$lte": self.inputData.endDate
                            },
                            "ecoData.endDate": {
                                "$gte": self.inputData.startDate
                            },
                        },
                    ]
                },
            ]
        }

        return map(
            AnalysedTransaction.from_dict, transactionsdb.find(query)
        )

    def get_cost_in_period(self) -> float:
        """Get total cost of transactions"""
        return sum(
            transaction.outputData.periodCost
            for transaction in self.outputData.transactions
        )


if __name__ == "__main__":
    inputData = AnalyticsInputData(
        username="test0",
        startDate="2023-10-01",
        endDate="2023-10-31",
    )
    analytics = Analytics(inputData)
    print(list(analytics.outputData.transactions))
