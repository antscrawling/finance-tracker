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
from decimal import Decimal
import csv
from models import Session, User, Account, Transaction, Category, TransactionType, ExchangeRate
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DatabaseError
from contextlib import contextmanager

class AccountWindow(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.session = Session()
        
        try:
            # Get user account
            user = self.session.query(User).filter_by(username=username).first()
            if not user:
                raise ValueError(f"User '{username}' not found")
                
            self.user_id = user.id
            self.account = self.session.query(Account)\
                .filter_by(user_id=self.user_id)\
                .first()
            
            if not self.account:
                raise ValueError("No account found for user")
                
            # Create UI before loading data
            self.create_ui_components()
            self.init_ui()
            
            # Set initial currency from account
            index = self.currency_combo.findText(self.account.currency)
            if index >= 0:
                self.currency_combo.setCurrentIndex(index)
                
            # Load data after UI is ready
            self.load_transactions()
            
        except Exception as e:
            if hasattr(self, 'session'):
                self.session.close()
            raise ValueError(f"Could not open account: {str(e)}")

    def create_ui_components(self):
        """Create UI components before initialization"""
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
        
        # Initialize currency combo
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(['SGD', 'USD', 'EUR', 'GBP', 'JPY'])
        self.currency_combo.currentTextChanged.connect(self.handle_currency_change)

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
            self.balance = Decimal(str(account.balance))
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
            running_balance = Decimal('0.00')
            for transaction in transactions:
                running_balance += Decimal(str(transaction.amount))
                self.add_transaction_to_table(transaction, running_balance)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load transactions: {str(e)}")

    def add_transaction(self):
        try:
            amount = Decimal(self.amount_input.text())
            transaction_type = TransactionType.EXPENSE if self.type_combo.currentText() == "Expense" else TransactionType.INCOME
            if transaction_type == TransactionType.EXPENSE:
                amount = -amount
                
            current_currency = self.currency_combo.currentText()
                
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
                
            # Create new transaction with currency
            transaction = Transaction(
                user_id=self.user_id,
                account_id=account.id,
                date=self.date_edit.date().toPyDate(),
                type=transaction_type,
                category_id=category.id,
                amount=float(amount),
                currency=current_currency,  # Add currency
                description=""
            )
            
            # Save to database
            self.session.add(transaction)
            self.session.commit()
            
            # Update account balance
            account.balance += float(amount)
            account.currency = current_currency  # Update account currency
            self.session.commit()
            
            # Add to table
            self.add_transaction_to_table(transaction)
            
            # Update balance display with currency
            self.balance = Decimal(str(account.balance))
            self.balance_label.setText(
                f"Current Balance: {current_currency} {self.balance:,.2f}")
            
            # Clear input
            self.amount_input.clear()
            
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Database Error", f"Failed to save transaction: {str(e)}")

    def add_transaction_to_table(self, transaction, running_balance=None):
        # Need to convert amount to account currency before updating balance
        if transaction.currency != self.account.currency:
            amount = self.convert_amount(
                Decimal(str(transaction.amount)),
                transaction.currency,
                self.account.currency
            )
        else:
            amount = Decimal(str(transaction.amount))
        try:
            row_position = self.transactions_table.rowCount()
            self.transactions_table.insertRow(row_position)
            
            # Format date
            date_item = QTableWidgetItem(transaction.date.strftime("%Y-%m-%d"))
            self.transactions_table.setItem(row_position, 0, date_item)
            
            # Convert enum to string for type
            type_item = QTableWidgetItem(transaction.type.value)
            self.transactions_table.setItem(row_position, 1, type_item)
            
            # Get category name
            category = self.session.query(Category).get(transaction.category_id)
            category_item = QTableWidgetItem(category.name if category else "Unknown")
            self.transactions_table.setItem(row_position, 2, category_item)
            
            # Format amount with currency
            amount = Decimal(str(transaction.amount))
            amount_item = QTableWidgetItem(f"{transaction.currency} {amount:,.2f}")
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.transactions_table.setItem(row_position, 3, amount_item)
            
            # Calculate running balance with currency
            prev_balance = Decimal('0.00') if row_position == 0 else \
                Decimal(self.transactions_table.item(row_position-1, 4).text().split()[-1].replace(',', ''))
            new_balance = prev_balance + amount
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
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select a transaction to delete")
            return
            
        try:
            with transaction_scope(self):
                # Get transaction details
                date_str = self.transactions_table.item(current_row, 0).text()
                amount = float(self.transactions_table.item(current_row, 3).text().replace(',', ''))
                
                # Find transaction in database
                transaction = self.session.query(Transaction)\
                    .filter(Transaction.user.has(username=self.username))\
                    .filter(Transaction.date==datetime.strptime(date_str, "%Y-%m-%d"))\
                    .filter(Transaction.amount==amount)\
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
                self.balance = Decimal(str(account.balance))
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
        try:
            with transaction_scope(self):
                # Update account balance in database
                self.account.balance = float(self.balance)
                # Update UI
                self.balance_label.setText(
                    f"Current Balance: {self.account.currency} {self.balance:,.2f}")
            
            running_balance = Decimal('0.00')
            
            # Recalculate all balances
            for row in range(self.transactions_table.rowCount()):
                # Get amount from current row
                amount = Decimal(self.transactions_table.item(row, 3).text().replace(',', ''))
                running_balance += amount
                
                # Update balance column
                balance_item = QTableWidgetItem(f"{running_balance:,.2f}")
                balance_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.transactions_table.setItem(row, 4, balance_item)
            
            # Update total balance display
            self.balance = running_balance
            self.balance_label.setText(
                f"Current Balance: {self.currency_combo.currentText()} {self.balance:,.2f}")
            
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

    def convert_amount(self, amount, from_curr, to_curr):
        """Convert amount between currencies using stored rates"""
        if from_curr == to_curr:
            return amount
            
        try:
            # Fix: Corrected the filter condition for to_currency
            rate = self.session.query(ExchangeRate)\
                .filter_by(from_currency=from_curr, to_currency=to_curr)\
                .first()
                
            if rate:
                return amount * Decimal(str(rate.rate))
                
            # Try reverse rate
            reverse_rate = self.session.query(ExchangeRate)\
                .filter_by(from_currency=to_curr, to_currency=from_curr)\
                .first()
                
            if reverse_rate:
                return amount / Decimal(str(reverse_rate.rate))
                
            raise ValueError(f"No exchange rate found for {from_curr} to {to_curr}")
                
        except Exception as e:
            QMessageBox.critical(self, "Conversion Error", str(e))
            return amount

    def handle_currency_change(self, new_currency):
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
                self.account.balance = float(self.balance)
                
                # Update balance display
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

@contextmanager
def transaction_scope(self):
    """Provide a transactional scope around a series of operations."""
    try:
        yield self.session
        self.session.commit()
    except Exception:
        self.session.rollback()
        raise