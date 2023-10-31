import logging
from typing import Optional, Dict, Any, Tuple
from dataclasses import asdict, dataclass
from datetime import datetime
from multiprocessing import Process

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
    oneOff: bool
    startDate: str
    endDate: str
    dailyAmount: float

    @classmethod
    def set_default(
        cls,
        transactionDate,
        transactionAmount,
    ):
        return cls(
            oneOff=True,
            startDate=transactionDate,
            endDate=transactionDate,
            dailyAmount=transactionAmount,
        )


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
        detailed = descriptions.get("detailed", {}).get(
            "unstructured"
        )
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
    id: str
    amount: float
    currency: str
    date: str
    description: TransactionDescription
    ecoData: TransactionEcoData
    tinkData: TinkTransactionData
    ignore: bool = False

    @classmethod
    def from_tink(cls, username: str, payload: Dict[str, Any]) -> "Transaction":
        """Create a transaction from a Tink payload
            Example:

        {
          "accountId": "4a2945d1481c4f4b98ab1b135afd96c0",
          "amount": {
            "currencyCode": "GBP",
            "value": {
              "scale": "1",
              "unscaledValue": "-1300"
            }
          },
          "bookedDateTime": "2020-12-15T09:25:12Z",
          "categories": {
            "pfm": {
              "id": "d8f37f7d19c240abb4ef5d5dbebae4ef",
              "name": ""
            }
          },
          "counterparties": {
            "payee": {
              "identifiers": {
                "financialInstitution": {
                  "accountNumber": "SE6651152689155983335132"
                }
              },
              "name": "Joe Doe"
            },
            "payer": {
              "identifiers": {
                "financialInstitution": {
                  "accountNumber": "SE3778591419782047144807"
                }
              },
              "name": "Jane Doe"
            }
          },
          "dates": {
            "booked": "2020-12-15",
            "value": "2020-12-15"
          },
          "descriptions": {
            "detailed": {
              "unstructured": "PAYMENT *SUBSCRIPTION 123/987"
            },
            "display": "Tesco",
            "original": "TESCO STORES 3297"
          },
          "id": "d8f37f7d19c240abb4ef5d5dbebae4ef",
          "identifiers": {
            "providerTransactionId": "500015d3-acf3-48cc-9918-9e53738d3692"
          },
          "merchantInformation": {
            "merchantCategoryCode": "4111",
            "merchantName": "Local Transit Company"
          },
          "providerMutability": "MUTABILITY_UNDEFINED",
          "reference": "RF12310007894321",
          "status": "BOOKED",
          "transactionDateTime": "2020-12-14T18:31:54Z",
          "types": {
            "financialInstitutionTypeCode": "DEB",
            "type": "DEFAULT"
          },
          "valueDateTime": "2020-12-15T09:25:12Z"
        }

        """

        id_ = payload["id"]
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
        ecoData = TransactionEcoData.set_default(
            transactionDate,
            amount,
        )
        return cls(
            username=username,
            id=id_,
            amount=amount,
            currency=currency,
            date=transactionDate,
            description=description,
            ecoData=ecoData,
            tinkData=tinkData,
        )
    
    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "Transaction":
        return from_dict(data_class=cls, data=payload)
        


def sync_transactions(username: str, noPages:int =1) -> Dict[str, Any]:
    transactions = get_user_transactions(username, noPages=noPages)
    cnt = 0
    for transaction_dict in transactions:
        tinkTransaction = Transaction.from_tink(
            username, transaction_dict
        )
        existing = transactionsdb.find_one(
            {"id": tinkTransaction.id, "username": tinkTransaction.username},
        )

        if existing:
            existingTransaction = Transaction.from_dict(existing)
            existingTransaction.tinkData = tinkTransaction.tinkData


        else:
            transactionsdb.insert_one(asdict(tinkTransaction))
            
        cnt += 1
    return {"message": f"{cnt} transactions synced"}


def get_transactions(username: str) -> Dict[str, Any]:
    async_process = Process(
        target=sync_transactions,
        args=(username,),
        daemon=True,
    )
    async_process.start()

    transactions = list(
        transactionsdb.find({"username": username, "ignore": False})
        .sort("date", -1)
        .limit(100)
    )
    transnoid = [
        {k: v for k, v in t.items() if k != "_id"}
        for t in transactions
    ]
    return transnoid


def get_specific_transaction(username: str, transaction_id: str) -> Dict[str, Any]:
    logger.debug(
        f"Getting transaction {transaction_id} for {username}"
    )
    transaction = transactionsdb.find_one(
        {"username": username, "id": transaction_id}
    )
    transaction = {k: v for k, v in transaction.items() if k != "_id"}
    logging.debug(f"Got transaction {transaction}")
    return transaction


def update_transaction(transaction: Dict[str, Any]) -> bool:
    transactionsdb.find_one_and_replace(
        {
            "id": transaction["id"],
            "username": transaction["username"],
        },
        transaction,
        upsert=False,
    )
    logger.debug(
        f"Finished mongo interaction for transaction {transaction['id']}"
    )
    return True


if __name__ == "__main__":
    print(sync_transactions("test0"))
