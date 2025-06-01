"""
Inline keyboards for ToolBot
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional
from models import Tool, Booking, BookingStatus

class InlineKeyboards:
    """Collection of inline keyboards"""
    
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Main menu keyboard"""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🛠 Browse Tools", callback_data="browse_tools"),
            InlineKeyboardButton(text="📅 My Bookings", callback_data="my_bookings")
        )
        builder.row(
            InlineKeyboardButton(text="💬 Contact Owner", callback_data="contact_owner"),
            InlineKeyboardButton(text="❓ Help", callback_data="help")
        )
        return builder.as_markup()
    
    @staticmethod
    def owner_menu() -> InlineKeyboardMarkup:
        """Owner panel menu"""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="➕ Add Tool", callback_data="add_tool"),
            InlineKeyboardButton(text="📋 List Tools", callback_data="list_tools")
        )
        builder.row(
            InlineKeyboardButton(text="✏️ Edit Tool", callback_data="edit_tool"),
            InlineKeyboardButton(text="🗑 Delete Tool", callback_data="delete_tool")
        )
        builder.row(
            InlineKeyboardButton(text="📊 View Bookings", callback_data="view_bookings"),
            InlineKeyboardButton(text="📈 Statistics", callback_data="stats")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 Back to User Menu", callback_data="user_menu")
        )
        return builder.as_markup()
    
    @staticmethod
    def tools_list(tools: List[Tool], page: int = 1, total_pages: int = 1) -> InlineKeyboardMarkup:
        """Tools list with pagination"""
        builder = InlineKeyboardBuilder()
        
        # Tool buttons
        for tool in tools:
            status = "✅" if tool.available else "❌"
            builder.row(
                InlineKeyboardButton(
                    text=f"{status} {tool.name} - ${tool.price_per_day}/day",
                    callback_data=f"tool_detail:{tool.id}"
                )
            )
        
        # Pagination
        nav_buttons = []
        if page > 1:
            nav_buttons.append(
                InlineKeyboardButton(text="◀️ Prev", callback_data=f"tools_page:{page-1}")
            )
        nav_buttons.append(
            InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore")
        )
        if page < total_pages:
            nav_buttons.append(
                InlineKeyboardButton(text="Next ▶️", callback_data=f"tools_page:{page+1}")
            )
        
        if nav_buttons:
            builder.row(*nav_buttons)
        
        # Back button
        builder.row(
            InlineKeyboardButton(text="🔙 Main Menu", callback_data="main_menu")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def tool_details(tool: Tool, is_owner: bool = False) -> InlineKeyboardMarkup:
        """Tool details keyboard"""
        builder = InlineKeyboardBuilder()
        
        if tool.available and not is_owner:
            builder.row(
                InlineKeyboardButton(text="📅 Book Now", callback_data=f"book_tool:{tool.id}")
            )
        
        if is_owner:
            builder.row(
                InlineKeyboardButton(text="✏️ Edit", callback_data=f"edit_tool:{tool.id}"),
                InlineKeyboardButton(text="🗑 Delete", callback_data=f"delete_tool:{tool.id}")
            )
            status_text = "❌ Mark Unavailable" if tool.available else "✅ Mark Available"
            builder.row(
                InlineKeyboardButton(
                    text=status_text,
                    callback_data=f"toggle_availability:{tool.id}"
                )
            )
        
        builder.row(
            InlineKeyboardButton(text="🔙 Back to List", callback_data="browse_tools")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def confirm_delete() -> InlineKeyboardMarkup:
        """Confirm deletion keyboard"""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="✅ Yes, Delete", callback_data="confirm_delete"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_delete")
        )
        return builder.as_markup()
    
    @staticmethod
    def delivery_options() -> InlineKeyboardMarkup:
        """Delivery options keyboard"""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🚚 Yes, I need delivery", callback_data="delivery_yes"),
            InlineKeyboardButton(text="🚶 No, I'll pick up", callback_data="delivery_no")
        )
        return builder.as_markup()
    
    @staticmethod
    def booking_confirmation(booking_details: dict) -> InlineKeyboardMarkup:
        """Booking confirmation keyboard"""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="✅ Confirm Booking", callback_data="confirm_booking"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_booking")
        )
        return builder.as_markup()
    
    @staticmethod
    def booking_actions(booking: Booking, is_owner: bool = False) -> InlineKeyboardMarkup:
        """Actions for a booking"""
        builder = InlineKeyboardBuilder()
        
        if is_owner:
            if booking.status == BookingStatus.PENDING:
                builder.row(
                    InlineKeyboardButton(
                        text="✅ Confirm",
                        callback_data=f"confirm_booking:{booking.id}"
                    ),
                    InlineKeyboardButton(
                        text="❌ Reject",
                        callback_data=f"reject_booking:{booking.id}"
                    )
                )
            builder.row(
                InlineKeyboardButton(
                    text="💬 Reply to Customer",
                    callback_data=f"reply_customer:{booking.id}"
                )
            )
        else:
            if booking.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
                builder.row(
                    InlineKeyboardButton(
                        text="❌ Cancel Booking",
                        callback_data=f"cancel_my_booking:{booking.id}"
                    )
                )
            builder.row(
                InlineKeyboardButton(
                    text="💬 Message Owner",
                    callback_data=f"message_about_booking:{booking.id}"
                )
            )
        
        builder.row(
            InlineKeyboardButton(text="🔙 Back", callback_data="my_bookings")
        )
        
        return builder.as_markup()
    
    @staticmethod
    def edit_tool_menu() -> InlineKeyboardMarkup:
        """Edit tool field selection"""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="📝 Name", callback_data="edit_field:name"),
            InlineKeyboardButton(text="📄 Description", callback_data="edit_field:description")
        )
        builder.row(
            InlineKeyboardButton(text="💰 Price", callback_data="edit_field:price"),
            InlineKeyboardButton(text="📸 Photos", callback_data="edit_field:photos")
        )
        builder.row(
            InlineKeyboardButton(text="🔄 Availability", callback_data="edit_field:availability")
        )
        builder.row(
            InlineKeyboardButton(text="✅ Done Editing", callback_data="done_editing")
        )
        return builder.as_markup()
    
    @staticmethod
    def skip_or_cancel() -> InlineKeyboardMarkup:
        """Skip or cancel keyboard"""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="⏭ Skip", callback_data="skip"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="cancel")
        )
        return builder.as_markup()