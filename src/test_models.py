import pytest
from models import init_db, session_scope, User, Account, Transaction, Category, TransactionType

def test_database_initialization():
    # Remove existing test database if present
    import os
    test_db_path = os.path.join(os.path.dirname(__file__), 'finance_tracker.db')
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    # Initialize fresh database
    init_db()
    
    with session_scope() as session:
        # Check if default categories were created
        categories = session.query(Category).all()
        assert len(categories) >= 6, "Expected at least 6 default categories"
        
        # Check if categories have correct types
        income_categories = [c for c in categories if c.type == TransactionType.INCOME]
        expense_categories = [c for c in categories if c.type == TransactionType.EXPENSE]
        
        # Verify minimum number of each type
        assert len(income_categories) >= 2, "Expected at least 2 income categories"
        assert len(expense_categories) >= 4, "Expected at least 4 expense categories"
        
        # Verify specific categories exist
        category_names = {c.name for c in categories}
        required_categories = {
            'Salary', 'Investment', 'Food', 'Transport', 
            'Utilities', 'Entertainment'
        }
        assert required_categories.issubset(category_names), \
            "Missing some required categories"

@pytest.fixture(autouse=True)
def cleanup():
    # Setup
    yield
    # Cleanup after test
    import os
    test_db_path = os.path.join(os.path.dirname(__file__), 'finance_tracker.db')
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

if __name__ == "__main__":
    pytest.main([__file__, '-v'])





