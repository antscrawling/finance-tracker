import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from login import LoginWindow
from models import init_db

def main():
    try:
        # Initialize database
        init_db()
        
        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # Use Fusion style for better macOS compatibility
        window = LoginWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        QMessageBox.critical(None, "Database Error", 
                           f"Failed to initialize database: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()