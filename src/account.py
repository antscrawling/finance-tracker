from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QComboBox, QDateEdit, QLineEdit, 
                           QPushButton, QTableWidget, QTableWidgetItem, QTabWidget,
                           QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QPainter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import sys
from datetime import datetime
from decimal import Decimal
import csv
from models import Session, Transaction, TransactionType, Category, Account
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DatabaseError
from contextlib import contextmanager

class AccountWindow(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.session = Session()
        
        # Create tabs before loading data
        self.tab_widget = QTabWidget()
        self.account_tab = QWidget()
        self.reports_tab = QWidget()
        self.settings_tab = QWidget()
        
        # Initialize transactions table
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(5)
        self.transactions_table.setHorizontalHeaderLabels([
            "Date", "Type", "Category", "Amount", "Balance"
        ])
        self.transactions_table.horizontalHeader().setStretchLastSection(True)
        
        try:
            # Get user ID from database
            from models import User
            user = self.session.query(User).filter_by(username=username).first()
            if not user:
                self.session.close()
                raise ValueError("User not found. Please sign up first.")
                
            self.user_id = user.id
            self.setWindowTitle(f"Finance Tracker - {username}'s Account")
            self.setFixedSize(800, 600)
            
            # Initialize UI components
            self.init_ui()
            
            # Load transactions after UI is ready
            self.load_transactions()
            
        except Exception as e:
            self.session.close()
            # Let the login window handle the error display
            raise ValueError(f"Could not open account: {str(e)}")

    def init_ui(self):
        """Initialize all UI components"""
        self.setCentralWidget(self.tab_widget)
        
        # Add tabs
        self.tab_widget.addTab(self.account_tab, "Account")
        self.tab_widget.addTab(self.reports_tab, "Reports")
        self.tab_widget.addTab(self.settings_tab, "Settings")
        
        self.setup_account_tab()
        self.setup_reports_tab()
        self.setup_settings_tab()
        
        # Initialize data
        self.transactions = []
        self.balance = Decimal('0.00')
        
    def setup_account_tab(self):
        layout = QVBoxLayout(self.account_tab)
        
        # Top bar with logout
        top_bar = QHBoxLayout()
        
        # Add title to top bar
        title_label = QLabel("Finance Tracker")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        top_bar.addWidget(title_label)
        
        # Add logout button
        logout_btn = QPushButton("Logout")
        logout_btn.setStyleSheet("""
            background-color: #f44336;
            color: white;
            padding: 5px 15px;
            border-radius: 3px;
        """)
        logout_btn.clicked.connect(self.handle_logout)
        top_bar.addWidget(logout_btn)
        
        layout.addLayout(top_bar)
        
        # Account details section
        account_layout = QHBoxLayout()
        
        # Account name display
        account_label = QLabel("DefaultAcct")
        account_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        account_layout.addWidget(account_label)
        
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["SGD","USD", "EUR", "GBP", "JPY"])
        self.currency_combo.currentTextChanged.connect(self.update_currency)
        account_layout.addWidget(QLabel("Currency:"))
        account_layout.addWidget(self.currency_combo)
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        account_layout.addWidget(QLabel("Date:"))
        account_layout.addWidget(self.date_edit)
        
        layout.addLayout(account_layout)
        
        # Balance display
        balance_layout = QHBoxLayout()
        self.balance_label = QLabel(f"Current Balance: {self.currency_combo.currentText()} 0.00")
        self.balance_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2196F3;")
        balance_layout.addWidget(self.balance_label)
        layout.addLayout(balance_layout)
        
        # Transactions table
        layout.addWidget(self.transactions_table)
        
        # Add transaction section
        transaction_layout = QHBoxLayout()
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Income", "Expense"])
        transaction_layout.addWidget(self.type_combo)
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Salary", "Food", "Transport", "Utilities"])
        transaction_layout.addWidget(self.category_combo)
        
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Amount")
        transaction_layout.addWidget(self.amount_input)
        
        add_btn = QPushButton("Add Transaction")
        add_btn.clicked.connect(self.add_transaction)
        add_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
        transaction_layout.addWidget(add_btn)
        
        # Add delete button
        delete_btn = QPushButton("Delete Transaction")
        delete_btn.setStyleSheet("""
            background-color: #f44336;
            color: white;
            padding: 5px 15px;
            border-radius: 3px;
        """)
        delete_btn.clicked.connect(self.delete_transaction)
        transaction_layout.addWidget(delete_btn)
        
        layout.addLayout(transaction_layout)
    
    def setup_reports_tab(self):
        layout = QVBoxLayout(self.reports_tab)
        
        # Chart selection
        chart_type = QComboBox()
        chart_type.addItems(["Expenses by Category", "Income by Category"])
        chart_type.currentTextChanged.connect(self.update_charts)
        layout.addWidget(chart_type)
        
        # Add pie chart
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # Report controls
        report_buttons = QHBoxLayout()
        
        date_range = QComboBox()
        date_range.addItems(["This Month", "Last Month", "This Year", "All Time"])
        report_buttons.addWidget(date_range)
        
        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_to_csv)
        report_buttons.addWidget(export_btn)
        
        refresh_btn = QPushButton("Refresh Charts")
        refresh_btn.clicked.connect(self.update_charts)
        report_buttons.addWidget(refresh_btn)
        
        layout.addLayout(report_buttons)
    
    def setup_settings_tab(self):
        layout = QVBoxLayout(self.settings_tab)
        
        # Category management
        category_layout = QVBoxLayout()
        category_layout.addWidget(QLabel("Manage Categories"))
        
        # Add category controls here
        
        layout.addLayout(category_layout)
    
    def load_transactions(self):
        # Load transactions from database
        transactions = self.session.query(Transaction)\
            .filter(Transaction.user.has(username=self.username))\
            .order_by(Transaction.date)\
            .all()
        
        for transaction in transactions:
            self.add_transaction_to_table(transaction)

    def add_transaction(self):
        try:
            amount = Decimal(self.amount_input.text())
            transaction_type = TransactionType.EXPENSE if self.type_combo.currentText() == "Expense" else TransactionType.INCOME
            if transaction_type == TransactionType.EXPENSE:
                amount = -amount
                
            # Get category ID
            category = self.session.query(Category)\
                .filter_by(name=self.category_combo.currentText())\
                .first()
            if not category:
                raise ValueError("Invalid category")
                
            # Get user's default account
            account = self.session.query(Account)\
                .filter_by(user_id=self.user_id)\
                .first()
            if not account:
                raise ValueError("No account found")
                
            # Create new transaction
            transaction = Transaction(
                user_id=self.user_id,
                account_id=account.id,
                date=self.date_edit.date().toPyDate(),
                type=transaction_type,
                category_id=category.id,
                amount=float(amount),
                description=""
            )
            
            # Save to database
            self.session.add(transaction)
            self.session.commit()
            
            # Update account balance
            account.balance += float(amount)
            self.session.commit()
            
            # Add to table
            self.add_transaction_to_table(transaction)
            
            # Update balance display
            self.balance = Decimal(str(account.balance))
            self.balance_label.setText(
                f"Current Balance: {self.currency_combo.currentText()} {self.balance:,.2f}")
            
            # Clear input
            self.amount_input.clear()
            
            # Update charts
            self.update_charts()
            
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to save transaction: {str(e)}")

    def add_transaction_to_table(self, transaction):
        """Add a transaction to the table widget"""
        try:
            row_position = self.transactions_table.rowCount()
            self.transactions_table.insertRow(row_position)
            
            # Format date
            date_item = QTableWidgetItem(transaction.date.strftime("%Y-%m-%d"))
            self.transactions_table.setItem(row_position, 0, date_item)
            
            # Convert enum to string for type
            type_item = QTableWidgetItem(transaction.type.value)  # Use .value to get string
            self.transactions_table.setItem(row_position, 1, type_item)
            
            # Get category name
            category = self.session.query(Category).get(transaction.category_id)
            category_item = QTableWidgetItem(category.name if category else "Unknown")
            self.transactions_table.setItem(row_position, 2, category_item)
            
            # Format amount with currency
            amount = Decimal(str(transaction.amount))
            amount_item = QTableWidgetItem(f"{amount:,.2f}")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.transactions_table.setItem(row_position, 3, amount_item)
            
            # Calculate and format running balance
            prev_balance = Decimal('0.00') if row_position == 0 else \
                Decimal(self.transactions_table.item(row_position-1, 4).text().replace(',', ''))
            new_balance = prev_balance + amount
            balance_item = QTableWidgetItem(f"{new_balance:,.2f}")
            balance_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.transactions_table.setItem(row_position, 4, balance_item)
            
            # Color code amounts
            if amount < 0:
                amount_item.setForeground(Qt.GlobalColor.red)
            else:
                amount_item.setForeground(Qt.GlobalColor.darkGreen)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add transaction to table: {str(e)}")

    def update_currency(self):
        self.balance_label.setText(
            f"Current Balance: {self.currency_combo.currentText()} {self.balance:,.2f}")
    
    def update_charts(self):
        self.ax.clear()
        
        # Group transactions by category
        expenses = {}
        incomes = {}
        
        for row in range(self.transactions_table.rowCount()):
            category = self.transactions_table.item(row, 2).text()
            amount = Decimal(self.transactions_table.item(row, 3).text().replace(',', ''))
            
            if amount < 0:
                expenses[category] = expenses.get(category, 0) + abs(amount)
            else:
                incomes[category] = incomes.get(category, 0) + amount
        
        # Create pie chart
        if expenses:
            labels = expenses.keys()
            sizes = expenses.values()
            self.ax.pie(sizes, labels=labels, autopct='%1.1f%%')
            self.ax.set_title("Expenses by Category")
        
        self.canvas.draw()
    
    def export_to_csv(self):
        # Add CSV export logic here
        pass
    
    def delete_transaction(self):
        current_row = self.transactions_table.currentRow()
        if current_row >= 0:
            # Get transaction from database
            date_str = self.transactions_table.item(current_row, 0).text()
            amount = float(self.transactions_table.item(current_row, 3).text().replace(',', ''))
            
            # Delete from database
            transaction = self.session.query(Transaction)\
                .filter(Transaction.user.has(username=self.username))\
                .filter(Transaction.date==datetime.strptime(date_str, "%Y-%m-%d"))\
                .filter(Transaction.amount==amount)\
                .first()
            
            if transaction:
                self.session.delete(transaction)
                self.session.commit()
            
            # Remove from table
            self.transactions_table.removeRow(current_row)
            self.update_balances()
        else:
            QMessageBox.warning(self, "Error", "Please select a transaction to delete")
    
    def handle_logout(self):
        from login import LoginWindow
        reply = QMessageBox.question(self, 'Logout', 
                                   'Are you sure you want to logout?',
                                   QMessageBox.StandardButton.Yes | 
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.login_window = LoginWindow()
            self.login_window.show()
            self.close()

    def handle_error(self, title, message):
        """Utility method to display error messages"""
        QMessageBox.warning(self, title, message)

@contextmanager
def transaction_scope(self):
    """Provide a transactional scope around a series of operations."""
    try:
        yield self.session
        self.session.commit()
    except Exception:
        self.session.rollback()
        raise