import html
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext

from shivu import application, user_collection, top_global_groups_collection

PHOTO_URL = ["https://files.catbox.moe/9j8e6b.jpg"]

# ==========================================================
#                    BADGE SYSTEM
# ==========================================================
def get_badge(rank: int, total: int):
    if total <= 0:
        return "", ""
    if rank == 1:
        return "🥇", "Champion"
    if rank == 2:
        return "🥈", "2nd Place"
    if rank == 3:
        return "🥉", "3rd Place"
    if rank <= 10:
        return "🏅", f"Top {rank}"

    pct = rank / total
    if pct <= 0.01:
        return "💎", "Top 1%"
    if pct <= 0.05:
        return "🔷", "Top 5%"
    if pct <= 0.10:
        return "🔹", "Top 10%"
    return "", ""

# ==========================================================
#               SAFE NAME BUILDER
# ==========================================================
def format_name(user):
    if user.get("first_name"):
        name = html.escape(user["first_name"])
    elif user.get("username"):
        name = "@" + html.escape(user["username"])
    else:
        name = f"User {user.get('id')}"

    # Limit name length to keep leaderboard clean
    if len(name) > 15:
        name = name[:15] + "..."

    return name

# ==========================================================
#                LEADERBOARD BUILDERS
# ==========================================================
def build_user_leaderboard(data):
    total = len(data)
    caption = "<b>🏆 TOP 10 USERS (CHARACTERS)</b>\n\n"

    for i, user in enumerate(data, start=1):
        uid = user.get("id")
        name = format_name(user)
        count = len(user.get("characters", []))
        badge, _ = get_badge(i, total)

        caption += f"{i}. {badge} <a href='tg://user?id={uid}'><b>{name}</b></a> ➜ <b>{count}</b>\n"
    return caption

def build_group_leaderboard(data):
    caption = "<b>🏆 TOP 10 GROUPS</b>\n\n"

    for i, group in enumerate(data, start=1):
        # Group name priority
        name = group.get("group_name") or group.get("title") or group.get("name") or f"Group {i}"
        name = html.escape(str(name))
        
        if len(name) > 15:
            name = name[:15] + "..."

        # Support all possible count fields
        count = group.get("count") or group.get("total") or group.get("score") or 0
        badge, _ = get_badge(i, len(data))

        caption += f"{i}. {badge} <b>{name}</b> ➜ <b>{count}</b>\n"
    return caption

def build_coin_leaderboard(data):
    total = len(data)
    caption = "<b>🏆 TOP 10 RICHEST USERS</b>\n\n"

    for i, user in enumerate(data, start=1):
        uid = user.get("id")
        name = format_name(user)
        coins = user.get("balance", 0)
        badge, _ = get_badge(i, total)

        caption += f"{i}. {badge} <a href='tg://user?id={uid}'><b>{name}</b></a> ➜ <b>{coins}</b>\n"
    return caption

def build_challenge_leaderboard(data):
    total = len(data)
    caption = "<b>🏆 TOP 10 CHALLENGERS</b>\n\n"

    for i, user in enumerate(data, start=1):
        uid = user.get("id")
        name = format_name(user)
        wins = user.get("wins", 0)
        badge, _ = get_badge(i, total)

        caption += f"{i}. {badge} <a href='tg://user?id={uid}'><b>{name}</b></a> ➜ <b>{wins} Wins</b>\n"
    return caption

# ==========================================================
#                     BUTTONS
# ==========================================================
def get_buttons(active):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("👤 Users" if active == "top" else "Users", callback_data="top"),
                InlineKeyboardButton("👥 Groups" if active == "top_group" else "Groups", callback_data="top_group"),
            ],
            [
                InlineKeyboardButton("💰 Richest" if active == "mtop" else "Richest", callback_data="mtop"),
                InlineKeyboardButton("⚔️ Challengers" if active == "ctop" else "Challengers", callback_data="ctop"),
            ],
        ]
    )

# ==========================================================
#                        /rank COMMAND
# ==========================================================
async def rank_cmd(update: Update, context: CallbackContext):
    cursor = user_collection.find({}, {"_id": 0, "id": 1, "first_name": 1, "username": 1, "characters": 1})
    data = await cursor.to_list(length=None)

    data.sort(key=lambda x: len(x.get("characters", [])), reverse=True)
    top_users = data[:10]

    caption = build_user_leaderboard(top_users)

    await update.message.reply_photo(
        photo=random.choice(PHOTO_URL),
        caption=caption,
        parse_mode="HTML",
        reply_markup=get_buttons("top"),
    )

# ==========================================================
#                 BUTTON HANDLER
# ==========================================================
async def leaderboard_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    btn = query.data

    if btn == "top":
        cursor = user_collection.find({}, {"_id": 0, "id": 1, "first_name": 1, "username": 1, "characters": 1})
        data = await cursor.to_list(length=None)
        data.sort(key=lambda x: len(x.get("characters", [])), reverse=True)
        caption = build_user_leaderboard(data[:10])

    elif btn == "top_group":
        cursor = top_global_groups_collection.aggregate([
            {"$project": {"group_name": 1, "title": 1, "count": 1}},
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ])
        data = await cursor.to_list(length=10)
        caption = build_group_leaderboard(data)

    elif btn == "mtop":
        cursor = user_collection.find({}, {"_id": 0, "id": 1, "first_name": 1, "username": 1, "balance": 1})
        data = await cursor.to_list(length=None)
        data.sort(key=lambda x: x.get("balance", 0), reverse=True)
        caption = build_coin_leaderboard(data[:10])

    elif btn == "ctop":
        cursor = user_collection.find({}, {"_id": 0, "id": 1, "first_name": 1, "username": 1, "wins": 1})
        data = await cursor.to_list(length=None)
        data.sort(key=lambda x: x.get("wins", 0), reverse=True)
        caption = build_challenge_leaderboard(data[:10])

    await query.message.edit_caption(caption, parse_mode="HTML", reply_markup=get_buttons(btn))

# ==========================================================
#                        /profile COMMAND
# ==========================================================
async def profile_cmd(update: Update, context: CallbackContext):
    message = update.message

    if message.reply_to_message:
        target = message.reply_to_message.from_user
    else:
        parts = message.text.split()
        target = None
        if len(parts) >= 2:
            try:
                if parts[1].startswith("@"):
                    target = await context.bot.get_chat(parts[1])
                else:
                    target = await context.bot.get_chat(int(parts[1]))
            except Exception:
                return await message.reply_text("❌ Invalid username or ID.")

    if not target:
        target = message.from_user

    uid = target.id

    user_doc = await user_collection.find_one(
        {"id": uid},
        {"_id": 0, "first_name": 1, "username": 1, "characters": 1, "balance": 1, "wins": 1},
    )

    if not user_doc:
        return await message.reply_text("❌ User not found in Database.")

    # Calculate global rank based on character count
    cursor = user_collection.find({}, {"_id": 0, "id": 1, "characters": 1})
    all_users = await cursor.to_list(length=None)
    all_users.sort(key=lambda x: len(x.get("characters", [])), reverse=True)

    total = len(all_users)
    rank = next((i for i, u in enumerate(all_users, start=1) if u["id"] == uid), 0)

    badge, label = get_badge(rank, total)

    characters = len(user_doc.get("characters", []))
    balance = user_doc.get("balance", 0)
    wins = user_doc.get("wins", 0)

    caption = (
        f"👤 <b>{html.escape(target.first_name)}'s Profile</b>\n\n"
        f"🏅 <b>Rank:</b> #{rank} / {total}\n"
        f"🎖 <b>Title:</b> {badge} {label}\n"
        f"🧾 <b>Characters:</b> {characters}\n"
        f"💰 <b>Balance:</b> {balance} Coins\n"
        f"⚔️ <b>Duels Won:</b> {wins}"
    )

    await message.reply_text(caption, parse_mode="HTML")

# ==========================================================
#              REGISTER HANDLERS
# ==========================================================
application.add_handler(CommandHandler("rank", rank_cmd))
application.add_handler(CommandHandler("profile", profile_cmd))
application.add_handler(CallbackQueryHandler(leaderboard_buttons, pattern="^(top|top_group|mtop|ctop)$"))
                  
