class TransactionManager:
    def __init__(self):
        self.transactions = []

    def add_transaction(self, transaction):
        self.transactions.append(transaction)

    def edit_transaction(self, index, updated_transaction):
        if 0 <= index < len(self.transactions):
            self.transactions[index] = updated_transaction

    def delete_transaction(self, index):
        if 0 <= index < len(self.transactions):
            del self.transactions[index]

    def get_transactions(self):
        return self.transactions