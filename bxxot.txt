import telebot
from telebot import types
import random
from datetime import date, datetime

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = "8978005144:AAH3uykYkjLNfAC-lEgmGa3FJrezq38qUp4"
ADMIN_ID = 7723971526

bot = telebot.TeleBot(BOT_TOKEN)

# =========================================================
# TEMP DATA
# =========================================================

users = {}
waiting_users = []
active_chats = {}
reports = []

# chat_logs:
# {
#   chat_id: [
#       {
#           "sender": user_id,
#           "receiver": user_id,
#           "text": "...",
#           "time": "..."
#       }
#   ]
# }
chat_logs = {}

# =========================================================
# RANKS
# =========================================================

RANKS = {
    "Bronze": {
        "price": 0,
        "chat_limit": 1,
        "color": "🥉",
        "description": "رتبه پایه"
    },
    "Silver": {
        "price": 500,
        "chat_limit": 2,
        "color": "🥈",
        "description": "امکان چت بهتر"
    },
    "Gold": {
        "price": 1500,
        "chat_limit": 3,
        "color": "🥇",
        "description": "بازی‌ها و امکانات بیشتر"
    },
    "Diamond": {
        "price": 3000,
        "chat_limit": 5,
        "color": "💎",
        "description": "امکانات ویژه"
    },
    "VIP": {
        "price": 7000,
        "chat_limit": 10,
        "color": "👑",
        "description": "دسترسی ویژه"
    }
}

# =========================================================
# SHOP
# =========================================================

SHOP_ITEMS = {
    "frame": {
        "name": "🖼 قاب پروفایل",
        "price": 1000
    },
    "badge": {
        "name": "🏅 مدال ویژه",
        "price": 1500
    },
    "color_name": {
        "name": "✨ نام ویژه",
        "price": 2000
    },
    "double_xp": {
        "name": "⚡ دو برابر XP",
        "price": 3000
    }
}

# =========================================================
# USER
# =========================================================

def generate_code():
    used = {u["code"] for u in users.values()}

    for i in range(1, 100001):
        code = f"{i:04d}"

        if code not in used:
            return code

    return None


def create_user(user_id, name):

    if user_id in users:
        return True

    code = generate_code()

    if code is None:
        return False

    users[user_id] = {
        "id": user_id,
        "name": name,
        "code": code,

        "rank": "Bronze",

        "level": 1,
        "xp": 0,

        "coins": 100,
        "balance": 0,

        "streak": 1,
        "last_daily": str(date.today()),

        "messages": 0,
        "chats": 0,

        "referrals": 0,

        "banned": False,

        "anonymous": True,

        "items": [],

        "missions": {
            "messages": 0,
            "games": 0,
            "chats": 0
        }
    }

    return True


def get_user(user_id):
    return users.get(user_id)


def is_admin(user_id):
    return user_id == ADMIN_ID


def is_banned(user_id):
    return user_id in users and users[user_id]["banned"]


# =========================================================
# BAN CHECK
# =========================================================

def blocked(message):
    user_id = message.from_user.id

    if is_admin(user_id):
        return False

    if is_banned(user_id):
        bot.send_message(
            message.chat.id,
            "🚫 حساب شما مسدود است.\n\n"
            "تا زمانی که مدیریت شما را از بن خارج نکند، "
            "امکان استفاده از بات را ندارید."
        )
        return True

    return False


# =========================================================
# XP
# =========================================================

def xp_needed(level):
    return level * 250


def add_xp(user_id, amount):

    user = get_user(user_id)

    if not user:
        return

    if "double_xp" in user["items"]:
        amount *= 2

    user["xp"] += amount

    while user["xp"] >= xp_needed(user["level"]):

        user["xp"] -= xp_needed(user["level"])
        user["level"] += 1

        reward = user["level"] * 100
        user["coins"] += reward

        try:
            bot.send_message(
                user_id,
                f"🎉 LEVEL UP!\n\n"
                f"⭐ Level {user['level']}\n"
                f"🪙 +{reward} سکه"
            )
        except:
            pass


# =========================================================
# RANK FEATURES
# =========================================================

def rank_limit(user):
    return RANKS[user["rank"]]["chat_limit"]


def rank_text(rank):
    data = RANKS.get(rank, RANKS["Bronze"])

    return (
        f"{data['color']} {rank}\n"
        f"✨ {data['description']}"
    )


# =========================================================
# MAIN KEYBOARD
# =========================================================

def main_keyboard(user_id):

    kb = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    kb.row(
        "👤 پروفایل",
        "💬 چت"
    )

    kb.row(
        "🎮 بازی‌ها",
        "🎯 مأموریت‌ها"
    )

    kb.row(
        "🛒 فروشگاه",
        "🪙 کیف پول"
    )

    kb.row(
        "🏆 رتبه‌بندی",
        "🎁 جوایز"
    )

    kb.row(
        "✏️ تغییر نام",
        "👥 دعوت دوستان"
    )

    kb.row(
        "⚙️ تنظیمات",
        "🗑 حذف حساب"
    )

    if user_id == ADMIN_ID:
        kb.row("👑 مدیریت")

    return kb


# =========================================================
# START
# =========================================================

@bot.message_handler(commands=["start"])
def start(message):

    user_id = message.from_user.id

    # مهم:
    # کاربر بن شده حتی با /start هم اجازه ندارد
    if is_banned(user_id):

        bot.send_message(
            message.chat.id,
            "🚫 حساب شما مسدود است."
        )

        return

    is_new = user_id not in users

    if not create_user(
        user_id,
        message.from_user.first_name or "کاربر"
    ):
        bot.send_message(
            message.chat.id,
            "❌ ظرفیت ثبت‌نام تکمیل شده است."
        )
        return

    user = users[user_id]

    # daily
    today = str(date.today())

    if not is_new and user["last_daily"] != today:

        user["last_daily"] = today
        user["streak"] += 1

        user["coins"] += 50

        add_xp(user_id, 20)

        bot.send_message(
            message.chat.id,
            f"🎁 پاداش روزانه\n\n"
            f"🪙 +50 سکه\n"
            f"⭐ +20 XP\n"
            f"🔥 استریک: {user['streak']}"
        )

    if is_new:

        bot.send_message(
            message.chat.id,
            f"""
🎉 خوش اومدی به «چت ناشناس»!

🆔 کد کاربری شما:
{user['code']}

🕵️ حالت ناشناس به صورت پیش‌فرض فعاله.

از منوی پایین می‌تونی:
💬 چت کنی
🎮 بازی کنی
🎯 مأموریت انجام بدی
🛒 خرید کنی
🏆 رتبه بگیری
"""
        )

    bot.send_message(
        message.chat.id,
        "🏠 منوی اصلی",
        reply_markup=main_keyboard(user_id)
    )


# =========================================================
# HELP / COMMANDS
# =========================================================

@bot.message_handler(commands=["help", "commands"])
def help_command(message):

    if blocked(message):
        return

    text = """
📚 دستورات «چت ناشناس»

/start
🚀 شروع ربات

/help
📚 لیست دستورات

/profile
👤 پروفایل

/chat
💬 چت

/end
🛑 پایان چت

/report
🚨 گزارش کاربر

/games
🎮 بازی‌ها

/missions
🎯 مأموریت‌ها

/shop
🛒 فروشگاه

/wallet
🪙 کیف پول

/rank
🏆 رتبه من

/leaderboard
🏆 رتبه‌بندی

/name
✏️ تغییر نام

/anonymous
🕵️ حالت ناشناس

/normal
👤 حالت عادی

/delete
🗑 حذف حساب

/ranks
👑 توضیح رتبه‌ها

/commands
📚 همین لیست
"""

    if is_admin(message.from_user.id):

        text += """
        
👑 دستورات مدیریت

/admin
👑 پنل مدیریت

/stats
📊 آمار

/logs
💬 لاگ چت‌ها
"""

    bot.send_message(
        message.chat.id,
        text
    )


# =========================================================
# PROFILE
# =========================================================

@bot.message_handler(commands=["profile"])
@bot.message_handler(func=lambda m: m.text == "👤 پروفایل")
def profile(message):

    if blocked(message):
        return

    user = get_user(message.from_user.id)

    if not user:
        start(message)
        return

    needed = xp_needed(user["level"])

    progress = int(
        user["xp"] / needed * 10
    )

    progress = min(progress, 10)

    bar = (
        "🟦" * progress
        + "⬜" * (10 - progress)
    )

    mode = (
        "🕵️ ناشناس"
        if user["anonymous"]
        else "👤 عادی"
    )

    items = ", ".join(user["items"]) if user["items"] else "نداری"

    text = f"""
╭━━━━━━━━━━━━━━╮
       👤 پروفایل
╰━━━━━━━━━━━━━━╯

👤 نام: {user['name']}
🆔 ID: {user['code']}

🏷 رتبه: {RANKS[user['rank']]['color']} {user['rank']}
⭐ Level: {user['level']}

✨ XP: {user['xp']} / {needed}
{bar}

🪙 سکه: {user['coins']}
💰 موجودی: {user['balance']:,} تومان

🔥 استریک: {user['streak']} روز

💬 چت‌ها: {user['chats']}
📨 پیام‌ها: {user['messages']}

🕵️ حالت: {mode}

🎁 آیتم‌ها:
{items}
"""

    bot.send_message(
        message.chat.id,
        text
    )


# =========================================================
# WALLET
# =========================================================

@bot.message_handler(commands=["wallet"])
@bot.message_handler(func=lambda m: m.text == "🪙 کیف پول")
def wallet(message):

    if blocked(message):
        return

    user = get_user(message.from_user.id)

    bot.send_message(
        message.chat.id,
        f"""
🪙 کیف پول

💰 موجودی:
{user['balance']:,} تومان

🪙 سکه:
{user['coins']}

🎁 آیتم‌ها:
{len(user['items'])}
"""
    )


# =========================================================
# RANKS
# =========================================================

@bot.message_handler(commands=["ranks"])
def ranks_command(message):

    if blocked(message):
        return

    text = "👑 رتبه‌ها\n\n"

    for rank, data in RANKS.items():

        text += (
            f"{data['color']} {rank}\n"
            f"🪙 قیمت: {data['price']}\n"
            f"💬 ظرفیت چت: {data['chat_limit']}\n"
            f"✨ {data['description']}\n\n"
        )

    bot.send_message(
        message.chat.id,
        text
    )


# =========================================================
# LEADERBOARD
# =========================================================

@bot.message_handler(commands=["leaderboard"])
@bot.message_handler(func=lambda m: m.text == "🏆 رتبه‌بندی")
def leaderboard(message):

    if blocked(message):
        return

    ranking = sorted(
        users.values(),
        key=lambda x: (
            x["level"],
            x["xp"]
        ),
        reverse=True
    )

    text = "🏆 رتبه‌بندی\n\n"

    for i, user in enumerate(ranking[:20], 1):

        text += (
            f"{i}. "
            f"{RANKS[user['rank']]['color']} "
            f"{user['name']} "
            f"• Lv.{user['level']} "
            f"• {user['xp']} XP\n"
        )

    bot.send_message(
        message.chat.id,
        text
    )


# =========================================================
# CHANGE NAME
# =========================================================

@bot.message_handler(commands=["name"])
@bot.message_handler(func=lambda m: m.text == "✏️ تغییر نام")
def change_name(message):

    if blocked(message):
        return

    msg = bot.send_message(
        message.chat.id,
        "✏️ نام جدیدت را بفرست:"
    )

    bot.register_next_step_handler(
        msg,
        save_name
    )


def save_name(message):

    if blocked(message):
        return

    name = message.text.strip()

    if len(name) < 2 or len(name) > 25:

        bot.send_message(
            message.chat.id,
            "❌ نام باید بین ۲ تا ۲۵ کاراکتر باشد."
        )

        return

    users[message.from_user.id]["name"] = name

    bot.send_message(
        message.chat.id,
        f"✅ نامت تغییر کرد به:\n\n👤 {name}"
    )


# =========================================================
# ANONYMOUS MODE
# =========================================================

@bot.message_handler(commands=["anonymous"])
def anonymous_mode(message):

    if blocked(message):
        return

    user = get_user(message.from_user.id)

    user["anonymous"] = True

    bot.send_message(
        message.chat.id,
        "🕵️ حالت ناشناس فعال شد."
    )


@bot.message_handler(commands=["normal"])
def normal_mode(message):

    if blocked(message):
        return

    user = get_user(message.from_user.id)

    user["anonymous"] = False

    bot.send_message(
        message.chat.id,
        """
👤 حالت عادی فعال شد.

از این به بعد هنگام چت،
اطلاعات پروفایل تو برای طرف مقابل نمایش داده می‌شود.
"""
    )


# =========================================================
# GAMES
# =========================================================

@bot.message_handler(commands=["games"])
@bot.message_handler(func=lambda m: m.text == "🎮 بازی‌ها")
def games(message):

    if blocked(message):
        return

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "🎯 حدس عدد",
            callback_data="game_guess"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "✊ سنگ کاغذ قیچی",
            callback_data="game_rps"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "🎲 تاس",
            callback_data="game_dice"
        )
    )

    bot.send_message(
        message.chat.id,
        "🎮 بازی مورد نظرت را انتخاب کن:",
        reply_markup=kb
    )


# =========================================================
# GUESS
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "game_guess"
)
def game_guess(call):

    number = random.randint(1, 5)

    kb = types.InlineKeyboardMarkup()

    for i in range(1, 6):

        kb.add(
            types.InlineKeyboardButton(
                str(i),
                callback_data=f"guess_{i}_{number}"
            )
        )

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        "🎯 یک عدد از ۱ تا ۵ انتخاب کن:",
        reply_markup=kb
    )


@bot.callback_query_handler(
    func=lambda c: c.data.startswith("guess_")
)
def guess_result(call):

    parts = call.data.split("_")

    selected = int(parts[1])
    number = int(parts[2])

    user_id = call.from_user.id

    if selected == number:

        users[user_id]["coins"] += 100
        users[user_id]["missions"]["games"] += 1

        add_xp(user_id, 50)

        text = (
            "🎉 بردی!\n\n"
            f"🔢 عدد: {number}\n"
            "🪙 +100 سکه\n"
            "⭐ +50 XP"
        )

    else:

        users[user_id]["missions"]["games"] += 1

        text = (
            "❌ باختی!\n\n"
            f"🔢 عدد درست: {number}"
        )

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        text
    )


# =========================================================
# RPS
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "game_rps"
)
def rps_start(call):

    kb = types.InlineKeyboardMarkup()

    kb.row(
        types.InlineKeyboardButton(
            "✊",
            callback_data="rps_rock"
        ),
        types.InlineKeyboardButton(
            "🖐",
            callback_data="rps_paper"
        ),
        types.InlineKeyboardButton(
            "✌️",
            callback_data="rps_scissors"
        )
    )

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        "🎮 انتخاب کن:",
        reply_markup=kb
    )


@bot.callback_query_handler(
    func=lambda c: c.data.startswith("rps_")
)
def rps_result(call):

    user_id = call.from_user.id

    user_choice = call.data.replace(
        "rps_",
        ""
    )

    bot_choice = random.choice(
        ["rock", "paper", "scissors"]
    )

    names = {
        "rock": "✊ سنگ",
        "paper": "🖐 کاغذ",
        "scissors": "✌️ قیچی"
    }

    if user_choice == bot_choice:

        result = "🤝 مساوی!"

    elif (
        (user_choice == "rock" and bot_choice == "scissors")
        or
        (user_choice == "paper" and bot_choice == "rock")
        or
        (user_choice == "scissors" and bot_choice == "paper")
    ):

        users[user_id]["coins"] += 100
        add_xp(user_id, 50)

        result = "🎉 بردی!\n🪙 +100 سکه\n⭐ +50 XP"

    else:

        result = "😅 باختی!"

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        f"""
🎮 نتیجه

👤 تو: {names[user_choice]}
🤖 بات: {names[bot_choice]}

{result}
"""
    )


# =========================================================
# DICE
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "game_dice"
)
def dice_game(call):

    user_id = call.from_user.id

    user_roll = random.randint(1, 6)
    bot_roll = random.randint(1, 6)

    if user_roll > bot_roll:

        users[user_id]["coins"] += 150
        add_xp(user_id, 70)

        result = "🎉 تو بردی!\n🪙 +150 سکه"

    elif user_roll == bot_roll:

        result = "🤝 مساوی!"

    else:

        result = "😅 بات برد!"

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        f"""
🎲 نتیجه تاس

👤 تو: {user_roll}
🤖 بات: {bot_roll}

{result}
"""
    )


# =========================================================
# MISSIONS
# =========================================================

@bot.message_handler(commands=["missions"])
@bot.message_handler(func=lambda m: m.text == "🎯 مأموریت‌ها")
def missions(message):

    if blocked(message):
        return

    user = users[message.from_user.id]
    m = user["missions"]

    text = f"""
🎯 مأموریت‌های تو

💬 ارسال پیام:
{m['messages']} / 10
🎁 جایزه: 100 XP

👥 چت:
{m['chats']} / 3
🎁 جایزه: 150 XP

🎮 بازی:
{m['games']} / 5
🎁 جایزه: 250 سکه

🔥 ورود روزانه:
استریک فعلی: {user['streak']}
"""

    bot.send_message(
        message.chat.id,
        text
    )


# =========================================================
# SHOP
# =========================================================

@bot.message_handler(commands=["shop"])
@bot.message_handler(func=lambda m: m.text == "🛒 فروشگاه")
def shop(message):

    if blocked(message):
        return

    kb = types.InlineKeyboardMarkup()

    for key, item in SHOP_ITEMS.items():

        kb.add(
            types.InlineKeyboardButton(
                f"{item['name']} | {item['price']} 🪙",
                callback_data=f"buy_{key}"
            )
        )

    for rank, data in RANKS.items():

        if rank == "Bronze":
            continue

        kb.add(
            types.InlineKeyboardButton(
                f"{data['color']} {rank} | {data['price']} 🪙",
                callback_data=f"rank_{rank}"
            )
        )

    bot.send_message(
        message.chat.id,
        f"""
🛒 فروشگاه

🪙 سکه فعلی:
{users[message.from_user.id]['coins']}

خریدت رو انتخاب کن:
""",
        reply_markup=kb
    )


@bot.callback_query_handler(
    func=lambda c: c.data.startswith("buy_")
)
def buy_item(call):

    user_id = call.from_user.id
    key = call.data.replace("buy_", "")

    if key not in SHOP_ITEMS:
        return

    item = SHOP_ITEMS[key]
    user = users[user_id]

    if user["coins"] < item["price"]:

        bot.answer_callback_query(
            call.id,
            "❌ سکه کافی نیست!",
            show_alert=True
        )

        return

    if key in user["items"]:

        bot.answer_callback_query(
            call.id,
            "❌ این آیتم را قبلاً داری!",
            show_alert=True
        )

        return

    user["coins"] -= item["price"]
    user["items"].append(key)

    bot.answer_callback_query(
        call.id,
        "✅ خرید شد!"
    )

    bot.send_message(
        user_id,
        f"🎉 خرید موفق!\n\n{item['name']}"
    )


@bot.callback_query_handler(
    func=lambda c: c.data.startswith("rank_")
)
def buy_rank(call):

    user_id = call.from_user.id

    rank = call.data.replace(
        "rank_",
        ""
    )

    if rank not in RANKS:
        return

    user = users[user_id]
    price = RANKS[rank]["price"]

    if user["coins"] < price:

        bot.answer_callback_query(
            call.id,
            "❌ سکه کافی نیست!",
            show_alert=True
        )

        return

    user["coins"] -= price
    user["rank"] = rank

    bot.answer_callback_query(
        call.id,
        "👑 رتبه خریداری شد!"
    )

    bot.send_message(
        user_id,
        f"""
🎉 تبریک!

رتبه جدید:
{RANKS[rank]['color']} {rank}

✨ {RANKS[rank]['description']}
"""
    )


# =========================================================
# CHAT MENU
# =========================================================

@bot.message_handler(commands=["chat"])
@bot.message_handler(func=lambda m: m.text == "💬 چت")
def chat_menu(message):

    if blocked(message):
        return

    user_id = message.from_user.id

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "🔎 پیدا کردن چت",
            callback_data="find_chat"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "🕵️ ناشناس",
            callback_data="mode_anonymous"
        ),
        types.InlineKeyboardButton(
            "👤 عادی",
            callback_data="mode_normal"
        )
    )

    bot.send_message(
        message.chat.id,
        """
💬 چت

🕵️ حالت ناشناس:
اطلاعات واقعی تو نمایش داده نمی‌شود.

👤 حالت عادی:
اطلاعات پروفایل تو برای طرف مقابل نمایش داده می‌شود.
""",
        reply_markup=kb
    )


# =========================================================
# CHAT MODES
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "mode_anonymous"
)
def mode_anonymous(call):

    users[call.from_user.id]["anonymous"] = True

    bot.answer_callback_query(
        call.id,
        "🕵️ ناشناس فعال شد!"
    )


@bot.callback_query_handler(
    func=lambda c: c.data == "mode_normal"
)
def mode_normal(call):

    users[call.from_user.id]["anonymous"] = False

    bot.answer_callback_query(
        call.id,
        "👤 حالت عادی فعال شد!"
    )


# =========================================================
# FIND CHAT
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "find_chat"
)
def find_chat(call):

    user_id = call.from_user.id

    if user_id in active_chats:

        bot.answer_callback_query(
            call.id,
            "❌ شما داخل چت هستید!",
            show_alert=True
        )

        return

    if user_id in waiting_users:

        bot.answer_callback_query(
            call.id,
            "⏳ شما در صف هستید.",
            show_alert=True
        )

        return

    partner = None

    for waiting in waiting_users:

        if waiting != user_id:
            partner = waiting
            break

    if partner is None:

        waiting_users.append(user_id)

        bot.answer_callback_query(call.id)

        bot.send_message(
            user_id,
            "🔎 در حال پیدا کردن یک نفر...\n\n"
            "⏳ منتظر بمان."
        )

        return

    waiting_users.remove(partner)

    active_chats[user_id] = partner
    active_chats[partner] = user_id

    users[user_id]["chats"] += 1
    users[partner]["chats"] += 1

    users[user_id]["missions"]["chats"] += 1
    users[partner]["missions"]["chats"] += 1

    chat_id = f"{min(user_id, partner)}_{max(user_id, partner)}"

    chat_logs[chat_id] = []

    bot.answer_callback_query(
        call.id
    )

    send_chat_started(user_id, partner)
    send_chat_started(partner, user_id)


def send_chat_started(user_id, partner_id):

    user = users[user_id]
    partner = users[partner_id]

    if partner["anonymous"]:

        info = f"""
🕵️ کاربر ناشناس

🏷 رتبه:
{RANKS[partner['rank']]['color']} {partner['rank']}

💬 چت شروع شد!
"""

    else:

        info = f"""
👤 اطلاعات کاربر

👤 نام: {partner['name']}
🆔 کد: {partner['code']}
🏷 رتبه: {RANKS[partner['rank']]['color']} {partner['rank']}
⭐ Level: {partner['level']}
💬 تعداد چت: {partner['chats']}

💬 چت شروع شد!
"""

    bot.send_message(
        user_id,
        info
        + "\n\n"
        "برای پایان:\n"
        "/end\n\n"
        "برای گزارش:\n"
        "/report"
    )


# =========================================================
# END CHAT
# =========================================================

@bot.message_handler(commands=["end"])
def end_chat(message):

    user_id = message.from_user.id

    if user_id not in active_chats:

        bot.send_message(
            message.chat.id,
            "❌ داخل چتی نیستی."
        )

        return

    partner = active_chats.get(user_id)

    active_chats.pop(user_id, None)
    active_chats.pop(partner, None)

    bot.send_message(
        user_id,
        "🛑 چت پایان یافت."
    )

    if partner:

        bot.send_message(
            partner,
            "🛑 طرف مقابل چت را پایان داد."
        )


# =========================================================
# REPORT
# =========================================================

@bot.message_handler(commands=["report"])
def report(message):

    user_id = message.from_user.id

    if user_id not in active_chats:

        bot.send_message(
            message.chat.id,
            "❌ داخل چتی نیستی."
        )

        return

    partner = active_chats[user_id]

    reports.append({
        "reporter": user_id,
        "reported": partner,
        "time": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    })

    bot.send_message(
        user_id,
        "🚨 گزارش ثبت شد."
    )


# =========================================================
# CHAT MESSAGE
# =========================================================

@bot.message_handler(
    func=lambda m: (
        m.from_user.id in active_chats
        and m.text is not None
        and not m.text.startswith("/")
        and m.text not in [
            "👤 پروفایل",
            "💬 چت",
            "🎮 بازی‌ها",
            "🎯 مأموریت‌ها",
            "🛒 فروشگاه",
            "🪙 کیف پول",
            "🏆 رتبه‌بندی",
            "🎁 جوایز",
            "✏️ تغییر نام",
            "👥 دعوت دوستان",
            "⚙️ تنظیمات",
            "🗑 حذف حساب",
            "👑 مدیریت"
        ]
    )
)
def anonymous_chat(message):

    user_id = message.from_user.id

    if is_banned(user_id):
        return

    partner = active_chats.get(user_id)

    if not partner:
        return

    if partner not in users:
        return

    user = users[user_id]

    # XP و آمار
    user["messages"] += 1
    user["missions"]["messages"] += 1

    add_xp(user_id, 5)

    chat_id = f"{min(user_id, partner)}_{max(user_id, partner)}"

    if chat_id not in chat_logs:
        chat_logs[chat_id] = []

    # ثبت لاگ
    chat_logs[chat_id].append({
        "sender": user_id,
        "receiver": partner,
        "text": message.text,
        "time": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    })

    # پیام برای طرف مقابل
    if user["anonymous"]:

        text = (
            f"🕵️ {user['rank']}\n\n"
            f"{message.text}"
        )

    else:

        text = f"""
👤 اطلاعات فرستنده

👤 نام: {user['name']}
🆔 کد: {user['code']}
🏷 رتبه: {RANKS[user['rank']]['color']} {user['rank']}
⭐ Level: {user['level']}

━━━━━━━━━━━━

{message.text}
"""

    bot.send_message(
        partner,
        text
    )


# =========================================================
# DELETE ACCOUNT
# 30,000 تومان
# =========================================================

@bot.message_handler(commands=["delete"])
@bot.message_handler(func=lambda m: m.text == "🗑 حذف حساب")
def delete_account(message):

    if blocked(message):
        return

    user_id = message.from_user.id
    user = users.get(user_id)

    if not user:
        return

    if user["balance"] < 30000:

        bot.send_message(
            message.chat.id,
            f"""
🗑 حذف کامل حساب

هزینه حذف حساب:
💰 30,000 تومان

موجودی شما:
💰 {user['balance']:,} تومان

❌ موجودی کافی نیست.
"""
        )

        return

    kb = types.InlineKeyboardMarkup()

    kb.row(
        types.InlineKeyboardButton(
            "❌ لغو",
            callback_data="delete_no"
        ),
        types.InlineKeyboardButton(
            "🗑 حذف کامل",
            callback_data="delete_yes"
        )
    )

    bot.send_message(
        message.chat.id,
        """
⚠️ هشدار

با حذف حساب:

❌ پروفایل پاک می‌شود
❌ XP پاک می‌شود
❌ سکه‌ها پاک می‌شوند
❌ موجودی پاک می‌شود
❌ رتبه پاک می‌شود
❌ آیتم‌ها پاک می‌شوند
❌ آمار پاک می‌شود

و هزینه:
💰 30,000 تومان

برای ادامه تأیید کن.
""",
        reply_markup=kb
    )


@bot.callback_query_handler(
    func=lambda c: c.data == "delete_no"
)
def delete_no(call):

    bot.answer_callback_query(
        call.id,
        "لغو شد."
    )

    bot.send_message(
        call.message.chat.id,
        "✅ حذف حساب لغو شد."
    )


@bot.callback_query_handler(
    func=lambda c: c.data == "delete_yes"
)
def delete_yes(call):

    user_id = call.from_user.id

    if user_id not in users:
        return

    user = users[user_id]

    if user["balance"] < 30000:

        bot.answer_callback_query(
            call.id,
            "❌ موجودی کافی نیست!",
            show_alert=True
        )

        return

    # پایان چت
    if user_id in active_chats:

        partner = active_chats.get(user_id)

        active_chats.pop(user_id, None)

        if partner:
            active_chats.pop(partner, None)

            try:
                bot.send_message(
                    partner,
                    "🛑 طرف مقابل حساب خود را حذف کرد."
                )
            except:
                pass

    # حذف از صف
    if user_id in waiting_users:
        waiting_users.remove(user_id)

    # حذف لاگ‌های مربوط به کاربر
    for chat_id in list(chat_logs.keys()):

        logs = chat_logs[chat_id]

        logs = [
            x for x in logs
            if x["sender"] != user_id
            and x["receiver"] != user_id
        ]

        if logs:
            chat_logs[chat_id] = logs
        else:
            del chat_logs[chat_id]

    # حذف گزارش‌های مربوط به کاربر
    reports[:] = [
        r for r in reports
        if r["reporter"] != user_id
        and r["reported"] != user_id
    ]

    # حذف کامل
    del users[user_id]

    bot.answer_callback_query(
        call.id,
        "حساب حذف شد."
    )

    bot.send_message(
        call.message.chat.id,
        """
🗑 حساب شما کاملاً حذف شد.

تمام اطلاعات مربوط به حساب پاک شد.

برای ساخت حساب جدید:
 /start
"""
    )


# =========================================================
# REWARDS
# =========================================================

@bot.message_handler(
    func=lambda m: m.text == "🎁 جوایز"
)
def rewards(message):

    if blocked(message):
        return

    bot.send_message(
        message.chat.id,
        """
🎁 جوایز

⭐ با بالا رفتن Level:
🪙 سکه دریافت می‌کنی.

🔥 با استریک روزانه:
🪙 سکه بیشتر می‌گیری.

🎯 با انجام مأموریت:
⭐ XP و 🪙 سکه می‌گیری.

🏆 با فعالیت بیشتر:
رتبه‌ات را ارتقا بده.
"""
    )


# =========================================================
# REFERRAL
# =========================================================

@bot.message_handler(
    func=lambda m: m.text == "👥 دعوت دوستان"
)
def referrals(message):

    if blocked(message):
        return

    user_id = message.from_user.id

    info = bot.get_me()

    link = (
        f"https://t.me/{info.username}"
        f"?start=ref{user_id}"
    )

    bot.send_message(
        message.chat.id,
        f"""
👥 دعوت دوستان

🔗 لینک دعوت تو:

{link}

🎁 با دعوت دوستان می‌توانی
پاداش دریافت کنی.
"""
    )


# =========================================================
# SETTINGS
# =========================================================

@bot.message_handler(
    func=lambda m: m.text == "⚙️ تنظیمات"
)
def settings(message):

    if blocked(message):
        return

    user = users[message.from_user.id]

    mode = (
        "🕵️ ناشناس"
        if user["anonymous"]
        else "👤 عادی"
    )

    bot.send_message(
        message.chat.id,
        f"""
⚙️ تنظیمات

🕵️ حالت فعلی:
{mode}

برای ناشناس:
/anonymous

برای حالت عادی:
/normal

برای تغییر نام:
/name
"""
    )


# =========================================================
# ADMIN PANEL
# =========================================================

@bot.message_handler(commands=["admin"])
def admin(message):

    if not is_admin(message.from_user.id):

        bot.send_message(
            message.chat.id,
            "⛔ دسترسی غیرمجاز."
        )

        return

    admin_panel(message)


@bot.message_handler(
    func=lambda m: m.text == "👑 مدیریت"
)
def admin_button(message):

    if not is_admin(message.from_user.id):
        return

    admin_panel(message)


def admin_panel(message):

    kb = types.InlineKeyboardMarkup()

    kb.row(
        types.InlineKeyboardButton(
            "📊 آمار",
            callback_data="a_stats"
        ),
        types.InlineKeyboardButton(
            "👥 کاربران",
            callback_data="a_users"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            "🔎 جستجو",
            callback_data="a_search"
        ),
        types.InlineKeyboardButton(
            "💬 لاگ چت",
            callback_data="a_logs"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            "💰 افزایش موجودی",
            callback_data="a_addmoney"
        ),
        types.InlineKeyboardButton(
            "💸 کاهش موجودی",
            callback_data="a_removemoney"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            "🪙 تغییر سکه",
            callback_data="a_coins"
        ),
        types.InlineKeyboardButton(
            "⭐ تغییر XP",
            callback_data="a_xp"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            "👑 تغییر رتبه",
            callback_data="a_rank"
        ),
        types.InlineKeyboardButton(
            "🚫 بن",
            callback_data="a_ban"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            "🔓 آن‌بن",
            callback_data="a_unban"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            "🚨 گزارش‌ها",
            callback_data="a_reports"
        ),
        types.InlineKeyboardButton(
            "📢 همگانی",
            callback_data="a_broadcast"
        )
    )

    bot.send_message(
        message.chat.id,
        "👑 پنل مدیریت",
        reply_markup=kb
    )


# =========================================================
# ADMIN STATS
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "a_stats"
)
def a_stats(call):

    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        f"""
📊 آمار ربات

👥 کاربران:
{len(users)}

⏳ در صف:
{len(waiting_users)}

💬 چت فعال:
{len(active_chats) // 2}

🚨 گزارش:
{len(reports)}

💬 لاگ:
{sum(len(x) for x in chat_logs.values())}
"""
    )


# =========================================================
# ADMIN USERS
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "a_users"
)
def a_users(call):

    if not is_admin(call.from_user.id):
        return

    text = "👥 کاربران\n\n"

    for user in list(users.values())[:50]:

        text += (
            f"🆔 {user['code']} | "
            f"{user['name']} | "
            f"{user['rank']} | "
            f"Lv.{user['level']}\n"
        )

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        text or "کاربری وجود ندارد."
    )


# =========================================================
# ADMIN SEARCH
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "a_search"
)
def a_search(call):

    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(call.id)

    msg = bot.send_message(
        call.message.chat.id,
        "🔎 کد کاربر را وارد کن:"
    )

    bot.register_next_step_handler(
        msg,
        admin_search_user
    )


def admin_search_user(message):

    if not is_admin(message.from_user.id):
        return

    code = message.text.strip()

    found = None

    for user in users.values():

        if user["code"] == code:
            found = user
            break

    if not found:

        bot.send_message(
            message.chat.id,
            "❌ پیدا نشد."
        )

        return

    bot.send_message(
        message.chat.id,
        f"""
👤 کاربر

🆔 کد: {found['code']}
👤 نام: {found['name']}
📱 Telegram ID: {found['id']}

👑 رتبه: {found['rank']}
⭐ Level: {found['level']}
✨ XP: {found['xp']}

🪙 سکه: {found['coins']}
💰 موجودی: {found['balance']:,}

🚫 بن:
{"بله" if found["banned"] else "خیر"}

🕵️ ناشناس:
{"فعال" if found["anonymous"] else "خاموش"}
"""
    )


# =========================================================
# ADMIN BAN
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "a_ban"
)
def a_ban(call):

    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(call.id)

    msg = bot.send_message(
        call.message.chat.id,
        "🚫 کد کاربر برای بن:"
    )

    bot.register_next_step_handler(
        msg,
        do_ban
    )


def do_ban(message):

    if not is_admin(message.from_user.id):
        return

    code = message.text.strip()

    for user in users.values():

        if user["code"] == code:

            user["banned"] = True

            # قطع چت
            if user["id"] in active_chats:

                partner = active_chats.get(
                    user["id"]
                )

                active_chats.pop(
                    user["id"],
                    None
                )

                if partner:
                    active_chats.pop(
                        partner,
                        None
                    )

                    try:
                        bot.send_message(
                            partner,
                            "🛑 طرف مقابل توسط مدیریت مسدود شد."
                        )
                    except:
                        pass

            bot.send_message(
                message.chat.id,
                f"🚫 کاربر {code} بن شد."
            )

            return

    bot.send_message(
        message.chat.id,
        "❌ کاربر پیدا نشد."
    )


# =========================================================
# ADMIN UNBAN
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "a_unban"
)
def a_unban(call):

    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(call.id)

    msg = bot.send_message(
        call.message.chat.id,
        "🔓 کد کاربر برای آن‌بن:"
    )

    bot.register_next_step_handler(
        msg,
        do_unban
    )


def do_unban(message):

    if not is_admin(message.from_user.id):
        return

    code = message.text.strip()

    for user in users.values():

        if user["code"] == code:

            user["banned"] = False

            bot.send_message(
                message.chat.id,
                f"✅ کاربر {code} از بن خارج شد."
            )

            return

    bot.send_message(
        message.chat.id,
        "❌ کاربر پیدا نشد."
    )


# =========================================================
# ADMIN CHAT LOGS
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "a_logs"
)
def a_logs(call):

    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(call.id)

    if not chat_logs:

        bot.send_message(
            call.message.chat.id,
            "💬 هیچ لاگ چتی وجود ندارد."
        )

        return

    kb = types.InlineKeyboardMarkup()

    for chat_id in list(chat_logs.keys())[-20:]:

        kb.add(
            types.InlineKeyboardButton(
                f"💬 {chat_id}",
                callback_data=f"log_{chat_id}"
            )
        )

    bot.send_message(
        call.message.chat.id,
        "💬 چت مورد نظر را انتخاب کن:",
        reply_markup=kb
    )


@bot.callback_query_handler(
    func=lambda c: c.data.startswith("log_")
)
def show_log(call):

    if not is_admin(call.from_user.id):
        return

    chat_id = call.data.replace(
        "log_",
        ""
    )

    logs = chat_logs.get(
        chat_id,
        []
    )

    if not logs:

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "❌ لاگی وجود ندارد."
        )

        return

    text = f"💬 لاگ چت\n\n"

    for log in logs:

        sender = users.get(
            log["sender"]
        )

        name = (
            sender["name"]
            if sender
            else "حذف شده"
        )

        text += (
            f"🕐 {log['time']}\n"
            f"👤 {name}\n"
            f"💬 {log['text']}\n\n"
        )

        if len(text) > 3800:

            bot.send_message(
                call.message.chat.id,
                text
            )

            text = ""

    if text:

        bot.send_message(
            call.message.chat.id,
            text
        )

    bot.answer_callback_query(call.id)


# =========================================================
# ADMIN REPORTS
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "a_reports"
)
def a_reports(call):

    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(call.id)

    if not reports:

        bot.send_message(
            call.message.chat.id,
            "🚨 گزارشی وجود ندارد."
        )

        return

    text = "🚨 گزارش‌ها\n\n"

    for i, report in enumerate(
        reports,
        1
    ):

        reporter = users.get(
            report["reporter"]
        )

        reported = users.get(
            report["reported"]
        )

        text += (
            f"{i}.\n"
            f"👤 گزارش‌دهنده: "
            f"{reporter['code'] if reporter else 'حذف شده'}\n"
            f"🚨 متهم: "
            f"{reported['code'] if reported else 'حذف شده'}\n"
            f"🕐 {report['time']}\n\n"
        )

    bot.send_message(
        call.message.chat.id,
        text
    )


# =========================================================
# ADMIN ADD MONEY
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "a_addmoney"
)
def a_addmoney(call):

    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(call.id)

    msg = bot.send_message(
        call.message.chat.id,
        "💰 کد کاربر و مبلغ:\n\n"
        "مثال:\n"
        "0001 50000"
    )

    bot.register_next_step_handler(
        msg,
        do_addmoney
    )


def do_addmoney(message):

    if not is_admin(message.from_user.id):
        return

    try:
        code, amount = message.text.split()
        amount = int(amount)
    except:
        bot.send_message(
            message.chat.id,
            "❌ فرمت اشتباه."
        )
        return

    for user in users.values():

        if user["code"] == code:

            user["balance"] += amount

            bot.send_message(
                message.chat.id,
                "✅ موجودی اضافه شد."
            )

            return

    bot.send_message(
        message.chat.id,
        "❌ کاربر پیدا نشد."
    )


# =========================================================
# ADMIN REMOVE MONEY
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "a_removemoney"
)
def a_removemoney(call):

    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(call.id)

    msg = bot.send_message(
        call.message.chat.id,
        "💸 کد کاربر و مبلغ:\n\n"
        "مثال:\n"
        "0001 50000"
    )

    bot.register_next_step_handler(
        msg,
        do_removemoney
    )


def do_removemoney(message):

    if not is_admin(message.from_user.id):
        return

    try:
        code, amount = message.text.split()
        amount = int(amount)
    except:
        bot.send_message(
            message.chat.id,
            "❌ فرمت اشتباه."
        )
        return

    for user in users.values():

        if user["code"] == code:

            user["balance"] = max(
                0,
                user["balance"] - amount
            )

            bot.send_message(
                message.chat.id,
                "✅ موجودی کم شد."
            )

            return

    bot.send_message(
        message.chat.id,
        "❌ کاربر پیدا نشد."
    )


# =========================================================
# ADMIN COINS
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "a_coins"
)
def a_coins(call):

    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(call.id)

    msg = bot.send_message(
        call.message.chat.id,
        "🪙 کد کاربر و مقدار سکه:\n\n"
        "مثال:\n"
        "0001 1000"
    )

    bot.register_next_step_handler(
        msg,
        do_coins
    )


def do_coins(message):

    if not is_admin(message.from_user.id):
        return

    try:
        code, amount = message.text.split()
        amount = int(amount)
    except:
        bot.send_message(
            message.chat.id,
            "❌ فرمت اشتباه."
        )
        return

    for user in users.values():

        if user["code"] == code:

            user["coins"] = max(
                0,
                user["coins"] + amount
            )

            bot.send_message(
                message.chat.id,
                "✅ سکه تغییر کرد."
            )

            return

    bot.send_message(
        message.chat.id,
        "❌ کاربر پیدا نشد."
    )


# =========================================================
# ADMIN XP
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "a_xp"
)
def a_xp(call):

    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(call.id)

    msg = bot.send_message(
        call.message.chat.id,
        "⭐ کد کاربر و XP:\n\n"
        "مثال:\n"
        "0001 500"
    )

    bot.register_next_step_handler(
        msg,
        do_xp
    )


def do_xp(message):

    if not is_admin(message.from_user.id):
        return

    try:
        code, amount = message.text.split()
        amount = int(amount)
    except:
        bot.send_message(
            message.chat.id,
            "❌ فرمت اشتباه."
        )
        return

    for user in users.values():

        if user["code"] == code:

            add_xp(
                user["id"],
                amount
            )

            bot.send_message(
                message.chat.id,
                "✅ XP تغییر کرد."
            )

            return

    bot.send_message(
        message.chat.id,
        "❌ کاربر پیدا نشد."
    )


# =========================================================
# ADMIN RANK
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "a_rank"
)
def a_rank(call):

    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(call.id)

    msg = bot.send_message(
        call.message.chat.id,
        "👑 کد کاربر و رتبه:\n\n"
        "مثال:\n"
        "0001 VIP\n\n"
        "رتبه‌ها:\n"
        "Bronze\n"
        "Silver\n"
        "Gold\n"
        "Diamond\n"
        "VIP"
    )

    bot.register_next_step_handler(
        msg,
        do_rank
    )


def do_rank(message):

    if not is_admin(message.from_user.id):
        return

    try:
        code, rank = message.text.split()
    except:
        bot.send_message(
            message.chat.id,
            "❌ فرمت اشتباه."
        )
        return

    if rank not in RANKS:

        bot.send_message(
            message.chat.id,
            "❌ این رتبه وجود ندارد."
        )

        return

    for user in users.values():

        if user["code"] == code:

            user["rank"] = rank

            bot.send_message(
                message.chat.id,
                "👑 رتبه تغییر کرد."
            )

            return

    bot.send_message(
        message.chat.id,
        "❌ کاربر پیدا نشد."
    )


# =========================================================
# BROADCAST
# =========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "a_broadcast"
)
def a_broadcast(call):

    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(call.id)

    msg = bot.send_message(
        call.message.chat.id,
        "📢 پیام همگانی:"
    )

    bot.register_next_step_handler(
        msg,
        do_broadcast
    )


def do_broadcast(message):

    if not is_admin(message.from_user.id):
        return

    success = 0

    for user_id in list(users.keys()):

        try:

            bot.send_message(
                user_id,
                f"📢 پیام مدیریت\n\n{message.text}"
            )

            success += 1

        except:
            pass

    bot.send_message(
        message.chat.id,
        f"✅ پیام برای {success} کاربر ارسال شد."
    )


# =========================================================
# SIMPLE COMMANDS
# =========================================================

@bot.message_handler(commands=["rank"])
def rank_command(message):

    if blocked(message):
        return

    user = users.get(message.from_user.id)

    bot.send_message(
        message.chat.id,
        rank_text(user["rank"])
    )


@bot.message_handler(commands=["stats"])
def stats_command(message):

    if not is_admin(message.from_user.id):
        return

    bot.send_message(
        message.chat.id,
        f"""
📊 آمار

👥 کاربران: {len(users)}
⏳ صف: {len(waiting_users)}
💬 چت فعال: {len(active_chats)//2}
🚨 گزارش: {len(reports)}
"""
    )


# =========================================================
# UNKNOWN COMMAND
# =========================================================

@bot.message_handler(
    func=lambda m: (
        m.text is not None
        and m.text.startswith("/")
    )
)
def unknown_command(message):

    if blocked(message):
        return

    bot.send_message(
        message.chat.id,
        "❌ این دستور وجود ندارد.\n\n"
        "برای دیدن دستورات:\n"
        "/help"
    )


# =========================================================
# RUN
# =========================================================

print("Anonymous Chat Bot is running...")

bot.infinity_polling(
    skip_pending=True
)
