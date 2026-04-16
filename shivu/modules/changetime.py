import asyncio
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from telegram.ext import MessageHandler, filters as ptb_filters
from shivu import (
    application,
    group_user_totals_collection,
    collection,
    shivuu,    
)
from pyrogram.enums import ChatMemberStatus
from .spawn import spawn_character, last_characters, first_correct_guesses, user_guess_progress

# Message counters for auto-spawn
message_counters = {}
OWNER_ID = 8441236350
# ==============================
#       Check if user is admin
# ==============================
async def is_admin(update: Update, context: CallbackContext, user_id: int) -> bool:
    chat_id = update.effective_chat.id
    if user_id == OWNER_ID:
        return True
    try:
        member = await shivuu.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception as e:
        print(f"Error checking admin: {e}")
        return False


# ==============================
#       /ctime COMMAND
# ==============================
async def ctime_command(update: Update, context: CallbackContext):
    message = update.message
    chat_id = update.effective_chat.id
    user_id = message.from_user.id

    # Admin or owner check
    is_admin_user = await is_admin(update, context, user_id)
    if not is_admin_user:
        return await message.reply_text("⚠️ Only group admins or bot owner can set changetime!")

    # Parse command argument
    try:
        ctime = int(context.args[0])
    except (IndexError, ValueError):
        return await message.reply_text("⚠️ Please provide a number (e.g., /changetime 80).")

    # Validate ctime based on permissions
    if user_id == OWNER_ID:
        if not 1 <= ctime <= 200:
            return await message.reply_text("⚠️ Bot owner can set changetime between 1 and 200.")
    else:
        if not 80 <= ctime <= 200:
            return await message.reply_text("⚠️ Admins can set changetime between 80 and 200.")

    # Update ctime in MongoDB
    await group_user_totals_collection.update_one(
        {"group_id": str(chat_id)},
        {"$set": {"ctime": ctime}},
        upsert=True
    )

    await message.reply_text(f"✅ Message count threshold set to {ctime} for this group.")


# ==============================
#   Auto-spawn message handler
# ==============================
async def auto_spawn_handler(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    # Increment message counter
    message_counters[chat_id] = message_counters.get(chat_id, 0) + 1

    # Get ctime from DB
    group = await group_user_totals_collection.find_one({"group_id": str(chat_id)})
    ctime = group.get("ctime", 80) if group else 80

    # Check if threshold reached
    if message_counters[chat_id] >= ctime:
        message_counters[chat_id] = 0  # Reset counter
        await spawn_character(update, context)  # Trigger spawn


# ==============================
#       REGISTER HANDLERS
# ==============================
application.add_handler(CommandHandler("ctime", ctime_command))
application.add_handler(
    MessageHandler(ptb_filters.ChatType.GROUPS & ~ptb_filters.COMMAND, auto_spawn_handler)
)
