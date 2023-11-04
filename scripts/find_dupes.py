from pprint import pprint
from ecobud.connections.mongo import collections
import jsondiff

transactionsdb = collections["transactions"]

records = transactionsdb.aggregate(
    [
        {
            "$group": {
                "_id": {"username": "$username", "id": "$id"},
                "count": {"$sum": 1},
                "documents": {"$push": "$$ROOT"}
            }
        },
        {"$match": {"count": {"$gt": 1}}},
    ]
)

for record in records:
    documents = record['documents']
    for i in range(len(documents) - 1):
        diff = jsondiff.diff(documents[i], documents[i+1])
        pprint(diff)