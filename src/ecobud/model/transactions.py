import logging
from dataclasses import asdict, dataclass
from multiprocessing import Process
from typing import Any, Dict, Optional

from dacite import from_dict

from ecobud.connections.mongo import collections
from ecobud.connections.tink import get_user_transactions

transactionsdb = collections["transactions"]

logger = logging.getLogger(__name__)


@dataclass
class TinkTransactionData:
    status: str
    accountId: str


@dataclass
class TransactionEcoData:
    oneOff: bool = True
    startDate: Optional[str] = None
    endDate: Optional[str] = None


@dataclass
class TransactionDescription:
    detailed: Optional[str]
    display: Optional[str]
    original: Optional[str]
    user: Optional[str]

    @classmethod
    def from_tink(cls, payload):
        """Create a transaction description from a Tink payload
            Example:

        {
          "detailed": {
            "unstructured": "PAYMENT *SUBSCRIPTION 123/987"
          },
          "display": "Tesco",
          "original": "TESCO STORES 3297"
        }

        """
        descriptions = payload["descriptions"]
        detailed = descriptions.get("detailed", {}).get("unstructured")
        display = descriptions.get("display")
        original = descriptions.get("original")
        user = display

        return cls(
            detailed=detailed,
            display=display,
            original=original,
            user=user,
        )


@dataclass
class Transaction:
    username: str
    _id: str
    amount: float
    currency: str
    date: str
    description: TransactionDescription
    ecoData: TransactionEcoData
    tinkData: TinkTransactionData
    ignore: bool = False

    @classmethod
    def from_tink(
        cls,
        username: str,
        payload: Dict[str, Any],
    ) -> "Transaction":
        """Create a transaction from a Tink payload"""

        _id = payload["id"]
        unscaledValue = payload["amount"]["value"]["unscaledValue"]
        scale = payload["amount"]["value"]["scale"]
        amount = float(unscaledValue) / (10 ** int(scale))
        currency = payload["amount"]["currencyCode"]
        transactionDate = payload["dates"]["booked"]

        tinkData = TinkTransactionData(
            status=payload["status"],
            accountId=payload["accountId"],
        )

        description = TransactionDescription.from_tink(payload)
        ecoData = TransactionEcoData()

        return cls(
            username=username,
            _id=_id,
            amount=amount,
            currency=currency,
            date=transactionDate,
            description=description,
            ecoData=ecoData,
            tinkData=tinkData,
        )

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "Transaction":
        return from_dict(data_class=Transaction, data=payload)


def sync_transactions(
    username: str,
    noPages: int = 1,
) -> Dict[str, Any]:
    transactions = get_user_transactions(username, noPages=noPages)
    for transaction_dict in transactions:
        tinkTransaction = Transaction.from_tink(username, transaction_dict)
        existing = transactionsdb.find_one(
            {
                "_id": tinkTransaction._id,
                "username": tinkTransaction.username,
            },
        )

        if existing:
            existingTransaction = Transaction.from_dict(existing)
            existingTransaction.tinkData = tinkTransaction.tinkData
            transactionsdb.find_one_and_replace(
                {
                    "_id": tinkTransaction._id,
                    "username": tinkTransaction.username,
                },
                asdict(existingTransaction),
                upsert=False,
            )

        else:
            transactionsdb.insert_one(asdict(tinkTransaction))

    return True


def get_transactions(username: str) -> Dict[str, Any]:
    async_process = Process(
        target=sync_transactions,
        args=(username,),
        daemon=True,
    )
    async_process.start()

    transactions = list(transactionsdb.find({"username": username, "ignore": False}).sort("date", -1).limit(100))
    return transactions

def get_specific_transaction(username: str, _id: str) -> Dict[str, Any]:
    logger.debug(f"Getting transaction {_id} for {username}")
    transaction = transactionsdb.find_one({"username": username, "_id": _id})
    logging.debug(f"Got transaction {transaction}")
    return transaction


def update_transaction(transaction: Dict[str, Any]) -> bool:
    transactionsdb.find_one_and_replace(
        {
            "_id": transaction["_id"],
            "username": transaction["username"],
        },
        transaction,
        upsert=False,
    )
    logger.debug(f"Finished mongo interaction for transaction {transaction['_id']}")
    return True


if __name__ == "__main__":
    print(sync_transactions("test0"))
