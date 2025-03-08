import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from login import LoginWindow
from models import init_db, Session, User, Account, Transaction, Category, TransactionType, ExchangeRate
from sqlalchemy import UniqueConstraint

def main():
    # Create QApplication first
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for better macOS compatibility
    
    try:
        # Initialize database
        init_db()
        
        # Test database connection
        session = Session()
        try:
            session.query(User).count()  # Test query to verify connection
        except Exception as db_error:
            QMessageBox.critical(None, "Database Error", 
                               f"Database connection failed: {str(db_error)}")
            return 1
        finally:
            session.close()
            
        # Show login window
        window = LoginWindow()
        window.show()
        
        # Start application event loop
        return app.exec()
        
    except Exception as e:
        QMessageBox.critical(None, "Database Error", 
                           f"Failed to initialize database: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

# These pairs are duplicated
ExchangeRate(from_currency='EUR', to_currency='USD', rate=1.08),  # First instance
ExchangeRate(from_currency='EUR', to_currency='USD', rate=1.08),  # Duplicate

ExchangeRate(from_currency='USD', to_currency='EUR', rate=0.93),  # First instance
ExchangeRate(from_currency='USD', to_currency='EUR', rate=0.93),  # Duplicate

class ExchangeRate(Base):
    __table_args__ = (
        UniqueConstraint('from_currency', 'to_currency', name='unique_currency_pair'),
    )

def parse_amount_string(self, amount_str):
    """Parse amount string to float, handling currency symbols and formatting"""
    try:
        # Remove all non-numeric characters except decimal point and minus sign
        clean_string = ''.join(c for c in amount_str if c.isdigit() or c in ['.', '-'])

        # Handle negative numbers
        if clean_string.startswith('-'):
            sign = -1
            clean_string = clean_string[1:]
        else:
            sign = 1

        # Remove commas
        clean_string = clean_string.replace(',', '')

        # Convert to float
        amount = float(clean_string) * sign
        return amount
    except (ValueError, AttributeError):
        return 0.0