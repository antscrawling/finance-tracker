from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QComboBox, QDateEdit, QLineEdit, 
                           QPushButton, QTableWidget, QTableWidgetItem, QTabWidget,
                           QMessageBox, QFileDialog, QGroupBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QPainter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation, ConversionSyntax
import csv
from models import Session, User, Account, Transaction, Category, TransactionType, ExchangeRate
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DatabaseError
from contextlib import contextmanager
from balance_inquiry import BalanceInquiry

class AccountWindow(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.balance_inquiry = BalanceInquiry(username)
        self.account = self.balance_inquiry.get_account()
        if not self.account:
            # Handle the case where the account is not found
            QMessageBox.critical(self, "Account Error", "Account not found.")
            self.close()
            return

        self.balance = self.balance_inquiry.get_balance()  # Get balance from balance_inquiry
        self.session = Session()
        self.balance_labels = {}
        
        try:
            # Get user data first
            user = self.session.query(User).filter_by(username=username).first()
            if not user:
                raise ValueError(f"User '{username}' not found")
                
            self.user_id = user.id
            self.account = self.session.query(Account)\
                .filter_by(user_id=self.user_id)\
                .first()
            
            if not self.account:
                raise ValueError("No account found for user")
            
            # Set initial balance from account
            self.balance = self.balance_inquiry.get_balance()  # Get balance from balance_inquiry
            
            # Set window properties
            self.setWindowTitle(f"Finance Tracker - {username}'s Account")
            self.setFixedSize(800, 600)
            
            # Create UI components first
            self.create_ui_components()
            
            # Create main widget and layout
            self.central_widget = QWidget()
            self.setCentralWidget(self.central_widget)
            self.main_layout = QVBoxLayout(self.central_widget)
            
            # Setup UI with created components
            self.setup_ui()
            
            # Set initial currency
            index = self.currency_combo.findText(self.account.currency)
            if index >= 0:
                self.currency_combo.setCurrentIndex(index)
            
            # Load data after UI is ready
            self.load_account_data()
            
        except Exception as e:
            if hasattr(self, 'session'):
                self.session.close()
            raise ValueError(f"Could not open account: {str(e)}")

    def setup_ui(self):
        """Setup all UI components in correct order"""
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.account_tab = QWidget()
        self.reports_tab = QWidget()
        self.settings_tab = QWidget()
        
        # Add tabs
        self.tab_widget.addTab(self.account_tab, "Account")
        self.tab_widget.addTab(self.reports_tab, "Reports")
        self.tab_widget.addTab(self.settings_tab, "Settings")
        
        # Setup each tab
        self.setup_account_tab()
        self.setup_reports_tab()
        self.setup_settings_tab()

    def load_account_data(self):
        """Load account data and update UI"""
        try:
            # Set initial balance
            self.account = self.balance_inquiry.get_account()
            self.balance = self.balance_inquiry.get_balance()  # Get balance from balance_inquiry
            
            # Set currency
            index = self.currency_combo.findText(self.account.currency)
            if index >= 0:
                self.currency_combo.setCurrentIndex(index)
            
            # Update all balance displays
            self.update_balances()
            
            # Load transactions
            self.load_transactions()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load account data: {str(e)}")

    def create_ui_components(self):
        """Create all UI components before layout setup"""
        # Currency selector
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(['SGD', 'USD', 'EUR', 'GBP', 'JPY'])
        self.currency_combo.currentTextChanged.connect(self.handle_currency_change)
        
        # Initialize transactions table
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(5)
        self.transactions_table.setHorizontalHeaderLabels([
            "Date", "Type", "Category", "Amount", "Balance"
        ])
        
        # Initialize balance labels
        self.balance_label = QLabel(f"{self.account.currency} {self.balance:,.2f}")
        self.balance_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        # Initialize currency balance labels
        for currency in ['SGD', 'USD', 'EUR', 'GBP', 'JPY']:
            label = QLabel(f"{currency} 0.00")
            label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2196F3;")
            self.balance_labels[currency] = label
        
        # Initialize tabs
        self.tab_widget = QTabWidget()
        self.account_tab = QWidget()
        self.reports_tab = QWidget()
        self.settings_tab = QWidget()

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
        
        account_layout.addWidget(QLabel("Currency:"))
        account_layout.addWidget(self.currency_combo)
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        account_layout.addWidget(QLabel("Date:"))
        account_layout.addWidget(self.date_edit)
        
        layout.addLayout(account_layout)
        
        # Balance display - use existing balance_labels
        balance_layout = QVBoxLayout()
        balance_layout.addWidget(QLabel("Current Balance:"))
        
        # Main balance label
        self.balance_label = QLabel(f"{self.account.currency} {self.balance:,.2f}")
        self.balance_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        balance_layout.addWidget(self.balance_label)
        
        # Add existing currency balance labels
        for currency in ['SGD', 'USD', 'EUR', 'GBP', 'JPY']:
            if currency not in self.balance_labels:
                self.balance_labels[currency] = QLabel(f"{currency} 0.00")
                self.balance_labels[currency].setStyleSheet(
                    "font-size: 14px; font-weight: bold; color: #2196F3;"
                )
            balance_layout.addWidget(self.balance_labels[currency])
        
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
        
        # Exchange Rates Section
        rates_group = QGroupBox("Exchange Rates")
        rates_layout = QVBoxLayout()
        
        # Exchange rate table
        self.rate_table = QTableWidget()
        self.rate_table.setColumnCount(4)
        self.rate_table.setHorizontalHeaderLabels([
            "From Currency", "To Currency", "Rate", "Last Updated"
        ])
        self.rate_table.horizontalHeader().setStretchLastSection(True)
        rates_layout.addWidget(self.rate_table)
        
        # Add rate controls
        rate_form = QHBoxLayout()
        
        self.from_currency = QComboBox()
        self.from_currency.addItems(['SGD', 'USD', 'EUR', 'GBP', 'JPY'])
        rate_form.addWidget(QLabel("From:"))
        rate_form.addWidget(self.from_currency)
        
        self.to_currency = QComboBox()
        self.to_currency.addItems(['SGD', 'USD', 'EUR', 'GBP', 'JPY'])
        rate_form.addWidget(QLabel("To:"))
        rate_form.addWidget(self.to_currency)
        
        self.rate_input = QLineEdit()
        self.rate_input.setPlaceholderText("Exchange Rate")
        rate_form.addWidget(self.rate_input)
        
        update_rate_btn = QPushButton("Add/Update Rate")
        update_rate_btn.clicked.connect(self.update_exchange_rate)
        update_rate_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 5px;"
        )
        rate_form.addWidget(update_rate_btn)
        
        rates_layout.addLayout(rate_form)
        rates_group.setLayout(rates_layout)
        layout.addWidget(rates_group)
        
        # Load existing rates
        self.load_exchange_rates()
    
    def load_transactions(self):
        """Load transactions and initialize balance from database"""
        try:
            # Get user's account and balance
            account = self.session.query(Account)\
                .filter_by(user_id=self.user_id)\
                .first()
                
            if not account:
                raise ValueError("No account found for user")
                
            # Initialize balance from account
            self.balance = float(account.balance)
            self.balance_label.setText(
                f"Current Balance: {self.currency_combo.currentText()} {self.balance:,.2f}")
            
            # Load transactions from database
            transactions = self.session.query(Transaction)\
                .filter_by(account_id=account.id)\
                .order_by(Transaction.date)\
                .all()
            
            # Clear existing table
            self.transactions_table.setRowCount(0)
            
            # Add transactions to table
            running_balance = 0.0
            for transaction in transactions:
                running_balance += float(transaction.amount)
                self.add_transaction_to_table(transaction, running_balance)
            
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load transactions: {str(e)}")

    def add_transaction(self):
        """Add a new transaction with float handling"""
        try:
            # Sanitize and validate amount input
            amount_str = self.amount_input.text().strip().replace(',', '')
            try:
                # Validate and convert amount
                amount = self.parse_amount_string(amount_str)
                if amount == 0:
                    raise ValueError("Please enter a valid amount (e.g., 123.45)")
            except ValueError:
                raise ValueError("Please enter a valid amount (e.g., 123.45)")
                
            current_currency = self.currency_combo.currentText()
            transaction_type = TransactionType.EXPENSE if self.type_combo.currentText() == "Expense" else TransactionType.INCOME
            
            # Adjust sign for expense
            if transaction_type == TransactionType.EXPENSE:
                amount = -amount
                
            # Get category
            category = self.session.query(Category)\
                .filter_by(name=self.category_combo.currentText())\
                .first()
            if not category:
                raise ValueError("Invalid category selected")
                
            # Create new transaction with proper decimal conversion
            transaction = Transaction(
                user_id=self.user_id,
                account_id=self.account.id,
                date=self.date_edit.date().toPyDate(),
                type=transaction_type,
                category_id=category.id,
                amount=amount,  # Use float directly
                currency=current_currency,
                description=""
            )
            
            # Save transaction and update balance within transaction scope
            with transaction_scope(self):
                self.session.add(transaction)
                
                # Convert amount if currencies differ
                if current_currency != self.account.currency:
                    converted_amount = self.convert_amount(amount, current_currency, self.account.currency)
                else:
                    converted_amount = amount
                    
                # Update account balance with float
                self.account.balance += converted_amount
                
                # Update UI
                self.account = self.balance_inquiry.get_account()
                self.balance = self.balance_inquiry.get_balance()  # Get balance from balance_inquiry
                self.balance_label.setText(
                    f"Current Balance: {self.account.currency} {self.balance:,.2f}"
                )
                
                # Add to transactions table
                self.add_transaction_to_table(transaction)
                
            # Clear input and update charts
            self.amount_input.clear()
            self.update_charts()
                
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to save transaction: {str(e)}")

    def add_transaction_to_table(self, transaction, running_balance=None):
        amount = 0.00
        try:
            row_position = self.transactions_table.rowCount()
            self.transactions_table.insertRow(row_position)
            
            # Format date
            date_item = QTableWidgetItem(transaction.date.strftime("%Y-%m-%d"))
            self.transactions_table.setItem(row_position, 0, date_item)
            
            # Transaction type
            type_item = QTableWidgetItem(transaction.type.value)
            self.transactions_table.setItem(row_position, 1, type_item)
            
            # Category
            category = self.session.query(Category).get(transaction.category_id)
            category_item = QTableWidgetItem(category.name if category else "Unknown")
            self.transactions_table.setItem(row_position, 2, category_item)
            
            # Amount with currency
            #if (transaction.amount).isdigit():
            #amount = float(transaction.amount)
            amount = transaction.amount
            amount_str = f"{transaction.currency} {abs(amount):,.2f}"
            if amount < 0:
                amount_str = f"{transaction.currency} -{abs(amount):,.2f}"
            amount_item = QTableWidgetItem(amount_str)
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.transactions_table.setItem(row_position, 3, amount_item)
            
            # Calculate running balance
            if running_balance is not None:
                new_balance = running_balance
            else:
                if row_position == 0:
                    new_balance = amount
                else:
                    # Get the balance from the database, not the screen
                    prev_balance = self.balance_inquiry.get_balance()
                    new_balance = round(prev_balance + amount, 2)

            # Format balance
            balance_item = QTableWidgetItem(f"{transaction.currency} {new_balance:,.2f}")
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
            amount_text = self.transactions_table.item(row, 3).text()
            
            try:
                # Parse amount using the improved method
                amount = self.parse_amount_string(amount_text)
                
                if amount < 0:
                    expenses[category] = expenses.get(category, 0) + abs(amount)
                else:
                    incomes[category] = incomes.get(category, 0) + amount
                    
            except ValueError as e:
                QMessageBox.warning(
                    self, 
                    "Conversion Error", 
                    f"Error processing amount in row {row + 1}: {str(e)}"
                )
        
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
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select a transaction to delete")
            return
            
        try:
            with transaction_scope(self):
                # Get transaction details
                date_str = self.transactions_table.item(current_row, 0).text()
                amount_text = self.transactions_table.item(current_row, 3).text()
                amount = self.parse_amount_string(amount_text)
                
                # Find transaction in database
                transaction = self.session.query(Transaction)\
                    .filter(Transaction.user.has(username=self.username))\
                    .filter(Transaction.date == datetime.strptime(date_str, "%Y-%m-%d"))\
                    .filter(Transaction.amount == amount)\
                    .first()
                
                if not transaction:
                    raise ValueError("Transaction not found in database")
                
                # Get and update account balance
                account = self.session.query(Account)\
                    .filter_by(user_id=self.user_id)\
                    .first()
                
                if account:
                    # Reverse the transaction amount
                    account.balance -= transaction.amount
                    
                # Delete the transaction
                self.session.delete(transaction)
                
                # Remove from table and update UI
                self.transactions_table.removeRow(current_row)
                self.update_balances()
                self.update_charts()
                
                # Update balance display with new account balance
                self.balance = float(account.balance)
                self.balance_label.setText(
                    f"Current Balance: {self.currency_combo.currentText()} {self.balance:,.2f}"
                )
                
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Database Error", f"Failed to delete transaction: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")

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

    def update_balances(self):
        """Update balances in all currencies using float"""
        try:
            with transaction_scope(self):
                # Get base balance from balance_inquiry
                self.account = self.balance_inquiry.get_account()
                if not self.account:
                    QMessageBox.critical(self, "Account Error", "Account not found.")
                    return
                base_balance = self.balance_inquiry.get_balance()  # Get balance from balance_inquiry
                
                # Update balance in all currencies
                for currency, label in self.balance_labels.items():
                    if currency == self.account.currency:
                        balance = base_balance
                    else:
                        balance = self.convert_amount(base_balance, self.account.currency, currency)
                    label.setText(f"{currency} {balance:,.2f}")
                
                # Update running balances in transaction table
                running_balance_sgd = 0.0
                running_balance_account = 0.0
                
                for row in range(self.transactions_table.rowCount()):
                    # Get amount from amount column
                    amount_text = self.transactions_table.item(row, 3).text()
                    curr,amt = amount_text.split() # Get currency
                    amount = float(amt.replace(',', '')) # Get amount
                    print(f'curr: {curr}, amount: {amount}')
                    
                    try:
                        # Parse amount using the improved method
                        #amount = self.parse_amount_string(amount_text)
                        
                        # Convert to SGD and account currency
                        if curr != 'SGD':
                            amount_sgd = self.convert_amount(amount, curr, 'SGD')
                        else:
                            amount_sgd = amount
                            
                        if curr != self.account.currency:
                            amount_account = self.convert_amount(amount, curr, self.account.currency)
                        else:
                            amount_account = amount
                        
                        running_balance_sgd = round(running_balance_sgd + amount_sgd, 2)
                        running_balance_account = round(running_balance_account + amount_account, 2)
                        
                        # Update balance column
                        balance_text = f"SGD {running_balance_sgd:,.2f} / {self.account.currency} {running_balance_account:,.2f}"
                        balance_item = QTableWidgetItem(balance_text)
                        balance_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        self.transactions_table.setItem(row, 4, balance_item)
                        
                    except ValueError as e:
                        QMessageBox.warning(
                            self, 
                            "Conversion Error", 
                            f"Error processing amount in row {row + 1}: {str(e)}"
                        )
                        
                # Update charts
                self.update_charts()
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"Failed to update balances: {str(e)}"
            )

    def load_exchange_rates(self):
        """Load exchange rates from database"""
        try:
            from models import ExchangeRate
            rates = self.session.query(ExchangeRate).all()
            self.rate_table.setRowCount(0)
            
            for rate in rates:
                row = self.rate_table.rowCount()
                self.rate_table.insertRow(row)
                self.rate_table.setItem(row, 0, QTableWidgetItem(rate.from_currency))
                self.rate_table.setItem(row, 1, QTableWidgetItem(rate.to_currency))
                self.rate_table.setItem(row, 2, QTableWidgetItem(f"{rate.rate:.4f}"))
                self.rate_table.setItem(row, 3, QTableWidgetItem(
                    rate.updated_at.strftime("%Y-%m-%d %H:%M")
                ))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load exchange rates: {str(e)}")

    def update_exchange_rate(self):
        """Add or update exchange rate"""
        try:
            from_curr = self.from_currency.currentText()
            to_curr = self.to_currency.currentText()
            
            if from_curr == to_curr:
                raise ValueError("From and To currencies must be different")
                
            try:
                if (self.rate_input.text()).isdigit():
                    rate = float(self.rate_input.text())
                if rate <= 0:
                    raise ValueError("Rate must be positive")
            except ValueError:
                raise ValueError("Please enter a valid rate")
            
            from models import ExchangeRate
            # Check if rate exists
            existing_rate = self.session.query(ExchangeRate)\
                .filter_by(from_currency=from_curr, to_currency=to_curr)\
                .first()
                
            with transaction_scope(self):
                if existing_rate:
                    existing_rate.rate = rate
                else:
                    new_rate = ExchangeRate(
                        from_currency=from_curr,
                        to_currency=to_curr,
                        rate=rate
                    )
                    self.session.add(new_rate)
                
            self.load_exchange_rates()
            self.rate_input.clear()
            QMessageBox.information(self, "Success", "Exchange rate updated successfully")
            
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update exchange rate: {str(e)}")

    def convert_amount(self, amount:float, from_curr:str, to_curr:str):
        """Convert amount between currencies using float"""
        if from_curr == to_curr:
            return round(float(amount), 2)
            
        try:
            # Get conversion rate
            rate = self.session.query(ExchangeRate)\
                .filter_by(from_currency=from_curr, to_currency=to_curr)\
                .first()
                
            if rate:
                return round(float(amount) * rate.rate, 2)
                
            # Try reverse rate
            reverse_rate = self.session.query(ExchangeRate)\
                .filter_by(from_currency=to_curr, to_currency=from_curr)\
                .first()
                
            if reverse_rate:
                return round(float(amount) / reverse_rate.rate, 2)
                
            raise ValueError(f"No exchange rate found for {from_curr} to {to_curr}")
                
        except Exception as e:
            QMessageBox.critical(self, "Conversion Error", str(e))
            return round(float(amount), 2)

    def handle_currency_change(self, new_currency:str):
        """Handle currency change and update all amounts"""
        try:
            old_currency = self.account.currency
            if old_currency == new_currency:
                return
            
            # Update account currency in database
            with transaction_scope(self):
                # Convert account balance
                self.balance = self.convert_amount(
                    self.balance, 
                    old_currency, 
                    new_currency
                )
                self.account.currency = new_currency
                self.account.balance = self.balance
                
                # Update balance display
                self.account = self.balance_inquiry.get_account()
                self.balance = self.balance_inquiry.get_balance()  # Get balance from balance_inquiry
                self.balance_label.setText(
                    f"Current Balance: {new_currency} {self.balance:,.2f}"
                )
                
                # Reload transactions with new currency
                self.load_transactions()
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Currency Error", 
                f"Failed to update currency: {str(e)}"
            )
            # Revert currency combo box
            index = self.currency_combo.findText(old_currency)
            if index >= 0:
                self.currency_combo.setCurrentIndex(index)

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

    def closeEvent(self, event):
        """Override close event to close the database session"""
        self.balance_inquiry.close_session()
        event.accept()

@contextmanager
def transaction_scope(self):
    """Provide a transactional scope around a series of operations."""
    try:
        yield self.session
        self.session.commit()
    except Exception:
        self.session.rollback()
        raise