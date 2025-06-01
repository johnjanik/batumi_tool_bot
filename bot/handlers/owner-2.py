"""
Owner tool management handlers (continuation of owner.py)
Add this content to the end of owner.py
"""

# === LIST TOOLS ===
@router.message(Command("listtools"))
@router.callback_query(F.data == "list_tools")
async def list_owner_tools(update: Message | CallbackQuery):
    """List all tools for owner"""
    async with async_session() as session:
        result = await session.execute(select(Tool).order_by(Tool.id))
        tools = result.scalars().all()
        
        if not tools:
            text = "📭 No tools in the catalog yet.\n\nUse /addtool to add your first tool!"
        else:
            text = "📋 <b>Your Tools Catalog:</b>\n\n"
            for tool in tools:
                status = "✅ Available" if tool.available else "❌ Unavailable"
                text += (
                    f"<b>#{tool.id} - {tool.name}</b>\n"
                    f"Price: ${tool.price_per_day}/day\n"
                    f"Status: {status}\n"
                    f"Photos: {len(tool.image_ids)}\n\n"
                )
        
        if isinstance(update, CallbackQuery):
            await update.message.answer(text)
            await update.answer()
        else:
            await update.answer(text)

# === VIEW BOOKINGS ===
@router.callback_query(F.data == "view_bookings")
async def view_all_bookings(callback: CallbackQuery):
    """View all bookings"""
    async with async_session() as session:
        result = await session.execute(
            select(Booking)
            .options(selectinload(Booking.tool))
            .order_by(Booking.created_at.desc())
            .limit(20)
        )
        bookings = result.scalars().all()
        
        if not bookings:
            await callback.message.answer("📭 No bookings yet.")
            await callback.answer()
            return
        
        text = "📊 <b>Recent Bookings:</b>\n\n"
        for booking in bookings:
            status_emoji = {
                BookingStatus.PENDING: "⏳",
                BookingStatus.CONFIRMED: "✅",
                BookingStatus.CANCELLED: "❌",
                BookingStatus.COMPLETED: "✔️"
            }
            
            text += (
                f"{status_emoji.get(booking.status, '❓')} <b>Booking #{booking.id}</b>\n"
                f"Tool: {booking.tool.name}\n"
                f"Customer: {booking.user_fullname or 'Unknown'}\n"
                f"Dates: {booking.start_date.strftime('%Y-%m-%d')} to {booking.end_date.strftime('%Y-%m-%d')}\n"
                f"Total: ${booking.total_price:.2f}\n"
                f"Status: {booking.status.value}\n\n"
            )
        
        await callback.message.answer(text)
        await callback.answer()

# === STATISTICS ===
@router.callback_query(F.data == "stats")
async def show_statistics(callback: CallbackQuery):
    """Show rental statistics"""
    async with async_session() as session:
        # Get tool count
        tool_count = await session.scalar(select(func.count(Tool.id)))
        
        # Get booking stats
        total_bookings = await session.scalar(select(func.count(Booking.id)))
        
        # Get bookings by status
        pending = await session.scalar(
            select(func.count(Booking.id))
            .where(Booking.status == BookingStatus.PENDING)
        )
        confirmed = await session.scalar(
            select(func.count(Booking.id))
            .where(Booking.status == BookingStatus.CONFIRMED)
        )
        completed = await session.scalar(
            select(func.count(Booking.id))
            .where(Booking.status == BookingStatus.COMPLETED)
        )
        
        # Get revenue
        total_revenue = await session.scalar(
            select(func.sum(Booking.total_price))
            .where(Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED]))
        ) or 0
        
        # Get this month's stats
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        monthly_bookings = await session.scalar(
            select(func.count(Booking.id))
            .where(Booking.created_at >= start_of_month)
        )
        monthly_revenue = await session.scalar(
            select(func.sum(Booking.total_price))
            .where(
                Booking.created_at >= start_of_month,
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED])
            )
        ) or 0
        
        text = (
            "📈 <b>ToolBot Statistics</b>\n\n"
            f"🛠 <b>Tools:</b> {tool_count}\n\n"
            f"📊 <b>All-Time Bookings:</b>\n"
            f"• Total: {total_bookings}\n"
            f"• Pending: {pending}\n"
            f"• Confirmed: {confirmed}\n"
            f"• Completed: {completed}\n\n"
            f"💰 <b>Revenue:</b>\n"
            f"• All-time: ${total_revenue:.2f}\n"
            f"• This month: ${monthly_revenue:.2f}\n"
            f"• Monthly bookings: {monthly_bookings}\n"
        )
        
        await callback.message.answer(text)
        await callback.answer()

# === TOGGLE AVAILABILITY ===
@router.callback_query(F.data.startswith("toggle_availability:"))
async def toggle_tool_availability(callback: CallbackQuery):
    """Toggle tool availability"""
    tool_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        tool = await session.get(Tool, tool_id)
        if not tool:
            await callback.answer("Tool not found!", show_alert=True)
            return
        
        tool.available = not tool.available
        await session.commit()
        
        status = "available" if tool.available else "unavailable"
        await callback.answer(f"Tool marked as {status}!")
        
        # Refresh the tool details
        await callback.message.edit_reply_markup(
            reply_markup=InlineKeyboards.tool_details(tool, is_owner=True)
        )

# === DELETE TOOL ===
@router.message(Command("deltool"))
@router.callback_query(F.data == "delete_tool")
async def start_delete_tool(update: Message | CallbackQuery, state: FSMContext):
    """Start tool deletion process"""
    async with async_session() as session:
        result = await session.execute(select(Tool).order_by(Tool.id))
        tools = result.scalars().all()
        
        if not tools:
            text = "No tools to delete."
            if isinstance(update, CallbackQuery):
                await update.message.answer(text)
                await update.answer()
            else:
                await update.answer(text)
            return
        
        text = "Select a tool to delete:\n\n"
        for tool in tools:
            text += f"/del_{tool.id} - {tool.name}\n"
        
        if isinstance(update, CallbackQuery):
            await update.message.answer(text)
            await update.answer()
        else:
            await update.answer(text)
        
        await state.set_state(DeleteToolStates.selecting_tool)

@router.message(DeleteToolStates.selecting_tool, F.text.startswith("/del_"))
async def confirm_delete_tool(message: Message, state: FSMContext):
    """Confirm tool deletion"""
    try:
        tool_id = int(message.text.split("_")[1])
    except (IndexError, ValueError):
        await message.answer("Invalid tool ID. Please try again.")
        return
    
    async with async_session() as session:
        tool = await session.get(Tool, tool_id)
        if not tool:
            await message.answer("Tool not found.")
            return
        
        # Check for active bookings
        active_bookings = await session.scalar(
            select(func.count(Booking.id))
            .where(
                Booking.tool_id == tool_id,
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
            )
        )
        
        warning = ""
        if active_bookings > 0:
            warning = f"\n\n⚠️ WARNING: This tool has {active_bookings} active bookings!"
        
        await state.update_data(tool_id=tool_id)
        await message.answer(
            f"Are you sure you want to delete:\n\n"
            f"<b>{tool.name}</b>\n"
            f"Price: ${tool.price_per_day}/day{warning}",
            reply_markup=InlineKeyboards.confirm_delete()
        )
        await state.set_state(DeleteToolStates.confirming)

@router.callback_query(DeleteToolStates.confirming, F.data == "confirm_delete")
async def execute_delete_tool(callback: CallbackQuery, state: FSMContext):
    """Execute tool deletion"""
    data = await state.get_data()
    tool_id = data.get('tool_id')
    
    async with async_session() as session:
        tool = await session.get(Tool, tool_id)
        if tool:
            tool_name = tool.name
            await session.delete(tool)
            await session.commit()
            
            await callback.message.edit_text(f"✅ Tool '{tool_name}' has been deleted.")
        else:
            await callback.message.edit_text("❌ Tool not found.")
    
    await state.clear()
    await callback.answer("Tool deleted!")

@router.callback_query(DeleteToolStates.confirming, F.data == "cancel_delete")
async def cancel_delete_tool(callback: CallbackQuery, state: FSMContext):
    """Cancel tool deletion"""
    await callback.message.edit_text("❌ Deletion cancelled.")
    await state.clear()
    await callback.answer()

# Import this at the top of owner.py:
from sqlalchemy.orm import selectinload