"""
User handlers for browsing and booking tools
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import logging
import math

from config import config
from db import async_session
from models import Tool, Booking, BookingStatus, Message as DBMessage
from bot.states import BookingStates, MessageStates, BrowsingStates
from bot.keyboards.inline import InlineKeyboards
from bot.keyboards.calendar import CalendarKeyboard

logger = logging.getLogger(__name__)
router = Router(name="user")

# === BROWSE TOOLS ===
@router.message(Command("tools"))
@router.callback_query(F.data == "browse_tools")
@router.callback_query(F.data.startswith("tools_page:"))
async def browse_tools(update: Message | CallbackQuery, state: FSMContext):
    """Browse available tools"""
    await state.clear()
    
    # Determine page number
    page = 1
    if isinstance(update, CallbackQuery) and update.data.startswith("tools_page:"):
        page = int(update.data.split(":")[1])
    
    async with async_session() as session:
        # Count total tools
        total_count = await session.scalar(
            select(func.count(Tool.id)).where(Tool.available == True)
        )
        
        if total_count == 0:
            text = "😔 No tools available for rent at the moment.\n\nPlease check back later!"
            if isinstance(update, CallbackQuery):
                await update.message.edit_text(text)
                await update.answer()
            else:
                await update.answer(text)
            return
        
        # Calculate pagination
        total_pages = math.ceil(total_count / config.TOOLS_PER_PAGE)
        offset = (page - 1) * config.TOOLS_PER_PAGE
        
        # Get tools for current page
        result = await session.execute(
            select(Tool)
            .where(Tool.available == True)
            .order_by(Tool.id)
            .offset(offset)
            .limit(config.TOOLS_PER_PAGE)
        )
        tools = result.scalars().all()
        
        text = "🛠 <b>Available Tools:</b>\n\nSelect a tool to view details:"
        keyboard = InlineKeyboards.tools_list(tools, page, total_pages)
        
        if isinstance(update, CallbackQuery):
            await update.message.edit_text(text, reply_markup=keyboard)
            await update.answer()
        else:
            await update.answer(text, reply_markup=keyboard)

# === VIEW TOOL DETAILS ===
@router.callback_query(F.data.startswith("tool_detail:"))
async def view_tool_details(callback: CallbackQuery, state: FSMContext):
    """View detailed information about a tool"""
    tool_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        tool = await session.get(Tool, tool_id)
        if not tool:
            await callback.answer("Tool not found!", show_alert=True)
            return
        
        # Build tool description
        text = (
            f"🛠 <b>{tool.name}</b>\n\n"
            f"📝 <b>Description:</b>\n{tool.description}\n\n"
            f"💰 <b>Price:</b> ${tool.price_per_day:.2f} per day\n"
            f"📸 <b>Photos:</b> {len(tool.image_ids)}\n"
            f"✅ <b>Status:</b> {'Available' if tool.available else 'Not Available'}"
        )
        
        # Send photos if available
        if tool.image_ids:
            if len(tool.image_ids) == 1:
                await callback.message.answer_photo(
                    photo=tool.image_ids[0],
                    caption=text,
                    reply_markup=InlineKeyboards.tool_details(
                        tool, 
                        is_owner=config.is_owner(callback.from_user.id)
                    )
                )
            else:
                # Send as media group
                media = [
                    InputMediaPhoto(media=file_id) for file_id in tool.image_ids[:10]
                ]
                media[0].caption = text
                await callback.message.answer_media_group(media)
                await callback.message.answer(
                    "What would you like to do?",
                    reply_markup=InlineKeyboards.tool_details(
                        tool,
                        is_owner=config.is_owner(callback.from_user.id)
                    )
                )
        else:
            await callback.message.answer(
                text,
                reply_markup=InlineKeyboards.tool_details(
                    tool,
                    is_owner=config.is_owner(callback.from_user.id)
                )
            )
        
        await callback.answer()
        await state.update_data(current_tool_id=tool_id)

# === START BOOKING ===
@router.callback_query(F.data.startswith("book_tool:"))
async def start_booking(callback: CallbackQuery, state: FSMContext):
    """Start the booking process"""
    tool_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        tool = await session.get(Tool, tool_id)
        if not tool or not tool.available:
            await callback.answer("This tool is not available!", show_alert=True)
            return
        
        await state.update_data(
            tool_id=tool_id,
            tool_name=tool.name,
            tool_price=tool.price_per_day
        )
        
        await callback.message.answer(
            f"📅 <b>Booking: {tool.name}</b>\n\n"
            "Please select the <b>start date</b> for your rental:",
            reply_markup=CalendarKeyboard.create_calendar()
        )
        
        await state.set_state(BookingStates.selecting_start_date)
        await callback.answer()

# === HANDLE CALENDAR CALLBACKS ===
@router.callback_query(BookingStates.selecting_start_date, F.data.startswith(("calendar", "calendar_nav", "calendar_cancel")))
async def handle_start_date_selection(callback: CallbackQuery, state: FSMContext):
    """Handle start date selection"""
    result = CalendarKeyboard.parse_calendar_callback(callback.data)
    
    if result['action'] == 'cancel':
        await callback.message.edit_text("❌ Booking cancelled.")
        await state.clear()
        await callback.answer()
        return
    
    elif result['action'] == 'navigate':
        # Update calendar view
        await callback.message.edit_reply_markup(
            reply_markup=CalendarKeyboard.create_calendar(
                year=result['year'],
                month=result['month']
            )
        )
        await callback.answer()
        
    elif result['action'] == 'select':
        # Save start date and move to end date selection
        start_date = result['date']
        await state.update_data(start_date=start_date)
        
        await callback.message.edit_text(
            f"✅ Start date: <b>{start_date.strftime('%B %d, %Y')}</b>\n\n"
            "Now select the <b>end date</b> for your rental:",
            reply_markup=CalendarKeyboard.create_calendar(min_date=start_date)
        )
        
        await state.set_state(BookingStates.selecting_end_date)
        await callback.answer()
    
    else:
        await callback.answer()

@router.callback_query(BookingStates.selecting_end_date, F.data.startswith(("calendar", "calendar_nav", "calendar_cancel")))
async def handle_end_date_selection(callback: CallbackQuery, state: FSMContext):
    """Handle end date selection"""
    result = CalendarKeyboard.parse_calendar_callback(callback.data)
    
    if result['action'] == 'cancel':
        await callback.message.edit_text("❌ Booking cancelled.")
        await state.clear()
        await callback.answer()
        return
    
    elif result['action'] == 'navigate':
        data = await state.get_data()
        start_date = data['start_date']
        
        # Update calendar view
        await callback.message.edit_reply_markup(
            reply_markup=CalendarKeyboard.create_calendar(
                year=result['year'],
                month=result['month'],
                min_date=start_date
            )
        )
        await callback.answer()
        
    elif result['action'] == 'select':
        # Validate end date
        data = await state.get_data()
        start_date = data['start_date']
        end_date = result['date']
        
        # Check maximum booking period
        days_diff = (end_date - start_date).days + 1
        if days_diff > config.MAX_BOOKING_DAYS:
            await callback.answer(
                f"Maximum booking period is {config.MAX_BOOKING_DAYS} days!",
                show_alert=True
            )
            return
        
        await state.update_data(end_date=end_date)
        
        # Calculate total price
        total_price = days_diff * data['tool_price']
        await state.update_data(
            days=days_diff,
            total_price=total_price
        )
        
        # Ask about delivery
        await callback.message.edit_text(
            f"📅 <b>Booking Summary:</b>\n\n"
            f"Tool: <b>{data['tool_name']}</b>\n"
            f"Start: <b>{start_date.strftime('%B %d, %Y')}</b>\n"
            f"End: <b>{end_date.strftime('%B %d, %Y')}</b>\n"
            f"Days: <b>{days_diff}</b>\n"
            f"Total: <b>${total_price:.2f}</b>\n\n"
            "Do you need delivery?",
            reply_markup=InlineKeyboards.delivery_options()
        )
        
        await state.set_state(BookingStates.choosing_delivery)
        await callback.answer()
    
    else:
        await callback.answer()

# === DELIVERY CHOICE ===
@router.callback_query(BookingStates.choosing_delivery, F.data.in_(["delivery_yes", "delivery_no"]))
async def handle_delivery_choice(callback: CallbackQuery, state: FSMContext):
    """Handle delivery choice"""
    needs_delivery = callback.data == "delivery_yes"
    await state.update_data(delivery_required=needs_delivery)
    
    if needs_delivery:
        await callback.message.edit_text(
            "🚚 Please enter your delivery address:\n\n"
            "(Send /skip if you'll provide it later)"
        )
        await state.set_state(BookingStates.entering_address)
    else:
        await state.update_data(delivery_address=None)
        await ask_for_message(callback.message, state)
    
    await callback.answer()

# === DELIVERY ADDRESS ===
@router.message(BookingStates.entering_address)
async def handle_delivery_address(message: Message, state: FSMContext):
    """Handle delivery address input"""
    if message.text == "/skip":
        await state.update_data(delivery_address="To be provided")
    else:
        await state.update_data(delivery_address=message.text)
    
    await ask_for_message(message, state)

async def ask_for_message(message: Message, state: FSMContext):
    """Ask if user wants to add a message"""
    await message.answer(
        "💬 Would you like to add a message for the owner?\n\n"
        "Send your message or /skip to continue without a message."
    )
    await state.set_state(BookingStates.adding_message)

# === OPTIONAL MESSAGE ===
@router.message(BookingStates.adding_message)
async def handle_optional_message(message: Message, state: FSMContext):
    """Handle optional message"""
    if message.text != "/skip":
        await state.update_data(user_message=message.text)
    else:
        await state.update_data(user_message=None)
    
    # Show booking confirmation
    await show_booking_confirmation(message, state)

async def show_booking_confirmation(message: Message, state: FSMContext):
    """Show booking confirmation"""
    data = await state.get_data()
    
    summary = (
        "📋 <b>Booking Confirmation</b>\n\n"
        f"Tool: <b>{data['tool_name']}</b>\n"
        f"Start: <b>{data['start_date'].strftime('%B %d, %Y')}</b>\n"
        f"End: <b>{data['end_date'].strftime('%B %d, %Y')}</b>\n"
        f"Days: <b>{data['days']}</b>\n"
        f"Total: <b>${data['total_price']:.2f}</b>\n\n"
    )
    
    if data['delivery_required']:
        summary += f"🚚 Delivery: <b>Yes</b>\n"
        if data.get('delivery_address') and data['delivery_address'] != "To be provided":
            summary += f"📍 Address: {data['delivery_address']}\n"
    else:
        summary += "🚚 Delivery: <b>No (pickup)</b>\n"
    
    if data.get('user_message'):
        summary += f"\n💬 Message: {data['user_message'][:100]}..."
    
    await message.answer(
        summary,
        reply_markup=InlineKeyboards.booking_confirmation(data)
    )
    await state.set_state(BookingStates.confirming)

# === CONFIRM BOOKING ===
@router.callback_query(BookingStates.confirming, F.data == "confirm_booking")
async def confirm_booking(callback: CallbackQuery, state: FSMContext):
    """Confirm and save booking"""
    data = await state.get_data()
    user = callback.from_user
    
    async with async_session() as session:
        # Create booking
        booking = Booking(
            user_id=user.id,
            user_username=user.username,
            user_fullname=user.full_name,
            tool_id=data['tool_id'],
            start_date=datetime.combine(data['start_date'], datetime.min.time()),
            end_date=datetime.combine(data['end_date'], datetime.min.time()),
            delivery_required=data['delivery_required'],
            delivery_address=data.get('delivery_address'),
            status=BookingStatus.PENDING,
            total_price=data['total_price']
        )
        session.add(booking)
        await session.flush()
        
        # Add user message if provided
        if data.get('user_message'):
            message = DBMessage(
                user_id=user.id,
                booking_id=booking.id,
                text=data['user_message'],
                is_from_owner=False
            )
            session.add(message)
        
        await session.commit()
        
        # Notify owner
        bot = callback.bot
        owner_text = (
            f"🔔 <b>New Booking Request!</b>\n\n"
            f"Tool: <b>{data['tool_name']}</b>\n"
            f"Customer: {user.full_name} (@{user.username or 'no username'})\n"
            f"Dates: {data['start_date'].strftime('%B %d')} - {data['end_date'].strftime('%B %d, %Y')}\n"
            f"Days: {data['days']}\n"
            f"Total: ${data['total_price']:.2f}\n"
        )
        
        if data['delivery_required']:
            owner_text += f"\n🚚 Delivery requested"
            if data.get('delivery_address'):
                owner_text += f"\n📍 Address: {data['delivery_address']}"
        
        if data.get('user_message'):
            owner_text += f"\n\n💬 Message: {data['user_message']}"
        
        try:
            await bot.send_message(
                config.OWNER_ID,
                owner_text,
                reply_markup=InlineKeyboards.booking_actions(booking, is_owner=True)
            )
        except Exception as e:
            logger.error(f"Failed to notify owner: {e}")
    
    await callback.message.edit_text(
        "✅ <b>Booking confirmed!</b>\n\n"
        f"Your booking request has been sent to the owner.\n"
        f"Booking ID: #{booking.id}\n\n"
        "You'll receive a notification when the owner responds."
    )
    
    await state.clear()
    await callback.answer("Booking confirmed!")

@router.callback_query(BookingStates.confirming, F.data == "cancel_booking")
async def cancel_booking_creation(callback: CallbackQuery, state: FSMContext):
    """Cancel booking creation"""
    await callback.message.edit_text("❌ Booking cancelled.")
    await state.clear()
    await callback.answer()

# Import at the top
from sqlalchemy import func