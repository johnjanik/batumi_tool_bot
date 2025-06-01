"""
Database models for ToolBot Mini
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, 
    DateTime, ForeignKey, JSON, Enum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

class BookingStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class Tool(Base):
    __tablename__ = 'tools'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    price_per_day = Column(Float, nullable=False)
    image_ids = Column(JSON, default=list)  # List of Telegram file_ids
    available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = relationship("Booking", back_populates="tool", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tool(id={self.id}, name='{self.name}', price={self.price_per_day})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price_per_day': self.price_per_day,
            'image_ids': self.image_ids,
            'available': self.available
        }

class Booking(Base):
    __tablename__ = 'bookings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)  # Telegram user ID
    user_username = Column(String(255), nullable=True)  # Telegram username for display
    user_fullname = Column(String(255), nullable=True)  # User's full name
    tool_id = Column(Integer, ForeignKey('tools.id'), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    delivery_required = Column(Boolean, default=False)
    delivery_address = Column(Text, nullable=True)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    total_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tool = relationship("Tool", back_populates="bookings")
    messages = relationship("Message", back_populates="booking", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Booking(id={self.id}, user_id={self.user_id}, tool_id={self.tool_id}, status={self.status.value})>"
    
    def calculate_days(self):
        """Calculate the number of rental days"""
        delta = self.end_date - self.start_date
        return max(1, delta.days + 1)  # Minimum 1 day
    
    def calculate_total_price(self):
        """Calculate total price based on days and tool price"""
        if self.tool:
            return self.calculate_days() * self.tool.price_per_day
        return 0

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)  # Telegram user ID
    booking_id = Column(Integer, ForeignKey('bookings.id'), nullable=True)
    text = Column(Text, nullable=False)
    is_from_owner = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    booking = relationship("Booking", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, user_id={self.user_id}, timestamp={self.timestamp})>"