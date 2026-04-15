import asyncio
import time
from html import escape
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackContext

from shivu import (
    application, 
    user_collection, 
    top_global_groups_collection
)
from shivu.modules.helpers import check_cooldown, get_remaining_cooldown, react_to_message
from shivu.modules.spawn import last_characters, first_correct_guesses, user_guess_progress


# ==============================
#      CORE CAPTURE LOGIC
# ==============================
async def process_successful_guess(update: Update, context: CallbackContext, chat_id: int, user_id: int):
    """Main function to handle database updates and messages when a guess is correct"""
    message = update.message
    today = datetime.utcnow().date()

    first_correct_guesses[chat_id] = user_id

    # Cancel expiry task so it doesn't say "character ran away"
    for task in asyncio.all_tasks():
        if task.get_name() == f"expire_session_{chat_id}":
            task.cancel()
            break

    # Time calculation
    timestamp = last_characters[chat_id].get("timestamp")
    time_taken_str = f"{int(time.time() - timestamp)} seconds" if timestamp else "Unknown"

    # Progress tracking
    if user_id not in user_guess_progress or user_guess_progress[user_id]["date"] != today:
        user_guess_progress[user_id] = {"date": today, "count": 0}
    user_guess_progress[user_id]["count"] += 1

    # User DB update
    user = await user_collection.find_one({"id": user_id})
    update_fields = {"$push": {"characters": last_characters[chat_id]}}
    
    if user:
        old_balance = user.get("balance", 0)
        set_fields = {}
        if message.from_user.username != user.get("username"):
            set_fields["username"] = message.from_user.username
        if message.from_user.first_name != user.get("first_name"):
            set_fields["first_name"] = message.from_user.first_name
        if set_fields:
            update_fields["$set"] = set_fields
    else:
        old_balance = 0
        update_fields["$set"] = {
            "id": user_id,
            "username": message.from_user.username,
            "first_name": message.from_user.first_name,
            "balance": 0
        }

    await user_collection.update_one({"id": user_id}, update_fields, upsert=True)

    # Balance update
    new_balance = old_balance + 40
    await user_collection.update_one({"id": user_id}, {"$set": {"balance": new_balance}})

    # Group Leaderboard update
    if message.chat.type in ["group", "supergroup"]:
        await top_global_groups_collection.update_one(
            {"chat_id": str(message.chat.id)},
            {"$set": {"group_name": message.chat.title}, "$inc": {"count": 1}},
            upsert=True,
        )

    await react_to_message(message.chat.id, message.message_id)

    # Final Simple Message
    response_text = (
        f"<b><a href='tg://user?id={user_id}'>{escape(message.from_user.first_name)}</a></b> "
        f"has captured a character!\n\n"
        f"<b>Name:</b> {last_characters[chat_id]['name']}\n"
        f"<b>Anime:</b> {last_characters[chat_id]['anime']}\n"
        f"<b>Rarity:</b> {last_characters[chat_id]['rarity']}\n"
        f"<b>Time:</b> {time_taken_str}\n\n"
        f"<b>+40 Coins</b> • Balance: <b>{new_balance}</b>"
    )

    keyboard = [[InlineKeyboardButton("See Harem", switch_inline_query_current_chat=f"collection.{user_id}")]]

    await message.reply_text(
        response_text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )

# ==============================
#          /guess COMMAND
# ==============================
async def guess_command(update: Update, context: CallbackContext):
    message = update.message
    chat_id = update.effective_chat.id
    user_id = message.from_user.id

    if chat_id not in last_characters or "name" not in last_characters[chat_id]:
        return await message.reply_text("❌ No active character to guess.")

    if chat_id in first_correct_guesses or last_characters[chat_id].get("ranaway"):
        return await message.reply_text("❌ This character has already been claimed!")

    guess_text = " ".join(context.args).lower().strip() if context.args else ""
    if not guess_text:
        return await message.reply_text("❌ Usage: /guess <name>")

    if "()" in guess_text or "&" in guess_text:
        return await message.reply_text("❌ Invalid characters in guess.")

    correct_name = last_characters[chat_id]["name"].lower()
    name_parts = correct_name.split()

    if sorted(name_parts) == sorted(guess_text.split()) or guess_text in name_parts:
        if await check_cooldown(user_id):
            remaining_time = await get_remaining_cooldown(user_id)
            return await message.reply_text(f"⚠️ You are still in cooldown.\n⏳ Wait {remaining_time} seconds.")
            
        await process_successful_guess(update, context, chat_id, user_id)
    else:
        # Send wrong guess message ONLY if they used a command
        message_id = last_characters[chat_id].get("message_id")
        keyboard = [[InlineKeyboardButton("See Media Again", url=f"https://t.me/c/{str(chat_id)[4:]}/{message_id}")]] if message_id else None
        await message.reply_text("❌ Wrong guess! Try again.", reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)

# ==============================
#    TEXT GUESS (NO COMMAND)
# ==============================
async def text_guess_handler(update: Update, context: CallbackContext):
    message = update.message
    if not message or not message.text:
        return

    chat_id = update.effective_chat.id
    user_id = message.from_user.id

    # Quick exit if no active character
    if chat_id not in last_characters or "name" not in last_characters[chat_id]:
        return
    if chat_id in first_correct_guesses or last_characters[chat_id].get("ranaway"):
        return

    guess_text = message.text.lower().strip()
    
    # Ignore long messages or invalid chars to save processing
    if len(guess_text) > 50 or "()" in guess_text or "&" in guess_text:
        return

    correct_name = last_characters[chat_id]["name"].lower()
    name_parts = correct_name.split()

    # Check if correct guess
    if sorted(name_parts) == sorted(guess_text.split()) or guess_text in name_parts:
        if await check_cooldown(user_id):
            remaining_time = await get_remaining_cooldown(user_id)
            return await message.reply_text(f"⚠️ You are still in cooldown.\n⏳ Wait {remaining_time} seconds.")
            
        await process_successful_guess(update, context, chat_id, user_id)


# ==============================
#          REGISTRATION
# ==============================
application.add_handler(CommandHandler(["guess", "protecc", "collect", "grab", "hunt"], guess_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_guess_handler))
  
