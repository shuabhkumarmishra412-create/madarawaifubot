import time

# Simple cooldown storage
cooldowns = {}

def check_cooldown(user_id, cooldown_time):
    now = time.time()
    if user_id in cooldowns:
        if now - cooldowns[user_id] < cooldown_time:
            return False
    cooldowns[user_id] = now
    return True

def get_remaining_cooldown(user_id, cooldown_time):
    now = time.time()
    if user_id in cooldowns:
        remaining = cooldown_time - (now - cooldowns[user_id])
        return max(0, int(remaining))
    return 0

async def react_to_message(message, emoji="👍"):
    try:
        await message.react(emoji)
    except Exception:
        pass
