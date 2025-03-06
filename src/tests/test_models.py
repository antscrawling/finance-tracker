import pytest
from models import init_db, session_scope, User, Account, Transaction, Category, TransactionType

def test_database_initialization():
    init_db()
    
    with session_scope() as session:
        # Check if default categories were created
        categories = session.query(Category).all()
        assert len(categories) >= 8
        
        # Check if categories have correct types
        income_categories = [c for c in categories if c.type == TransactionType.INCOME]
        expense_categories = [c for c in categories if c.type == TransactionType.EXPENSE]
        assert len(income_categories) >= 2
        assert len(expense_categories) >= 6