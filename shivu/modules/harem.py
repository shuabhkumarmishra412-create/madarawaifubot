import math
import random
from itertools import groupby
from html import escape
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from shivu import shivuu, user_collection, collection

# -------------------------------
# RARITY MAP
# -------------------------------
RARITY_MAP = {
    1: "⛩ Normal",
    2: "🏮 Standard",
    3: "🍀 Regular",
    4: "🔮 Mystic",
    5: "🎐 Eternal",
    6: "👑 Royal",
    7: "🔥 Infernal",
    8: "🎊 Astral",
    9: "🏮 Classic",
    10: "🎭 Mythic",
    11: "🧧 Continental",
    12: "🎈 Chunbiyo"
}

# -------------------------------
# HELPERS
# -------------------------------
async def fetch_user_characters(user_id: int):
    doc = await user_collection.find_one({"id": user_id})
    if not doc or not doc.get("characters"):
        return None, "ʏᴏᴜ ʜᴀᴠᴇ ɴᴏᴛ ᴄʟᴀɪᴍᴇᴅ ᴀɴʏ ᴄʜᴀʀᴀᴄᴛᴇʀꜱ ʏᴇᴛ."

    characters = []
    for c in doc["characters"]:
        if isinstance(c, dict) and c.get("id"):
            characters.append(c)

    if not characters:
        return None, "ɴᴏ ᴠᴀʟɪᴅ ᴄʜᴀʀᴀᴄᴛᴇʀꜱ ꜰᴏᴜɴᴅ ɪɴ ʏᴏᴜʀ ᴄᴏʟʟᴇᴄᴛɪᴏɴ."

    return characters, None

# -------------------------------
# MAIN DISPLAY FUNCTION
# -------------------------------
async def display_harem(
    client,
    message,
    callback_query,
    user_id: int,
    page: int,
    filter_rarity,
    is_initial: bool,
):
    try:
        characters, error = await fetch_user_characters(user_id)
        if error:
            if callback_query:
                await callback_query.answer(error, show_alert=True)
            else:
                await message.reply_text(f"<b>{error}</b>", parse_mode=ParseMode.HTML)
            return

        if filter_rarity:
            characters = [c for c in characters if c.get("rarity") == filter_rarity]

        characters = sorted(
            characters, 
            key=lambda x: (str(x.get("anime") or ""), str(x.get("id") or ""))
        )

        character_counts = {}
        for k, g in groupby(characters, key=lambda x: x["id"]):
            character_counts[k] = len(list(g))

        unique_characters = list({c["id"]: c for c in characters}.values())

        total_pages = max(1, math.ceil(len(unique_characters) / 15))
        page = max(0, min(page, total_pages - 1))

        display_name = (
            callback_query.from_user.first_name
            if callback_query
            else message.from_user.first_name
        )

        harem_msg = (
            f"<b>|| {escape(display_name)}'s Harem ||</b>\n"
            f"<b>Page:</b> {page+1}/{total_pages}\n"
            f"<b>Total Collection:</b> {len(unique_characters)}\n"
        )

        if filter_rarity:
            harem_msg += f"<b>Filtered by:</b> {escape(str(filter_rarity))}\n"

        current_chars = unique_characters[page * 15 : (page + 1) * 15]

        grouped = {}
        for c in current_chars:
            anime = c.get("anime") or "Unknown"
            grouped.setdefault(anime, []).append(c)

        for anime, chars in grouped.items():
            total_in_anime = (
                await collection.count_documents({"anime": anime})
                if anime != "Unknown"
                else 0
            )
            harem_msg += f"\n<b>{escape(str(anime))} {len(chars)}/{total_in_anime}</b>\n"

            for character in chars:
                rarity = character.get("rarity") or "Unknown"
                count = character_counts.get(character["id"], 1)
                cid = escape(str(character.get("id")))
                cname = escape(str(character.get("name") or "Unknown"))
                harem_msg += f"◈⌠{rarity}⌡ {cid} {cname} ×{count}\n"

        # Buttons (Simplified)
        keyboard = [
            [
                InlineKeyboardButton("Collection", switch_inline_query_current_chat=f"collection.{user_id}"),
                InlineKeyboardButton("Animation", switch_inline_query_current_chat=f"collection.{user_id}.AMV"),
            ],
            [
                InlineKeyboardButton("ᴄʜᴇᴄᴋ ɴᴏᴡ", url="http://t.me/Waifu_catcherbot/Waifu")
            ]
        ]

        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("⬅️ Back", callback_data=f"harem:{page-1}:{user_id}:{filter_rarity or 'None'}"))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"harem:{page+1}:{user_id}:{filter_rarity or 'None'}"))
        
        if nav:
            keyboard.append(nav)

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Media Logic
        user_doc = await user_collection.find_one({"id": user_id})
        fav = None

        if user_doc and user_doc.get("favorites"):
            fav_id = user_doc["favorites"][0]
            fav = next((c for c in characters if str(c["id"]) == str(fav_id)), None)
            if not fav:
                fav = await collection.find_one({"id": fav_id})

        preview = (
            fav
            or next((c for c in characters if c.get("vid_url")), None)
            or next((c for c in characters if c.get("img_url")), None)
            or random.choice(characters) if characters else None
        )

        if is_initial:
            try:
                if preview and preview.get("vid_url"):
                    return await message.reply_video(video=preview["vid_url"], caption=harem_msg, reply_markup=reply_markup)
                elif preview and preview.get("img_url"):
                    return await message.reply_photo(photo=preview["img_url"], caption=harem_msg, reply_markup=reply_markup)
            except Exception:
                pass 

            return await message.reply_text(text=harem_msg, reply_markup=reply_markup)

        if callback_query.message.photo or callback_query.message.video or callback_query.message.animation:
            try:
                await callback_query.message.edit_caption(caption=harem_msg, reply_markup=reply_markup)
            except Exception:
                await callback_query.message.edit_text(text=harem_msg, reply_markup=reply_markup)
        else:
            await callback_query.message.edit_text(text=harem_msg, reply_markup=reply_markup)

    except Exception as e:
        error_msg = f"⚠️ <b>Error loading collection:</b>\n<code>{escape(str(e))}</code>"
        if callback_query:
            try:
                await callback_query.message.reply_text(error_msg, parse_mode=ParseMode.HTML)
            except: pass
        elif message:
            try:
                await message.reply_text(error_msg, parse_mode=ParseMode.HTML)
            except: pass

# -------------------------------
# COMMANDS & CALLBACKS
# -------------------------------
@shivuu.on_message(filters.command(["harem", "collection"]))
async def harem_command(client, message):
    user_id = message.from_user.id
    user_doc = await user_collection.find_one({"id": user_id})
    filter_rarity = user_doc.get("filter_rarity") if user_doc else None

    await display_harem(client, message, None, user_id, 0, filter_rarity, True)


@shivuu.on_callback_query(filters.regex(r"^harem:"))
async def harem_callback(client, callback_query):
    await callback_query.answer()
    _, page, uid, rarity = callback_query.data.split(":")
    
    if callback_query.from_user.id != int(uid):
        return await callback_query.answer("Not your harem!", show_alert=True)

    await display_harem(client, callback_query.message, callback_query, int(uid), int(page), None if rarity == "None" else rarity, False)


RARITIES = [
    {"name": "Normal", "key": "⛩ Normal"},
    {"name": "Standard", "key": "🏮 Standard"},
    {"name": "Regular", "key": "🍀 Regular"},
    {"name": "Mystic", "key": "🔮 Mystic"},
    {"name": "Eternal", "key": "🎐 Eternal"},
    {"name": "Royal", "key": "👑 Royal"},
    {"name": "Infernal", "key": "🔥 Infernal"},
    {"name": "Astral", "key": "🎊 Astral"},
    {"name": "Classic", "key": "🏮 Classic"},
    {"name": "Mythic", "key": "🎭 Mythic"},
    {"name": "Continental", "key": "🧧 Continental"},
    {"name": "Chunbiyo", "key": "🎈 Chunbiyo"},
]


@shivuu.on_message(filters.command("wmode"))
async def wmode_command(client, message):
    user_id = message.from_user.id
    args = message.command[1:]

    if args:
        rarity_input = args[0].title()
        valid_rarity = next((r for r in RARITIES if r["key"].lower() == rarity_input.lower()), None)
        
        if valid_rarity:
            await user_collection.update_one({"id": user_id}, {"$set": {"filter_rarity": valid_rarity["key"]}}, upsert=True)
            return await message.reply_text(f"✅ Filter set to: {valid_rarity['key']}")
        else:
            return await message.reply_text("❌ Invalid Rarity. Please use the menu.")

    keyboard = []
    row = []
    
    for rarity in RARITIES:
        row.append(InlineKeyboardButton(text=rarity["name"], callback_data=f"set_rarity:{user_id}:{rarity['key']}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
            
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="❌ Clear Filter (All)", callback_data=f"set_rarity:{user_id}:None")])

    await message.reply_text("<b>🎯 Select Rarity to Filter:</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)


@shivuu.on_callback_query(filters.regex(r"^set_rarity:"))
async def set_rarity_callback(client, callback_query):
    _, uid, key = callback_query.data.split(":")
    
    if callback_query.from_user.id != int(uid):
        return await callback_query.answer("❌ This menu is not for you!", show_alert=True)

    rarity_to_set = None if key == "None" else key
    
    await user_collection.update_one({"id": int(uid)}, {"$set": {"filter_rarity": rarity_to_set}}, upsert=True)

    if rarity_to_set:
        await callback_query.message.edit_text(f"✅ <b>Filter updated!</b>\n🔮 Current Filter: {rarity_to_set}", parse_mode=ParseMode.HTML)
    else:
        await callback_query.message.edit_text("✅ <b>Filter cleared! Showing all rarities.</b>", parse_mode=ParseMode.HTML)
            
