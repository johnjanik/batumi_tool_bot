"""
Common handlers for all users
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from config import config
from bot.keyboards.inline import InlineKeyboards

router = Router(name="common")

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command"""
    await state.clear()
    
    # Check if user is owner
    if config.is_owner(message.from_user.id):
        text = f"Welcome back, Owner! 👨‍🔧\n\n{config.WELCOME_MESSAGE}"
        keyboard = InlineKeyboards.owner_menu()
    else:
        text = config.WELCOME_MESSAGE
        keyboard = InlineKeyboards.main_menu()
    
    await message.answer(text, reply_markup=keyboard)

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    text = config.WELCOME_MESSAGE
    if config.is_owner(message.from_user.id):
        text += f"\n\n{config.OWNER_WELCOME_MESSAGE}"
    
    await message.answer(text)

@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Show main menu"""
    if config.is_owner(message.from_user.id):
        keyboard = InlineKeyboards.owner_menu()
    else:
        keyboard = InlineKeyboards.main_menu()
    
    await message.answer("📋 Main Menu:", reply_markup=keyboard)

@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery, state: FSMContext):
    """Show main menu via callback"""
    await state.clear()
    
    if config.is_owner(callback.from_user.id):
        keyboard = InlineKeyboards.owner_menu()
    else:
        keyboard = InlineKeyboards.main_menu()
    
    await callback.message.edit_text("📋 Main Menu:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "user_menu")
async def show_user_menu(callback: CallbackQuery, state: FSMContext):
    """Show user menu (for owner switching views)"""
    await state.clear()
    keyboard = InlineKeyboards.main_menu()
    await callback.message.edit_text("📋 User Menu:", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery):
    """Show help via callback"""
    text = config.WELCOME_MESSAGE
    if config.is_owner(callback.from_user.id):
        text += f"\n\n{config.OWNER_WELCOME_MESSAGE}"
    
    await callback.message.answer(text)
    await callback.answer()

@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    """Ignore certain callbacks (like calendar headers)"""
    await callback.answer()

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Universal cancel command"""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Nothing to cancel.")
        return
    
    await state.clear()
    await message.answer(
        "❌ Operation cancelled.",
        reply_markup=InlineKeyboards.main_menu() if not config.is_owner(message.from_user.id) 
        else InlineKeyboards.owner_menu()
    )

# Error handler for any unhandled callbacks
@router.callback_query()
async def handle_unknown_callback(callback: CallbackQuery):
    """Handle unknown callbacks"""
    await callback.answer("Unknown action. Please try again.", show_alert=True)