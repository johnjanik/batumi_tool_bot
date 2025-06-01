"""
FSM States for ToolBot
"""
from aiogram.fsm.state import State, StatesGroup

class AddToolStates(StatesGroup):
    """States for adding a new tool"""
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_photos = State()
    confirming = State()

class EditToolStates(StatesGroup):
    """States for editing a tool"""
    selecting_tool = State()
    selecting_field = State()
    editing_name = State()
    editing_description = State()
    editing_price = State()
    editing_photos = State()
    editing_availability = State()

class DeleteToolStates(StatesGroup):
    """States for deleting a tool"""
    selecting_tool = State()
    confirming = State()

class BookingStates(StatesGroup):
    """States for booking a tool"""
    viewing_tool = State()
    selecting_start_date = State()
    selecting_end_date = State()
    choosing_delivery = State()
    entering_address = State()
    adding_message = State()
    confirming = State()

class MessageStates(StatesGroup):
    """States for messaging"""
    writing_message = State()
    replying_to_user = State()

class BrowsingStates(StatesGroup):
    """States for browsing tools"""
    viewing_list = State()
    viewing_details = State()