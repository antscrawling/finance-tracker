from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from contextlib import contextmanager
from datetime import datetime
import enum
import os

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
    created_at = Column(DateTime, default=datetime.utcnow)
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")

class Account(Base):
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    currency = Column(String(3), nullable=False)
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    type = Column(Enum(TransactionType), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
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
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Category(name='{self.name}', type='{self.type}')>"

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
    """Initialize database and create default categories"""
    Base.metadata.create_all(ENGINE)
    
    with session_scope() as session:
        # Create default categories if none exist
        if session.query(Category).count() == 0:
            default_categories = [
                Category(name='Salary', type=TransactionType.INCOME),
                Category(name='Investment', type=TransactionType.INCOME),
                Category(name='Food', type=TransactionType.EXPENSE),
                Category(name='Transport', type=TransactionType.EXPENSE),
                Category(name='Utilities', type=TransactionType.EXPENSE),
                Category(name='Entertainment', type=TransactionType.EXPENSE),
                Category(name='Other Income', type=TransactionType.INCOME),
                Category(name='Other Expense', type=TransactionType.EXPENSE),
            ]
            session.add_all(default_categories)

def get_session():
    """Get a new database session with proper error handling"""
    return Session()