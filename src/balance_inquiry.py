from models import Session, Account, User  # Import the User model
from PyQt6.QtWidgets import QMessageBox

class BalanceInquiry:
    def __init__(self, username):
        self.username = username
        self.session = Session()
        self.account = self.get_account()

    def get_account(self):
        """Get user account"""
        try:
            account = self.session.query(Account)\
                .join(User)\
                .filter(User.username == self.username)\
                .first()
            if not account:
                QMessageBox.warning(None, "Account Error", "Account not found")
                return None
            return account
        except Exception as e:
            QMessageBox.critical(None, "Database Error", f"Failed to get account: {str(e)}")
            return None

    def get_balance(self):
        """Get account balance"""
        if not self.account:
            return None
        return self.account.balance

    def close_session(self):
        """Close the database session"""
        self.session.close()