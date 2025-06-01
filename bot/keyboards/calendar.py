"""
Calendar keyboard for date selection
"""
from datetime import datetime, timedelta
from calendar import monthcalendar, month_name
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

class CalendarKeyboard:
    """Generate calendar inline keyboard"""
    
    @staticmethod
    def create_calendar(year: int = None, month: int = None, min_date: datetime = None) -> InlineKeyboardMarkup:
        """
        Create calendar keyboard for month/year
        
        Args:
            year: Year to display (default: current year)
            month: Month to display (default: current month)
            min_date: Minimum selectable date (default: today)
        """
        now = datetime.now()
        year = year or now.year
        month = month or now.month
        min_date = min_date or now.date()
        
        builder = InlineKeyboardBuilder()
        
        # Month and year header
        builder.row(
            InlineKeyboardButton(
                text=f"{month_name[month]} {year}",
                callback_data="ignore"
            )
        )
        
        # Day headers
        days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        builder.row(*[
            InlineKeyboardButton(text=day, callback_data="ignore")
            for day in days
        ])
        
        # Calendar days
        month_calendar = monthcalendar(year, month)
        for week in month_calendar:
            row_buttons = []
            for day in week:
                if day == 0:
                    # Empty cell
                    row_buttons.append(
                        InlineKeyboardButton(text=" ", callback_data="ignore")
                    )
                else:
                    # Check if date is selectable
                    date = datetime(year, month, day).date()
                    if date < min_date:
                        # Past date - not selectable
                        row_buttons.append(
                            InlineKeyboardButton(
                                text=f"⊘{day}",
                                callback_data="ignore"
                            )
                        )
                    else:
                        # Future date - selectable
                        row_buttons.append(
                            InlineKeyboardButton(
                                text=str(day),
                                callback_data=f"calendar:{year}:{month}:{day}"
                            )
                        )
            builder.row(*row_buttons)
        
        # Navigation buttons
        nav_buttons = []
        
        # Previous month button
        if month == 1:
            prev_month = 12
            prev_year = year - 1
        else:
            prev_month = month - 1
            prev_year = year
            
        # Only show previous month if it has selectable dates
        first_day_prev = datetime(prev_year, prev_month, 1).date()
        if first_day_prev >= min_date or (prev_year == min_date.year and prev_month == min_date.month):
            nav_buttons.append(
                InlineKeyboardButton(
                    text="◀️ Prev",
                    callback_data=f"calendar_nav:{prev_year}:{prev_month}"
                )
            )
        else:
            nav_buttons.append(
                InlineKeyboardButton(text=" ", callback_data="ignore")
            )
        
        # Cancel button
        nav_buttons.append(
            InlineKeyboardButton(
                text="❌ Cancel",
                callback_data="calendar_cancel"
            )
        )
        
        # Next month button
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year
            
        nav_buttons.append(
            InlineKeyboardButton(
                text="Next ▶️",
                callback_data=f"calendar_nav:{next_year}:{next_month}"
            )
        )
        
        builder.row(*nav_buttons)
        
        return builder.as_markup()
    
    @staticmethod
    def parse_calendar_callback(callback_data: str) -> dict:
        """
        Parse calendar callback data
        
        Returns:
            dict with 'action' and 'date' or 'year'/'month'
        """
        parts = callback_data.split(":")
        
        if parts[0] == "calendar" and len(parts) == 4:
            # Date selected
            return {
                'action': 'select',
                'date': datetime(int(parts[1]), int(parts[2]), int(parts[3])).date()
            }
        elif parts[0] == "calendar_nav" and len(parts) == 3:
            # Navigation
            return {
                'action': 'navigate',
                'year': int(parts[1]),
                'month': int(parts[2])
            }
        elif callback_data == "calendar_cancel":
            return {'action': 'cancel'}
        else:
            return {'action': 'ignore'}