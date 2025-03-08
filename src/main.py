import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from login import LoginWindow
from models import init_db, Session, User, Account, Transaction, Category, TransactionType, ExchangeRate

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