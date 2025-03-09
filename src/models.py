from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from contextlib import contextmanager
from datetime import datetime
import enum
import os
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem

Base = declarative_base()

class TransactionType(enum.Enum):
    EXPENSE = "EXPENSE"
    INCOME = "INCOME"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now())
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")

class Account(Base):
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    currency = Column(String(3), nullable=False)
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now())
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False, default=datetime.now())
    type = Column(Enum(TransactionType), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default='SGD')  # Add currency field
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.now())
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    account = relationship("Account", back_populates="transactions")
    user = relationship("User", back_populates="transactions")
    category = relationship("Category")

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    created_at = Column(DateTime, default=datetime.now())

    def __repr__(self):
        return f"<Category(name='{self.name}', type='{self.type}')>"

class ExchangeRate(Base):
    __tablename__ = 'exchange_rates'
    
    id = Column(Integer, primary_key=True)
    from_currency = Column(String(3), nullable=False)
    to_currency = Column(String(3), nullable=False)
    rate = Column(Float, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('from_currency', 'to_currency', name='unique_currency_pair'),
    )

# Improve database configuration
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'finance_tracker.db')
ENGINE = create_engine(f'sqlite:///{DB_PATH}')
SessionFactory = sessionmaker(bind=ENGINE)
Session = scoped_session(SessionFactory)

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def init_db():
    """Initialize database and create default data"""
    Base.metadata.create_all(ENGINE)
    
    session = Session()
    try:
        # Create default categories if none exist
        if session.query(Category).count() == 0:
            default_categories = [
                Category(name='Salary', type=TransactionType.INCOME),
                Category(name='Investment', type=TransactionType.INCOME),
                Category(name='Food', type=TransactionType.EXPENSE),
                Category(name='Transport', type=TransactionType.EXPENSE),
                Category(name='Utilities', type=TransactionType.EXPENSE),
                Category(name='Entertainment', type=TransactionType.EXPENSE),
            ]
            session.add_all(default_categories)
            session.commit()
            
        # Initialize default exchange rates
        init_default_exchange_rates(session)
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def init_default_exchange_rates(session):
    """Initialize default exchange rates if none exist"""
    try:
        if session.query(ExchangeRate).count() == 0:
            default_rates = [
                # SGD base rates
                ExchangeRate(from_currency='USD', to_currency='SGD', rate=1.33),
                ExchangeRate(from_currency='SGD', to_currency='USD', rate=1/1.33),
                ExchangeRate(from_currency='EUR', to_currency='SGD', rate=1.44),
                ExchangeRate(from_currency='SGD', to_currency='EUR', rate=1/1.44),
                ExchangeRate(from_currency='GBP', to_currency='SGD', rate=1.72),
                ExchangeRate(from_currency='SGD', to_currency='GBP', rate=1/1.72),
                ExchangeRate(from_currency='SGD', to_currency='JPY', rate=111.23),
                ExchangeRate(from_currency='JPY', to_currency='SGD', rate=1/111.23),
                
                # USD pairs
                ExchangeRate(from_currency='USD', to_currency='EUR', rate=0.93),
                ExchangeRate(from_currency='EUR', to_currency='USD', rate=1.08),
                ExchangeRate(from_currency='USD', to_currency='GBP', rate=0.77),
                ExchangeRate(from_currency='GBP', to_currency='USD', rate=1.29),
                ExchangeRate(from_currency='USD', to_currency='JPY', rate=148.02),
                ExchangeRate(from_currency='JPY', to_currency='USD', rate=1/148.02),
                
                # EUR pairs
                ExchangeRate(from_currency='EUR', to_currency='GBP', rate=0.83),
                ExchangeRate(from_currency='GBP', to_currency='EUR', rate=1.20),
                ExchangeRate(from_currency='EUR', to_currency='JPY', rate=159.16),
                ExchangeRate(from_currency='JPY', to_currency='EUR', rate=1/159.16),
                
                # GBP pairs
                ExchangeRate(from_currency='GBP', to_currency='JPY', rate=191.76),
                ExchangeRate(from_currency='JPY', to_currency='GBP', rate=1/191.76)
            ]
            session.add_all(default_rates)
            session.commit()
    except Exception as e:
        session.rollback()
        raise ValueError(f"Failed to initialize exchange rates: {str(e)}")

def get_session():
    """Get a new database session with proper error handling"""
    return Session()

def update_balances(self):
    """Update balances in all currencies using float"""
    try:
        with session_scope() as session:
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
                #curr = amount_text.split()[0]  # Get currency
                curr, amount = amount_text.split()  # Split currency and amount
                try:
                    ## Parse amount using the improved method
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

def add_transaction_to_table(self, transaction, running_balance=None):
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
        amount = float(transaction.amount)
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
