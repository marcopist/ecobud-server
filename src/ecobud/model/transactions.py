from ecobud.connections.mongo import collections
from ecobud.connections.tink import get_user_transactions
from dataclasses import dataclass

transactionsdb = collections["transactions"]

@dataclass
class Transaction:
    pass

def sync_transactions(username, noPages=1):
    transactions = get_user_transactions(username, noPages=noPages)
    cnt = 0
    for transaction in transactions:

        transaction["username"] = username
        transactionsdb.find_one_and_replace(
            {"id": transaction["id"], "username": username},
            transaction,
            upsert=True,
        )
        cnt+=1
    return {"message": f"{cnt} transactions synced"}, 200

if __name__ == "__main__":
    print(sync_transactions("test0"))