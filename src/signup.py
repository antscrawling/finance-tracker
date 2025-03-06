from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLineEdit, QPushButton, QLabel, QMessageBox)
from PyQt6.QtCore import Qt

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
            
        # TODO: Add actual signup logic here
        QMessageBox.information(self, "Success", "Account created successfully!")
        self.close()
        if self.parent_window:
            self.parent_window.show()
    
    def handle_cancel(self):
        self.close()
        if self.parent_window:
            self.parent_window.show()