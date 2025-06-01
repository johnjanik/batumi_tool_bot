"""
Configuration management for ToolBot
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Bot configuration"""
    
    # Bot settings
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not found in environment variables!")
    
    # Owner settings
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))
    if OWNER_ID == 0:
        raise ValueError("OWNER_ID not found in environment variables!")
    
    # Database settings
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data/toolbot.db")
    
    # Bot messages
    WELCOME_MESSAGE = """
🛠 Welcome to ToolBot Mini!

I help you rent tools from our catalog.

Available commands:
/tools - Browse available tools
/mybookings - View your bookings
/contact - Send message to owner
/help - Show this message

Owner commands:
/owner - Access owner panel
"""
    
    OWNER_WELCOME_MESSAGE = """
👨‍🔧 Owner Panel

Available commands:
/addtool - Add new tool
/listtools - List all tools
/editool - Edit tool
/deltool - Delete tool
/bookings - View all bookings
/stats - View statistics
"""
    
    # Booking settings
    MAX_BOOKING_DAYS = 30  # Maximum days for a single booking
    MIN_BOOKING_DAYS = 1   # Minimum days for a booking
    
    # Pagination
    TOOLS_PER_PAGE = 5
    BOOKINGS_PER_PAGE = 10
    
    @classmethod
    def is_owner(cls, user_id: int) -> bool:
        """Check if user is the bot owner"""
        return user_id == cls.OWNER_ID

# Create config instance
config = Config()