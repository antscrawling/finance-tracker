from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLineEdit, QPushButton, QLabel, QMessageBox)
from PyQt6.QtCore import Qt
import sys
from biometric import BiometricAuth  # Changed to absolute import

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Finance Tracker - Login")
        self.setFixedSize(400, 300)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Logo/Title
        title = QLabel("Finance Tracker")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Login form
        form_layout = QVBoxLayout()
        
        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.username.setStyleSheet("padding: 8px;")
        form_layout.addWidget(self.username)
        
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setStyleSheet("padding: 8px;")
        form_layout.addWidget(self.password)
        
        layout.addLayout(form_layout)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        
        self.login_btn = QPushButton("Login")
        self.login_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        self.login_btn.clicked.connect(self.handle_login)
        button_layout.addWidget(self.login_btn)
        
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setStyleSheet("padding: 8px;")
        self.reset_btn.clicked.connect(self.reset_fields)
        button_layout.addWidget(self.reset_btn)
        
        layout.addLayout(button_layout)
        
        # Links layout
        links_layout = QHBoxLayout()
        
        # Forgot password link
        forgot_link = QLabel('<a href="#forgot">Forgot Password?</a>')
        forgot_link.setOpenExternalLinks(False)  # Changed to False
        forgot_link.linkActivated.connect(self.handle_forgot_password)
        links_layout.addWidget(forgot_link)
        
        # Signup link
        signup_link = QLabel('<a href="#signup">Sign Up</a>')
        signup_link.setOpenExternalLinks(False)  # Changed to False
        signup_link.linkActivated.connect(self.handle_signup)
        links_layout.addWidget(signup_link)
        
        layout.addLayout(links_layout)
        
    def handle_login(self):
        if self.username.text() and self.password.text():
            if self.verify_credentials():
                if BiometricAuth().authenticate(self):
                    self.open_main_window()
                else:
                    QMessageBox.warning(self, "Error", "Biometric authentication failed")
            else:
                QMessageBox.warning(self, "Error", "Invalid credentials")
        else:
            QMessageBox.warning(self, "Error", "Please fill in all fields")
    
    def verify_credentials(self):
        try:
            from models import User
            session = Session()
            user = session.query(User).filter_by(username=self.username.text()).first()
            if not user:
                QMessageBox.warning(
                    self, 
                    "Login Error",
                    "User not found. Please sign up first."
                )
                return False
            # ...existing credential verification code...
            return True
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Database Error",
                f"Failed to verify credentials: {str(e)}"
            )
            return False
        finally:
            session.close()
    
    def reset_fields(self):
        self.username.clear()
        self.password.clear()
    
    def handle_forgot_password(self, link):
        QMessageBox.information(self, "Reset Password", 
                              "Password reset link will be sent to your email")
    
    def open_main_window(self):
        try:
            from account import AccountWindow
            username = self.username.text()
            
            if not username:
                QMessageBox.warning(
                    self, 
                    "Input Error", 
                    "Please enter a username"
                )
                return
                
            try:
                self.account_window = AccountWindow(username=username)
                self.account_window.show()
                self.hide()  # Hide instead of close to maintain state
            except ValueError as e:
                QMessageBox.warning(
                    self, 
                    "Account Error", 
                    str(e)
                )
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    "System Error",
                    f"Failed to open account: {str(e)}"
                )
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error",
                f"Failed to initialize account window: {str(e)}"
            )
    
    def handle_signup(self, link):
        from signup import SignupWindow
        self.hide()  # Hide instead of close
        self.signup_window = SignupWindow(self)
        self.signup_window.show()