import telebot
import random
import time
from datetime import date

# ==================================================
# تنظیمات
# ==================================================

BOT_TOKEN = "8978005144:AAGforuwqrN_oF880nVOT5VyWnSMiqxrPVM"

# 👑 Telegram ID خودت را اینجا بگذار
ADMIN_ID = 7723971526

bot = telebot.TeleBot(BOT_TOKEN)

# ==================================================
# حافظه موقت
# ==================================================

users = {}
waiting_users = []
active_chats = {}
reports = []

# ==================================================
# ساخت شماره کاربری
# ==================================================

def generate_code():

    while True:
        code = str(random.randint(1000, 9999))

        if not any(
            user["code"] == code
            for user in users.values()
        ):
            return code


# ==================================================
# پیدا کردن کاربر
# ==================================================

def get_user(user_id):
    return users.get(user_id)


# ==================================================
# XP
# ==================================================

def xp_needed(level):
    return level * 250


def add_xp(user_id, amount):

    user = get_user(user_id)

    if not user:
        return

    user["xp"] += amount

    while user["xp"] >= xp_needed(user["level"]):

        user["xp"] -= xp_needed(user["level"])

        user["level"] += 1

        reward = user["level"] * 100

        user["coins"] += reward

        bot.send_message(
            user_id,
            f"""
🎉 LEVEL UP!

⭐ Level جدید:
{user['level']}

🎁 جایزه:
🪙 +{reward} سکه

🔥 ادامه بده!
"""
        )


# ==================================================
# ثبت نام
# ==================================================

def register_user(message, name):

    user_id = message.from_user.id

    users[user_id] = {

        "id": user_id,

        "name": name,

        "code": generate_code(),

        "rank": "Member",

        "level": 1,

        "xp": 0,

        "coins": 0,

        "balance": 0,

        "streak": 0,

        "last_daily": None,

        "banned": False,

        "messages": 0,

        "chats": 0,

        "referrals": 0
    }


# ==================================================
# منوی اصلی
# ==================================================

def main_keyboard():

    kb = telebot.types.ReplyKeyboardMarkup(
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
        "🎁 جوایز",
        "🪙 کیف پول"
    )

    kb.row(
        "🏆 رتبه‌بندی",
        "🛒 فروشگاه"
    )

    kb.row(
        "👥 دعوت دوستان",
        "⚙️ تنظیمات"
    )

    return kb


# ==================================================
# START
# ==================================================

@bot.message_handler(commands=["start"])
def start(message):

    user_id = message.from_user.id

    if user_id in users:

        if users[user_id]["banned"]:

            bot.send_message(
                user_id,
                "🚫 حساب شما مسدود است."
            )

            return

        bot.send_message(
            user_id,
            "🔥 خوش برگشتی!",
            reply_markup=main_keyboard()
        )

        daily_bonus(user_id)

        return

    msg = bot.send_message(
        user_id,
        """
👋 سلام!

🔥 به Streamer خوش اومدی!

برای ساخت حساب، اسم خودت رو بفرست:
"""
    )

    bot.register_next_step_handler(
        msg,
        finish_register
    )


def finish_register(message):

    name = message.text.strip()

    if len(name) < 2:

        msg = bot.send_message(
            message.chat.id,
            "❌ اسم خیلی کوتاهه.\nدوباره بفرست:"
        )

        bot.register_next_step_handler(
            msg,
            finish_register
        )

        return

    register_user(
        message,
        name
    )

    bot.send_message(
        message.chat.id,
        """
🎉 ثبت‌نام انجام شد!

🔥 به دنیای Streamer خوش اومدی.

از منوی پایین شروع کن 👇
""",
        reply_markup=main_keyboard()
    )


# ==================================================
# پاداش روزانه
# ==================================================

def daily_bonus(user_id):

    user = get_user(user_id)

    today = str(date.today())

    if user["last_daily"] == today:
        return

    yesterday_bonus = user["last_daily"]

    user["last_daily"] = today

    user["coins"] += 50

    add_xp(
        user_id,
        20
    )

    user["streak"] += 1

    bot.send_message(
        user_id,
        f"""
🔥 پاداش روزانه!

⭐ +20 XP
🪙 +50 سکه

🔥 Streak:
{user['streak']} روز
"""
    )


# ==================================================
# پروفایل
# ==================================================

@bot.message_handler(
    func=lambda m: m.text == "👤 پروفایل"
)
def profile(message):

    user = get_user(message.from_user.id)

    if not user:
        return

    needed = xp_needed(
        user["level"]
    )

    bot.send_message(
        message.chat.id,
        f"""
👤 پروفایل

━━━━━━━━━━━━

📝 نام:
{user['name']}

🔢 شماره:
#{user['code']}

👑 رتبه:
{user['rank']}

⭐ Level:
{user['level']}

✨ XP:
{user['xp']} / {needed}

🪙 سکه:
{user['coins']}

💰 موجودی:
{user['balance']:,} تومان

🔥 Streak:
{user['streak']} روز

💬 تعداد چت:
{user['chats']}

📨 پیام‌ها:
{user['messages']}

━━━━━━━━━━━━
"""
    )


# ==================================================
# کیف پول
# ==================================================

@bot.message_handler(
    func=lambda m: m.text == "🪙 کیف پول"
)
def wallet(message):

    user = get_user(message.from_user.id)

    if not user:
        return

    bot.send_message(
        message.chat.id,
        f"""
🪙 کیف پول

💰 موجودی:
{user['balance']:,} تومان

🪙 سکه:
{user['coins']}

⭐ XP:
{user['xp']}
"""
    )


# ==================================================
# مأموریت‌ها
# ==================================================

@bot.message_handler(
    func=lambda m: m.text == "🎯 مأموریت‌ها"
)
def missions(message):

    user = get_user(message.from_user.id)

    if not user:
        return

    bot.send_message(
        message.chat.id,
        """
🎯 مأموریت‌های امروز

⬜ یک چت انجام بده
🎁 +20 XP

⬜ 5 پیام بفرست
🎁 +30 XP

⬜ یک دوست دعوت کن
🎁 +100 XP

⬜ پاداش روزانه را بگیر
🎁 +20 XP
"""
    )


# ==================================================
# بازی
# ==================================================

@bot.message_handler(
    func=lambda m: m.text == "🎮 بازی‌ها"
)
def games(message):

    kb = telebot.types.InlineKeyboardMarkup()

    kb.add(
        telebot.types.InlineKeyboardButton(
            "🎲 حدس عدد",
            callback_data="guess"
        )
    )

    kb.add(
        telebot.types.InlineKeyboardButton(
            "✊ سنگ کاغذ قیچی",
            callback_data="rps"
        )
    )

    bot.send_message(
        message.chat.id,
        "🎮 بازی را انتخاب کن:",
        reply_markup=kb
    )


# ==================================================
# حدس عدد
# ==================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "guess"
)
def guess_game(call):

    number = random.randint(
        1,
        5
    )

    msg = bot.send_message(
        call.message.chat.id,
        "🎲 یک عدد بین 1 تا 5 بفرست:"
    )

    bot.register_next_step_handler(
        msg,
        check_guess,
        number
    )


def check_guess(message, number):

    try:
        guess = int(message.text)

    except:

        bot.send_message(
            message.chat.id,
            "❌ فقط عدد بفرست."
        )

        return

    if guess == number:

        user = get_user(
            message.from_user.id
        )

        user["coins"] += 100

        add_xp(
            message.from_user.id,
            50
        )

        bot.send_message(
            message.chat.id,
            """
🎉 بردی!

⭐ +50 XP
🪙 +100 سکه
"""
        )

    else:

        bot.send_message(
            message.chat.id,
            f"""
❌ باختی!

عدد درست:
{number}
"""
        )


# ==================================================
# رتبه‌بندی
# ==================================================

@bot.message_handler(
    func=lambda m: m.text == "🏆 رتبه‌بندی"
)
def leaderboard(message):

    top = sorted(
        users.values(),
        key=lambda u: (
            u["level"],
            u["xp"]
        ),
        reverse=True
    )[:10]

    text = "🏆 برترین کاربران\n\n"

    medals = [
        "🥇",
        "🥈",
        "🥉"
    ]

    for i, user in enumerate(top):

        medal = (
            medals[i]
            if i < 3
            else f"{i+1}."
        )

        text += (
            f"{medal} "
            f"{user['name']} | "
            f"Level {user['level']} | "
            f"{user['rank']}\n"
        )

    bot.send_message(
        message.chat.id,
        text
    )


# ==================================================
# فروشگاه
# ==================================================

@bot.message_handler(
    func=lambda m: m.text == "🛒 فروشگاه"
)
def shop(message):

    kb = telebot.types.InlineKeyboardMarkup()

    kb.add(
        telebot.types.InlineKeyboardButton(
            "🥈 Silver — 50,000",
            callback_data="silver"
        )
    )

    kb.add(
        telebot.types.InlineKeyboardButton(
            "🥇 Gold — 160,000",
            callback_data="gold"
        )
    )

    kb.add(
        telebot.types.InlineKeyboardButton(
            "💎 Diamond — 300,000",
            callback_data="diamond"
        )
    )

    bot.send_message(
        message.chat.id,
        "🛒 فروشگاه\n\nرتبه موردنظر را انتخاب کن:",
        reply_markup=kb
    )


@bot.callback_query_handler(
    func=lambda c:
    c.data in [
        "silver",
        "gold",
        "diamond"
    ]
)
def buy_rank(call):

    user = get_user(
        call.from_user.id
    )

    prices = {
        "silver": 50000,
        "gold": 160000,
        "diamond": 300000
    }

    ranks = {
        "silver": "Silver",
        "gold": "Gold",
        "diamond": "Diamond"
    }

    price = prices[call.data]
    rank = ranks[call.data]

    if user["balance"] < price:

        bot.answer_callback_query(
            call.id,
            "❌ موجودی کافی نیست."
        )

        return

    user["balance"] -= price
    user["rank"] = rank

    bot.answer_callback_query(
        call.id,
        "✅ خرید موفق!"
    )

    bot.send_message(
        call.message.chat.id,
        f"""
🎉 تبریک!

👑 رتبه جدید:
{rank}

💰 پرداخت:
{price:,} تومان
"""
    )


# ==================================================
# دعوت
# ==================================================

@bot.message_handler(
    func=lambda m: m.text == "👥 دعوت دوستان"
)
def referral(message):

    user = get_user(
        message.from_user.id
    )

    username = bot.get_me().username

    link = (
        f"https://t.me/"
        f"{username}"
        f"?start=ref{user['id']}"
    )

    bot.send_message(
        message.chat.id,
        f"""
👥 دعوت دوستان

لینک دعوت تو:

{link}

🎁 هر دوست جدید:
⭐ +100 XP
🪙 +100 سکه
"""
    )


# ==================================================
# چت
# ==================================================

@bot.message_handler(
    func=lambda m: m.text == "💬 چت"
)
def chat_menu(message):

    kb = telebot.types.InlineKeyboardMarkup()

    kb.add(
        telebot.types.InlineKeyboardButton(
            "🔎 پیدا کردن چت",
            callback_data="find"
        )
    )

    bot.send_message(
        message.chat.id,
        """
💬 چت ناشناس

با یک کاربر دیگر صحبت کن.

Telegram ID و Username نمایش داده نمی‌شود.
""",
        reply_markup=kb
    )


@bot.callback_query_handler(
    func=lambda c: c.data == "find"
)
def find_chat(call):

    user_id = call.from_user.id

    if user_id in active_chats:

        bot.answer_callback_query(
            call.id,
            "❌ تو الان در چت هستی."
        )

        return

    if user_id not in waiting_users:

        waiting_users.append(
            user_id
        )

    if len(waiting_users) < 2:

        bot.send_message(
            user_id,
            "🔎 منتظر یک نفر دیگر هستیم..."
        )

        return

    first = waiting_users.pop(0)
    second = waiting_users.pop(0)

    active_chats[first] = second
    active_chats[second] = first

    users[first]["chats"] += 1
    users[second]["chats"] += 1

    bot.send_message(
        first,
        """
🎉 چت پیدا شد!

پیامت را بفرست 👇

❌ برای پایان:
 /end
"""
    )

    bot.send_message(
        second,
        """
🎉 چت پیدا شد!

پیامت را بفرست 👇

❌ برای پایان:
 /end
"""
    )


# ==================================================
# انتقال پیام چت
# ==================================================

@bot.message_handler(
    func=lambda m:
    m.from_user.id in active_chats
)
def relay(message):

    user_id = message.from_user.id

    other = active_chats[user_id]

    user = get_user(user_id)

    if not user:
        return

    user["messages"] += 1

    add_xp(
        user_id,
        5
    )

    bot.send_message(
        other,
        f"""
💬 {user['name']} | {user['rank']} گفت:

{message.text}
"""
    )


# ==================================================
# پایان چت
# ==================================================

@bot.message_handler(
    commands=["end"]
)
def end_chat(message):

    user_id = message.from_user.id

    if user_id not in active_chats:

        bot.send_message(
            user_id,
            "❌ چتی نداری."
        )

        return

    other = active_chats[user_id]

    del active_chats[user_id]

    if other in active_chats:
        del active_chats[other]

    bot.send_message(
        user_id,
        "❌ چت پایان یافت."
    )

    try:

        bot.send_message(
            other,
            "❌ طرف مقابل چت را پایان داد."
        )

    except:
        pass


# ==================================================
# گزارش
# ==================================================

@bot.message_handler(
    commands=["report"]
)
def report(message):

    user_id = message.from_user.id

    if user_id not in active_chats:
        return

    other = active_chats[user_id]

    reports.append({
        "reporter": user_id,
        "reported": other,
        "time": time.time()
    })

    bot.send_message(
        user_id,
        "🚨 گزارش ثبت شد."
    )


# ==================================================
# ADMIN
# ==================================================

def is_admin(user_id):

    return user_id == ADMIN_ID


@bot.message_handler(
    commands=["admin"]
)
def admin(message):

    if not is_admin(
        message.from_user.id
    ):

        bot.send_message(
            message.chat.id,
            "⛔ دسترسی ندارید."
        )

        return

    kb = telebot.types.InlineKeyboardMarkup()

    buttons = [

        ("📊 آمار", "stats"),

        ("👥 کاربران", "users"),

        ("🔎 جستجوی کاربر", "search"),

        ("💰 افزایش پول", "addmoney"),

        ("💸 کاهش پول", "removemoney"),

        ("⭐ تغییر XP", "xp"),

        ("🪙 تغییر سکه", "coins"),

        ("👑 تغییر رتبه", "rank"),

        ("🚫 بن کاربر", "ban"),

        ("📢 پیام همگانی", "broadcast"),

        ("🚨 گزارش‌ها", "reports")
    ]

    for text, data in buttons:

        kb.add(
            telebot.types.InlineKeyboardButton(
                text,
                callback_data="admin_" + data
            )
        )

    bot.send_message(
        message.chat.id,
        "👑 پنل مدیریت",
        reply_markup=kb
    )


# ==================================================
# ADMIN STATS
# ==================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "admin_stats"
)
def admin_stats(call):

    if not is_admin(call.from_user.id):
        return

    bot.send_message(
        call.message.chat.id,
        f"""
📊 آمار ربات

👥 کاربران:
{len(users)}

💬 چت‌های فعال:
{len(active_chats)//2}

🔎 منتظر چت:
{len(waiting_users)}

🚨 گزارش‌ها:
{len(reports)}
"""
    )


# ==================================================
# ADMIN USERS
# ==================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "admin_users"
)
def admin_users(call):

    if not is_admin(call.from_user.id):
        return

    text = "👥 کاربران\n\n"

    for user in list(users.values())[:20]:

        text += (
            f"👤 {user['name']}\n"
            f"🔢 #{user['code']}\n"
            f"👑 {user['rank']}\n"
            f"⭐ Level {user['level']}\n"
            f"💰 {user['balance']:,}\n\n"
        )

    bot.send_message(
        call.message.chat.id,
        text
    )


# ==================================================
# ADMIN SEARCH
# ==================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "admin_search"
)
def admin_search(call):

    if not is_admin(call.from_user.id):
        return

    msg = bot.send_message(
        call.message.chat.id,
        "🔎 شماره ۴ رقمی را بفرست:"
    )

    bot.register_next_step_handler(
        msg,
        search_user
    )


def search_user(message):

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

📝 {found['name']}

🔢 #{found['code']}

🆔 Telegram ID:
{found['id']}

👑 {found['rank']}

⭐ Level:
{found['level']}

✨ XP:
{found['xp']}

🪙 سکه:
{found['coins']}

💰 پول:
{found['balance']:,}

🚫 Ban:
{found['banned']}
"""
    )


# ==================================================
# ADMIN ADD MONEY
# ==================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "admin_addmoney"
)
def add_money(call):

    if not is_admin(call.from_user.id):
        return

    msg = bot.send_message(
        call.message.chat.id,
        "شماره کاربر و مبلغ را بفرست.\n\n"
        "مثال:\n"
        "1234 50000"
    )

    bot.register_next_step_handler(
        msg,
        process_add_money
    )


def process_add_money(message):

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


# ==================================================
# ADMIN REMOVE MONEY
# ==================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "admin_removemoney"
)
def remove_money(call):

    if not is_admin(call.from_user.id):
        return

    msg = bot.send_message(
        call.message.chat.id,
        "شماره کاربر و مبلغ را بفرست."
    )

    bot.register_next_step_handler(
        msg,
        process_remove_money
    )


def process_remove_money(message):

    if not is_admin(message.from_user.id):
        return

    try:

        code, amount = message.text.split()

        amount = int(amount)

    except:

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


# ==================================================
# ADMIN XP
# ==================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "admin_xp"
)
def admin_xp(call):

    if not is_admin(call.from_user.id):
        return

    msg = bot.send_message(
        call.message.chat.id,
        "شماره کاربر و XP را بفرست.\n\n"
        "مثال:\n"
        "1234 500"
    )

    bot.register_next_step_handler(
        msg,
        process_xp
    )


def process_xp(message):

    if not is_admin(message.from_user.id):
        return

    try:

        code, amount = message.text.split()

        amount = int(amount)

    except:

        return

    for user in users.values():

        if user["code"] == code:

            user["xp"] = max(
                0,
                user["xp"] + amount
            )

            bot.send_message(
                message.chat.id,
                "✅ XP تغییر کرد."
            )

            return


# ==================================================
# ADMIN COINS
# ==================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "admin_coins"
)
def admin_coins(call):

    if not is_admin(call.from_user.id):
        return

    msg = bot.send_message(
        call.message.chat.id,
        "شماره کاربر و مقدار سکه را بفرست."
    )

    bot.register_next_step_handler(
        msg,
        process_coins
    )


def process_coins(message):

    if not is_admin(message.from_user.id):
        return

    try:

        code, amount = message.text.split()

        amount = int(amount)

    except:

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


# ==================================================
# ADMIN RANK
# ==================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "admin_rank"
)
def admin_rank(call):

    if not is_admin(call.from_user.id):
        return

    msg = bot.send_message(
        call.message.chat.id,
        """
شماره کاربر و رتبه را بفرست.

مثال:

1234 Gold

رتبه‌ها:

Member
Silver
Gold
Diamond
"""
    )

    bot.register_next_step_handler(
        msg,
        process_rank
    )


def process_rank(message):

    if not is_admin(message.from_user.id):
        return

    try:

        code, rank = message.text.split()

    except:

        return

    if rank not in [
        "Member",
        "Silver",
        "Gold",
        "Diamond"
    ]:

        bot.send_message(
            message.chat.id,
            "❌ رتبه اشتباه."
        )

        return

    for user in users.values():

        if user["code"] == code:

            user["rank"] = rank

            bot.send_message(
                message.chat.id,
                "✅ رتبه تغییر کرد."
            )

            return


# ==================================================
# ADMIN BAN
# ==================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "admin_ban"
)
def admin_ban(call):

    if not is_admin(call.from_user.id):
        return

    msg = bot.send_message(
        call.message.chat.id,
        """
شماره کاربر و وضعیت را بفرست.

مثال:

1234 ban

یا:

1234 unban
"""
    )

    bot.register_next_step_handler(
        msg,
        process_ban
    )


def process_ban(message):

    if not is_admin(message.from_user.id):
        return

    try:

        code, action = message.text.split()

    except:

        return

    for user in users.values():

        if user["code"] == code:

            user["banned"] = (
                action.lower() == "ban"
            )

            bot.send_message(
                message.chat.id,
                "✅ انجام شد."
            )

            return


# ==================================================
# ADMIN BROADCAST
# ==================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "admin_broadcast"
)
def broadcast(call):

    if not is_admin(call.from_user.id):
        return

    msg = bot.send_message(
        call.message.chat.id,
        "📢 پیام همگانی را بفرست:"
    )

    bot.register_next_step_handler(
        msg,
        send_broadcast
    )


def send_broadcast(message):

    if not is_admin(message.from_user.id):
        return

    sent = 0

    for user in users.values():

        try:

            bot.send_message(
                user["id"],
                "📢 پیام مدیریت:\n\n"
                + message.text
            )

            sent += 1

            time.sleep(0.05)

        except:
            pass

    bot.send_message(
        message.chat.id,
        f"✅ برای {sent} نفر ارسال شد."
    )


# ==================================================
# ADMIN REPORTS
# ==================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "admin_reports"
)
def admin_reports(call):

    if not is_admin(call.from_user.id):
        return

    if not reports:

        bot.send_message(
            call.message.chat.id,
            "✅ گزارشی وجود ندارد."
        )

        return

    text = "🚨 گزارش‌ها\n\n"

    for r in reports:

        reporter = users.get(
            r["reporter"]
        )

        reported = users.get(
            r["reported"]
        )

        text += (
            f"👤 گزارش‌دهنده: "
            f"{reporter['name'] if reporter else '?'}\n"
            f"🚨 کاربر: "
            f"{reported['name'] if reported else '?'}\n"
            f"━━━━━━━━━━━━\n"
        )

    bot.send_message(
        call.message.chat.id,
        text
    )


# ==================================================
# تنظیمات
# ==================================================

@bot.message_handler(
    func=lambda m: m.text == "⚙️ تنظیمات"
)
def settings(message):

    bot.send_message(
        message.chat.id,
        """
⚙️ تنظیمات

🔔 اعلان‌ها
🛡️ حریم خصوصی
🚫 کاربران مسدودشده

نسخه آزمایشی.
"""
    )


# ==================================================
# جوایز
# ==================================================

@bot.message_handler(
    func=lambda m: m.text == "🎁 جوایز"
)
def rewards(message):

    user = get_user(
        message.from_user.id
    )

    needed = xp_needed(
        user["level"]
    )

    remaining = max(
        0,
        needed - user["xp"]
    )

    bot.send_message(
        message.chat.id,
        f"""
🎁 جوایز

⭐ Level:
{user['level']}

✨ XP باقی‌مانده:
{remaining}

🎁 با Level بالاتر سکه جایزه می‌گیری!
"""
    )


# ==================================================
# اجرا
# ==================================================

print("🔥 STREAMER BOT STARTED")

bot.infinity_polling(
    timeout=60,
    long_polling_timeout=60
)
