from ecobud.model.transactions import transactionsdb, sync_transactions

### Remove all transactions from the database
transactionsdb.delete_many({})

sync_transactions("test0")