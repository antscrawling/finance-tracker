from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLineEdit, QPushButton, QLabel, QMessageBox)
from PyQt6.QtCore import Qt
from models import User, Session, Account
import hashlib

class SignupWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle("Finance Tracker - Sign Up")
        self.setFixedSize(400, 400)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Title
        title = QLabel("Create Account")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Form fields
        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.username.setStyleSheet("padding: 8px;")
        layout.addWidget(self.username)
        
        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")
        self.email.setStyleSheet("padding: 8px;")
        layout.addWidget(self.email)
        
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setStyleSheet("padding: 8px;")
        layout.addWidget(self.password)
        
        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText("Confirm Password")
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password.setStyleSheet("padding: 8px;")
        layout.addWidget(self.confirm_password)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        signup_btn = QPushButton("Sign Up")
        signup_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        signup_btn.clicked.connect(self.handle_signup)
        button_layout.addWidget(signup_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("padding: 8px;")
        cancel_btn.clicked.connect(self.handle_cancel)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def handle_signup(self):
        if not all([self.username.text(), self.email.text(), 
                   self.password.text(), self.confirm_password.text()]):
            QMessageBox.warning(self, "Error", "Please fill in all fields")
            return
            
        if self.password.text() != self.confirm_password.text():
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return
        
        session = None
        try:
            session = Session()
            
            # Check if username already exists
            if session.query(User).filter_by(username=self.username.text()).first():
                QMessageBox.warning(self, "Error", "Username already exists")
                return
                
            # Check if email already exists
            if session.query(User).filter_by(email=self.email.text()).first():
                QMessageBox.warning(self, "Error", "Email already registered")
                return
            
            # Hash the password
            hashed_password = hashlib.sha256(
                self.password.text().encode()
            ).hexdigest()
            
            # Create new user
            new_user = User(
                username=self.username.text(),
                email=self.email.text(),
                password=hashed_password
            )
            session.add(new_user)
            
            # Create default account for user
            default_account = Account(
                name="Default Account",
                currency="USD",
                user=new_user
            )
            session.add(default_account)
            
            session.commit()
            QMessageBox.information(self, "Success", "Account created successfully!")
            self.return_to_login()
            
        except Exception as e:
            if session:
                session.rollback()
            QMessageBox.critical(self, "Error", f"Failed to create account: {str(e)}")
        finally:
            if session:
                session.close()

    def handle_cancel(self):
        self.return_to_login()

    def return_to_login(self):
        """Return to login window"""
        if self.parent_window:
            self.parent_window.show()
        self.close()