from datetime import datetime
import uuid

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql.sqltypes import Float

Base = declarative_base()


class Products(Base):
    __tablename__ = "products"

    product_id = Column(String, primary_key=True, nullable=False)
    product_name = Column(String, nullable=False)
    product_description = Column(String, nullable=False)
    product_price = Column(Float, nullable=False)


class Users(Base):
    __tablename__ = "users"

    user_fullname = Column(String(64), nullable=False)
    user_email = Column(String(64), primary_key=True, nullable=False)
    user_password = Column(String, nullable=False)


class Chats(Base):
    __tablename__ = "chats"

    chat_id = Column(String(64), primary_key=True, nullable=False, default=str(uuid.uuid4()))
    chat_bookmark = Column(String(128), nullable=False)
    chat_user = Column(String(64), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Messages(Base):
    __tablename__ = "messages"

    message_id = Column(String(64), primary_key=True, nullable=False, default=str(uuid.uuid4()))
    chat_id = Column(String(64), nullable=False)
    message_text = Column(String, nullable=False)
    author_type = Column(String(16), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

# create ms sql to cteate the table user
"""
CREATE TABLE users (
    user_fullname NVARCHAR(64) NOT NULL,
    user_email NVARCHAR(64) PRIMARY KEY NOT NULL
);
"""
