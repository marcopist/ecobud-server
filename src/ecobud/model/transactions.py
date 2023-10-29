from dataclasses import dataclass, asdict
from datetime import datetime

from ecobud.connections.mongo import collections
from ecobud.connections.tink import get_user_transactions

transactionsdb = collections["transactions"]

from pprint import pprint

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
            oneOff=False,
            startDate=transactionDate,
            endDate=transactionDate,
            dailyAmount=transactionAmount,
        )


@dataclass
class TransactionDescription:
    detailed: str
    display: str
    original: str

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

        return cls(
            detailed=detailed,
            display=display,
            original=original,
        )


@dataclass
class Transaction:
    user: str
    id: str
    amount: float
    currency: str
    date: str
    description: TransactionDescription
    ecoData: TransactionEcoData

    @classmethod
    def from_tink(cls, user, payload):
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

        description = TransactionDescription.from_tink(
            payload
        )
        ecoData = TransactionEcoData.set_default(
            transactionDate,
            amount,
        )
        return cls(
            user=user,
            id=id_,
            amount=amount,
            currency=currency,
            date=transactionDate,
            description=description,
            ecoData=ecoData,
        )


def sync_transactions(username, noPages=1):
    transactions = get_user_transactions(username, noPages=noPages)
    cnt = 0
    for transaction_dict in transactions:
        transaction = Transaction.from_tink(
            username, transaction_dict
        )
        transactionsdb.find_one_and_replace(
            {"id": transaction.id, "username": transaction.user},
            asdict(transaction),
            upsert=True,
        )

        cnt += 1
    return {"message": f"{cnt} transactions synced"}, 200

def get_transactions(username):
    transactions = list(transactionsdb.find({"user": username}).sort("date", -1).limit(100))
    transnoid = [{k:v for k, v in t.items() if k != "_id"} for t in transactions]
    return transnoid

if __name__ == "__main__":
    print(sync_transactions("test0"))
