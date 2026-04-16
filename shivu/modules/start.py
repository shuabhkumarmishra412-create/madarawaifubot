import random
import asyncio
import time
import traceback
from html import escape 

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler

from shivu import application, PHOTO_URL, SUPPORT_CHAT, UPDATE_CHAT, BOT_USERNAME, db, GROUP_ID
from shivu import pm_users as collection 


# ------------------ START TIME ------------------ #
START_TIME = time.time()


def get_uptime():
    uptime = int(time.time() - START_TIME)
    h, r = divmod(uptime, 3600)
    m, s = divmod(r, 60)
    return f"{h}h {m}m {s}s"


# ------------------ ANIMATION ------------------ #
async def startup_animation(update: Update, context: CallbackContext):
    try:
        msg = await update.message.reply_text("🔥 Hlo Baby...")
        await asyncio.sleep(0.7)

        await msg.edit_text("❛ Ping Pong... 💗")
        await asyncio.sleep(0.7)

        await msg.edit_text("𓂃 Welcome to Character Catcher 🌸")
        await asyncio.sleep(0.7)

        await msg.delete()
    except Exception:
        pass


# ------------------ START ------------------ #
async def start(update: Update, context: CallbackContext) -> None:
    try:
        user = update.effective_user
        chat = update.effective_chat

        user_id = user.id
        first_name = user.first_name
        username = user.username

        # ---------- DATABASE ----------
        try:
            user_data = await collection.find_one({"_id": user_id})

            if user_data is None:
                await collection.insert_one({
                    "_id": user_id,
                    "first_name": first_name,
                    "username": username
                })

                if GROUP_ID:
                    try:
                        await context.bot.send_message(
                            chat_id=GROUP_ID,
                            text=f"🆕 <b>New User Started!</b>\n👤 <a href='tg://user?id={user_id}'>{escape(first_name)}</a>",
                            parse_mode=ParseMode.HTML
                        )
                    except Exception:
                        pass
            else:
                if user_data.get("first_name") != first_name or user_data.get("username") != username:
                    await collection.update_one(
                        {"_id": user_id},
                        {"$set": {"first_name": first_name, "username": username}}
                    )
        except Exception:
            pass

        # ---------- PRIVATE ----------
        if chat.type == "private":

            await startup_animation(update, context)

            uptime = get_uptime()

            caption = (
                f"<blockquote>"
                f"🍃 <b>Greetings {escape(first_name)}!</b>\n\n"
                f"✨ I am your <b>Character Catcher Bot</b>\n\n"
                f"╭━━━━━━━╾❁✦❁╼━━━━━━━╮\n"
                f"⟡ Spawn anime characters in groups\n"
                f"⟡ Catch using /guess\n"
                f"⟡ Build your harem 💖\n"
                f"╰━━━━━━━╾❁✦❁╼━━━━━━━╯\n\n"
                f"⚡ <b>Uptime:</b> {uptime}\n"
                f"🚀 Add me to your group to start!"
                f"</blockquote>"
            )

            keyboard = [
                [InlineKeyboardButton("✨  ➕ Add Me  ✨", url=f'http://t.me/{BOT_USERNAME}?startgroup=true')],
                [
                    InlineKeyboardButton("💫 Support", url=f'https://t.me/{SUPPORT_CHAT}'),
                    InlineKeyboardButton("🚀 Updates", url=f'https://t.me/{UPDATE_CHAT}')
                ],
                [InlineKeyboardButton("👑 Developer", url="https://t.me/II_YOUR_VILLAIN_II")],
                [InlineKeyboardButton("📖 Help", callback_data='help')]
            ]

            photo_url = random.choice(PHOTO_URL)

            await context.bot.send_photo(
                chat_id=chat.id,
                photo=photo_url,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )

        # ---------- GROUP ----------
        else:
            photo_url = random.choice(PHOTO_URL)

            caption = (
                "<b>🍃 I'm alive!</b>\n\n"
                "I spawn anime characters here.\n"
                "Use /guess to catch them!\n\n"
                "Start me in private for full features."
            )

            keyboard = [
                [
                    InlineKeyboardButton("➕ Add Me", url=f'http://t.me/{BOT_USERNAME}?startgroup=true'),
                    InlineKeyboardButton("Support", url=f'https://t.me/{SUPPORT_CHAT}')
                ]
            ]

            await context.bot.send_photo(
                chat_id=chat.id,
                photo=photo_url,
                caption=caption,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )

    except Exception:
        print(traceback.format_exc())
        await update.message.reply_text("⚠️ Error occurred!")


# ------------------ BUTTON ------------------ #
async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    try:
        if query.data == 'help':
            text = (
                "<b>📚 Help Menu</b>\n\n"
                "🎮 /guess - Catch character\n"
                "📚 /harem - Your collection\n"
                "💖 /fav - Favorite character\n\n"
                "🔁 /trade - Trade\n"
                "🎁 /gift - Gift\n\n"
                "🏆 /top - Leaderboard"
            )

            keyboard = [[InlineKeyboardButton("⬅ Back", callback_data='back')]]

            await query.edit_message_caption(
                caption=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )

        elif query.data == 'back':
            caption = (
                "<b>✨ Character Catcher Bot ✨</b>\n\n"
                "Catch anime characters in groups!\n"
                "Build your harem and compete!"
            )

            keyboard = [
                [InlineKeyboardButton("➕ Add Me", url=f'http://t.me/{BOT_USERNAME}?startgroup=true')],
                [
                    InlineKeyboardButton("Support", url=f'https://t.me/{SUPPORT_CHAT}'),
                    InlineKeyboardButton("Updates", url=f'https://t.me/{UPDATE_CHAT}')
                ],
                [InlineKeyboardButton("Help", callback_data='help')]
            ]

            await query.edit_message_caption(
                caption=caption,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )

    except Exception:
        print(traceback.format_exc())


# ------------------ HANDLERS ------------------ #
application.add_handler(CallbackQueryHandler(button, pattern='^help$|^back$'))
application.add_handler(CommandHandler('start', start))
