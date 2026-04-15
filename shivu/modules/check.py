import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext

from shivu import application, collection as character_collection, user_collection

# ============================================================
# /check COMMAND
# ============================================================
async def check_character(update: Update, context: CallbackContext):
    if not context.args:
        return await update.message.reply_text("Use: /check <id>")

    char_id = context.args[0]
    character = await character_collection.find_one({"id": char_id})

    if not character:
        return await update.message.reply_text("❌ Character not found.")

    if character.get("deleted"):
        return await update.message.reply_text(f"📭 Slot `{char_id}` is EMPTY.")

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("📜 Who Have It", callback_data=f"whohaveit_{char_id}")]]
    )
    
    char_name = html.escape(character.get('name', 'Unknown'))
    char_anime = html.escape(character.get('anime', 'Unknown'))
    char_rarity = character.get('rarity', 'Unknown')

    # Default clean layout
    caption = (
        f"🌟 <b>Character Info</b>\n"
        f"🆔 <b>ID:</b> <code>{char_id}</code>\n"
        f"📛 <b>Name:</b> {char_name}\n"
        f"📺 <b>Anime:</b> {char_anime}\n"
        f"💎 <b>Rarity:</b> {char_rarity}\n"
    )

    if character.get("vid_url"):
        await update.message.reply_video(
            character["vid_url"],
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    else:
        await update.message.reply_photo(
            character["img_url"],
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )


# ============================================================
# WHO HAVE IT BUTTON LOGIC
# ============================================================
async def who_have_it(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    char_id = query.data.split("_")[1]
    users = await user_collection.find({"characters.id": char_id}).to_list(length=20)

    if not users:
        return await query.edit_message_caption(
            caption=query.message.caption_html + "\n\n❌ <b>Nobody owns this character yet.</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=query.message.reply_markup
        )

    text = "\n\n🏆 <b>Users Who Own This Character:</b>\n\n"

    for i, user in enumerate(users, start=1):
        count = sum(1 for c in user.get("characters", []) if c.get("id") == char_id)
        name = html.escape(user.get("first_name", "Unknown"))
        uid = user.get("id")
        text += f"{i}. <a href='tg://user?id={uid}'>{name}</a> — x{count}\n"

    await query.edit_message_caption(
        caption=query.message.caption_html + text,
        parse_mode=ParseMode.HTML,
        reply_markup=query.message.reply_markup
    )


# ============================================================
# HANDLERS
# ============================================================
application.add_handler(CommandHandler("check", check_character))
application.add_handler(
    CallbackQueryHandler(who_have_it, pattern=r"^whohaveit_"),
    group=1
)

