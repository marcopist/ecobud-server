from ecobud.model.transactions import sync_transactions, transactionsdb

### Remove all transactions from the database
transactionsdb.delete_many({})

sync_transactions("test0")
