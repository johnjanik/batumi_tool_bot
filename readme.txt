Now I need to make sure the __init__.py files are set up correctly to export the routers:
Now let's fix the main.py imports:Now make sure you have created all these files in your project:

1. **Replace the content of `bot/handlers/owner.py`** with the complete version from the artifact
 `toolbot-complete-owner-handlers`

2. **Replace the content of `bot/handlers/user.py`** with the complete version from the artifact
 `toolbot-complete-user-handlers`

3. **Replace the content of `bot/handlers/__init__.py`** with the content from the artifact
 `toolbot-handlers-init`

4. **Make sure `bot/handlers/user_bookings.py` content is added to the end of `user.py`**
 (it's already included in the complete version)

5. **Restart your bot:**
   ```bash
   # Stop the bot (Ctrl+C)
   # Make sure virtual environment is active
   source venv/bin/activate
   # Start again
   python main.py
   ```

Now all buttons should work:

**Owner Panel:**
- ✅ Add Tool - Add new tools with photos
- ✅ List Tools - View all your tools
- ✅ Edit Tool - Edit tool details (functionality included but simplified)
- ✅ Delete Tool - Delete tools with confirmation
- ✅ View Bookings - See all booking requests
- ✅ Statistics - View revenue and booking stats

**User Menu:**
- ✅ Browse Tools - View available tools with pagination
- ✅ My Bookings - View your bookings with details
- ✅ Contact Owner - Send messages to the owner
- ✅ Help - Show help information

Test each button and let me know if you encounter any specific errors!