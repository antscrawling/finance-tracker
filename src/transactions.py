from decimal import Decimal, InvalidOperation, ConversionSyntax
from datetime import datetime
from models import Transaction, Category, TransactionType, ExchangeRate

class TransactionManager:
    def __init__(self):
        self.transactions = []

    def validate_amount(self, amount_str):
        """Validate and convert amount string to float with 2 decimal places"""
        try:
            # Remove commas and whitespace
            clean_amount = amount_str.strip().replace(',', '')
            
            # Convert to float and round immediately
            amount = round(float(clean_amount), 2)
            
            if amount == 0:
                raise ValueError("Amount cannot be zero")
                
            return amount
            
        except ValueError:
            raise ValueError("Please enter a valid amount (e.g., 123.45)")

    def add_transaction(self, amount_str, currency, transaction_type, category_id, user_id, account_id):
        """Add a new transaction with proper float handling"""
        try:
            # Get rounded amount
            amount = self.validate_amount(amount_str)
            
            # Apply sign based on transaction type
            if transaction_type == TransactionType.EXPENSE and amount > 0:
                amount = round(-amount, 2)
            elif transaction_type == TransactionType.INCOME and amount < 0:
                amount = round(abs(amount), 2)

            transaction = Transaction(
                user_id=user_id,
                account_id=account_id,
                date=datetime.now(),
                type=transaction_type,
                category_id=category_id,
                amount=amount,  # Already rounded to 2 decimal places
                currency=currency,
                description=""
            )
            
            self.transactions.append(transaction)
            return transaction
            
        except ValueError as e:
            raise ValueError(f"Invalid transaction input: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to create transaction: {str(e)}")

    def edit_transaction(self, index, amount_str, currency, transaction_type, category_id):
        """Edit transaction with decimal validation"""
        if 0 <= index < len(self.transactions):
            try:
                amount = self.validate_amount(amount_str)
                if transaction_type == TransactionType.EXPENSE:
                    amount = -amount
                    
                transaction = self.transactions[index]
                transaction.amount = float(str(amount))
                transaction.currency = currency
                transaction.type = transaction_type
                transaction.category_id = category_id
                return transaction
                
            except ValueError as e:
                raise ValueError(f"Invalid amount: {str(e)}")
            except Exception as e:
                raise Exception(f"Failed to update transaction: {str(e)}")

    def delete_transaction(self, index):
        """Delete transaction at given index"""
        if 0 <= index < len(self.transactions):
            return self.transactions.pop(index)
        return None

    def get_transactions(self):
        """Get all transactions"""
        return self.transactions

    def get_balance(self, currency='SGD'):
        """Calculate total balance in specified currency"""
        try:
            balance = 0.0
            for transaction in self.transactions:
                if transaction.currency == currency:
                    balance += float(transaction.amount)
            return round(balance, 2)  # Round to 2 decimal places
        except Exception as e:
            raise Exception(f"Failed to calculate balance: {str(e)}")

    def convert_amount(self, amount, from_curr, to_curr):
        """Convert amount between currencies with proper rounding"""
        if from_curr == to_curr:
            return round(float(amount), 2)
            
        try:
            rate = self.session.query(ExchangeRate)\
                .filter_by(from_currency=from_curr, to_currency=to_curr)\
                .first()
                
            if rate:
                return round(float(amount) * rate.rate, 2)
                
            # Try reverse rate
            reverse_rate = self.session.query(ExchangeRate)\
                .filter_by(from_currency=to_curr, to_currency=from_curr)\
                .first()
                
            if reverse_rate:
                return round(float(amount) / reverse_rate.rate, 2)
                
            raise ValueError(f"No exchange rate found for {from_curr} to {to_curr}")
                
        except Exception as e:
            return round(float(amount), 2)