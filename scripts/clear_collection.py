from ecobud.connections.mongo import collections

transactionsdb = collections["transactions"]

### Remove all transactions from the database

transactionsdb.delete_many({})