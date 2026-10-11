import sqlite3
import random
import time
from datetime import datetime, date

import telebot
from telebot import types


# =========================================================
# تنظیمات
# =========================================================

BOT_TOKEN = "8978005144:AAGforuwqrN_oF880nVOT5VyWnSMiqxrPVM"

ADMIN_ID = 7723971526

DELETE_ACCOUNT_PRICE = 30000

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)


# =========================================================
# DATABASE
# =========================================================

DB_NAME = "bot.db"

db = sqlite3.connect(
    DB_NAME,
    check_same_thread=False
)

db.row_factory = sqlite3.Row


def execute(query, params=(), commit=True):

    cursor = db.cursor()

    cursor.execute(
        query,
        params
    )

    if commit:
        db.commit()

    return cursor


def init_database():

    execute("""
    CREATE TABLE IF NOT EXISTS users (
        tg_id INTEGER PRIMARY KEY,
        public_id INTEGER UNIQUE,
        username TEXT,
        name TEXT,
        coins INTEGER DEFAULT 100,
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        rank TEXT DEFAULT 'Member',
        banned INTEGER DEFAULT 0,
        ban_reason TEXT DEFAULT '',
        created_at TEXT,
        last_daily TEXT DEFAULT '',
        daily_streak INTEGER DEFAULT 0
    )
    """)

    execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user1 INTEGER,
        user2 INTEGER,
        active INTEGER DEFAULT 1,
        anonymous INTEGER DEFAULT 1,
        created_at TEXT
    )
    """)

    execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        sender INTEGER,
        receiver INTEGER,
        text TEXT,
        created_at TEXT
    )
    """)

    execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reporter INTEGER,
        reported INTEGER,
        chat_id INTEGER,
        reason TEXT,
        created_at TEXT,
        status TEXT DEFAULT 'open'
    )
    """)

    execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item TEXT,
        amount INTEGER DEFAULT 1
    )
    """)

    execute("""
    CREATE TABLE IF NOT EXISTS deleted_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        old_public_id INTEGER,
        deleted_at TEXT
    )
    """)


init_database()


# =========================================================
# RANK
# =========================================================

RANKS = {
    "Member": {
        "level": 1,
        "games": 2,
        "missions": 2,
        "discount": 0
    },

    "Bronze": {
        "level": 5,
        "games": 4,
        "missions": 4,
        "discount": 5
    },

    "Silver": {
        "level": 10,
        "games": 6,
        "missions": 6,
        "discount": 10
    },

    "Gold": {
        "level": 20,
        "games": 10,
        "missions": 10,
        "discount": 15
    },

    "Diamond": {
        "level": 35,
        "games": 15,
        "missions": 15,
        "discount": 20
    },

    "VIP": {
        "level": 50,
        "games": 20,
        "missions": 20,
        "discount": 30
    }
}


def calculate_rank(level):

    if level >= 50:
        return "VIP"

    if level >= 35:
        return "Diamond"

    if level >= 20:
        return "Gold"

    if level >= 10:
        return "Silver"

    if level >= 5:
        return "Bronze"

    return "Member"


# =========================================================
# USER
# =========================================================

def get_user(tg_id):

    return execute(
        """
        SELECT *
        FROM users
        WHERE tg_id = ?
        """,
        (tg_id,),
        False
    ).fetchone()


def get_user_by_public_id(public_id):

    return execute(
        """
        SELECT *
        FROM users
        WHERE public_id = ?
        """,
        (public_id,),
        False
    ).fetchone()


def get_next_public_id():

    row = execute(
        """
        SELECT MAX(public_id) AS max_id
        FROM users
        """,
        (),
        False
    ).fetchone()

    if row["max_id"] is None:
        return 1

    return row["max_id"] + 1


def register_user(message):

    tg_id = message.from_user.id

    user = get_user(tg_id)

    if user:
        return user

    public_id = get_next_public_id()

    username = message.from_user.username or ""

    name = (
        message.from_user.first_name
        or "کاربر"
    )

    execute(
        """
        INSERT INTO users
        (
            tg_id,
            public_id,
            username,
            name,
            coins,
            xp,
            level,
            rank,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            tg_id,
            public_id,
            username,
            name,
            100,
            0,
            1,
            "Member",
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )
    )

    return get_user(tg_id)


# =========================================================
# ACCESS
# =========================================================

def check_access(message):

    user = get_user(
        message.from_user.id
    )

    if not user:

        user = register_user(message)

    if user["banned"]:

        reason = (
            user["ban_reason"]
            or "بدون دلیل"
        )

        bot.send_message(
            message.chat.id,
            f"""
🚫 <b>شما بن شده‌اید.</b>

دلیل:
<code>{reason}</code>

تا زمانی که مدیریت شما را آن‌بن نکند،
امکان استفاده از ربات را ندارید.
"""
        )

        return False

    return True


def admin_only(message):

    if message.from_user.id != ADMIN_ID:

        bot.send_message(
            message.chat.id,
            "⛔ شما مدیر ربات نیستید."
        )

        return False

    return True


# =========================================================
# XP
# =========================================================

def required_xp(level):

    return level * 100


def add_xp(tg_id, amount):

    user = get_user(tg_id)

    if not user:
        return

    xp = user["xp"] + amount

    level = user["level"]

    while xp >= required_xp(level):

        xp -= required_xp(level)

        level += 1

    rank = calculate_rank(level)

    execute(
        """
        UPDATE users
        SET xp = ?,
            level = ?,
            rank = ?
        WHERE tg_id = ?
        """,
        (
            xp,
            level,
            rank,
            tg_id
        )
    )


def add_coins(tg_id, amount):

    execute(
        """
        UPDATE users
        SET coins = coins + ?
        WHERE tg_id = ?
        """,
        (
            amount,
            tg_id
        )
    )


def remove_coins(tg_id, amount):

    execute(
        """
        UPDATE users
        SET coins = coins - ?
        WHERE tg_id = ?
        AND coins >= ?
        """,
        (
            amount,
            tg_id,
            amount
        )
    )


# =========================================================
# START
# =========================================================

@bot.message_handler(commands=["start"])
def start(message):

    if not check_access(message):
        return

    user = get_user(
        message.from_user.id
    )

    bot.send_message(
        message.chat.id,
        f"""
👋 <b>خوش اومدی {user["name"]}!</b>

🆔 شناسه:
<code>{user["public_id"]:04d}</code>

🪙 سکه:
<b>{user["coins"]}</b>

⭐ Level:
<b>{user["level"]}</b>

🏆 Rank:
<b>{user["rank"]}</b>

💬 برای شروع چت:
<code>/chat</code>

📋 برای دیدن دستورات:
<code>/</code>
"""
    )


# =========================================================
# /
# =========================================================

@bot.message_handler(
    func=lambda m:
        m.text is not None
        and m.text.strip() == "/"
)
def slash_commands(message):

    if not check_access(message):
        return

    bot.send_message(
        message.chat.id,
        """
📋 <b>دستورات ربات</b>

👤 <b>حساب</b>

/profile
/id
/name

💬 <b>چت ناشناس</b>

/chat
/next
/end
/reveal
/report
/block

🪙 <b>سکه</b>

/coins
/shop
/buy
/daily

🎮 <b>بازی</b>

/games
/guess
/rps

🎯 <b>مأموریت</b>

/missions

🏆 <b>رتبه</b>

/rank
/leaderboard

⚙️ <b>سایر</b>

/help

👑 <b>مدیریت</b>

/admin
"""
    )


@bot.message_handler(commands=["help"])
def help_command(message):

    slash_commands(message)


# =========================================================
# PROFILE
# =========================================================

@bot.message_handler(commands=["profile"])
def profile(message):

    if not check_access(message):
        return

    user = get_user(
        message.from_user.id
    )

    bot.send_message(
        message.chat.id,
        f"""
👤 <b>پروفایل</b>

📛 نام:
<b>{user["name"]}</b>

🆔 ID:
<code>{user["public_id"]:04d}</code>

🪙 سکه:
<b>{user["coins"]}</b>

⭐ Level:
<b>{user["level"]}</b>

✨ XP:
<b>{user["xp"]}/{required_xp(user["level"])}</b>

🏆 Rank:
<b>{user["rank"]}</b>
"""
    )


@bot.message_handler(commands=["id"])
def user_id(message):

    if not check_access(message):
        return

    user = get_user(
        message.from_user.id
    )

    bot.send_message(
        message.chat.id,
        f"""
🆔 شناسه شما:

<code>{user["public_id"]:04d}</code>
"""
    )


# =========================================================
# NAME
# =========================================================

@bot.message_handler(commands=["name"])
def change_name(message):

    if not check_access(message):
        return

    parts = message.text.split(
        maxsplit=1
    )

    if len(parts) != 2:

        bot.send_message(
            message.chat.id,
            """
❌ روش استفاده:

<code>/name اسم جدید</code>
"""
        )

        return

    name = parts[1].strip()

    if len(name) > 30:

        bot.send_message(
            message.chat.id,
            "❌ نام حداکثر ۳۰ کاراکتر باشد."
        )

        return

    execute(
        """
        UPDATE users
        SET name = ?
        WHERE tg_id = ?
        """,
        (
            name,
            message.from_user.id
        )
    )

    bot.send_message(
        message.chat.id,
        f"✅ نام شما شد: <b>{name}</b>"
    )


# =========================================================
# COINS
# =========================================================

@bot.message_handler(commands=["coins"])
def coins(message):

    if not check_access(message):
        return

    user = get_user(
        message.from_user.id
    )

    bot.send_message(
        message.chat.id,
        f"""
🪙 موجودی شما:

<b>{user["coins"]}</b> سکه
"""
    )


# =========================================================
# DAILY
# =========================================================

@bot.message_handler(commands=["daily"])
def daily(message):

    if not check_access(message):
        return

    user = get_user(
        message.from_user.id
    )

    today = date.today().isoformat()

    if user["last_daily"] == today:

        bot.send_message(
            message.chat.id,
            "⏳ پاداش امروز را قبلاً گرفتی."
        )

        return

    streak = user["daily_streak"] + 1

    reward = min(
        100 + streak * 25,
        500
    )

    execute(
        """
        UPDATE users
        SET coins = coins + ?,
            last_daily = ?,
            daily_streak = ?
        WHERE tg_id = ?
        """,
        (
            reward,
            today,
            streak,
            message.from_user.id
        )
    )

    add_xp(
        message.from_user.id,
        20
    )

    bot.send_message(
        message.chat.id,
        f"""
🎁 <b>پاداش روزانه</b>

🪙 +{reward} سکه
⭐ +20 XP
🔥 Streak: {streak}
"""
    )


# =========================================================
# SHOP
# =========================================================

SHOP = {
    "xp": (
        "⭐ بسته XP",
        1000
    ),

    "boost": (
        "🚀 بوست چت",
        2500
    ),

    "reveal": (
        "👁️ خروج از ناشناس",
        3000
    )
}


@bot.message_handler(commands=["shop"])
def shop(message):

    if not check_access(message):
        return

    text = """
🛒 <b>فروشگاه</b>

"""

    for key, data in SHOP.items():

        name, price = data

        text += (
            f"{name}\n"
            f"🪙 قیمت: {price}\n"
            f"خرید: <code>/buy {key}</code>\n\n"
        )

    text += f"""
🗑 <b>حذف کامل حساب</b>

قیمت:
<b>{DELETE_ACCOUNT_PRICE:,} تومان</b>

برای پرداخت واقعی باید درگاه پرداخت متصل شود.
"""

    bot.send_message(
        message.chat.id,
        text
    )


@bot.message_handler(commands=["buy"])
def buy(message):

    if not check_access(message):
        return

    parts = message.text.split()

    if len(parts) != 2:

        bot.send_message(
            message.chat.id,
            "مثال:\n<code>/buy xp</code>"
        )

        return

    key = parts[1]

    if key not in SHOP:

        bot.send_message(
            message.chat.id,
            "❌ محصول پیدا نشد."
        )

        return

    name, price = SHOP[key]

    user = get_user(
        message.from_user.id
    )

    if user["coins"] < price:

        bot.send_message(
            message.chat.id,
            "❌ سکه کافی نداری."
        )

        return

    remove_coins(
        message.from_user.id,
        price
    )

    if key == "xp":

        add_xp(
            message.from_user.id,
            500
        )

    elif key == "boost":

        execute(
            """
            INSERT INTO inventory
            (user_id, item, amount)
            VALUES (?, ?, 1)
            """,
            (
                message.from_user.id,
                "chat_boost"
            )
        )

    elif key == "reveal":

        execute(
            """
            INSERT INTO inventory
            (user_id, item, amount)
            VALUES (?, ?, 1)
            """,
            (
                message.from_user.id,
                "reveal"
            )
        )

    bot.send_message(
        message.chat.id,
        f"✅ <b>{name}</b> خریداری شد."
    )


# =========================================================
# CHAT FUNCTIONS
# =========================================================

def active_chat(tg_id):

    return execute(
        """
        SELECT *
        FROM chats
        WHERE active = 1
        AND (
            user1 = ?
            OR user2 = ?
        )
        LIMIT 1
        """,
        (
            tg_id,
            tg_id
        ),
        False
    ).fetchone()


def partner_of(chat, tg_id):

    if chat["user1"] == tg_id:
        return chat["user2"]

    return chat["user1"]


def close_chat(chat_id):

    execute(
        """
        UPDATE chats
        SET active = 0
        WHERE id = ?
        """,
        (chat_id,)
    )


def find_waiting_user(tg_id):

    row = execute(
        """
        SELECT tg_id
        FROM users
        WHERE tg_id != ?
        AND banned = 0
        AND tg_id NOT IN
        (
            SELECT user1
            FROM chats
            WHERE active = 1

            UNION

            SELECT user2
            FROM chats
            WHERE active = 1
        )
        ORDER BY RANDOM()
        LIMIT 1
        """,
        (tg_id,),
        False
    ).fetchone()

    if row:
        return row["tg_id"]

    return None


def create_chat(user1, user2):

    cursor = execute(
        """
        INSERT INTO chats
        (
            user1,
            user2,
            active,
            anonymous,
            created_at
        )
        VALUES (?, ?, 1, 1, ?)
        """,
        (
            user1,
            user2,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )
    )

    return cursor.lastrowid


# =========================================================
# CHAT
# =========================================================

@bot.message_handler(commands=["chat"])
def chat(message):

    if not check_access(message):
        return

    tg_id = message.from_user.id

    if active_chat(tg_id):

        bot.send_message(
            message.chat.id,
            "❌ شما در حال حاضر داخل یک چت هستید."
        )

        return

    partner = find_waiting_user(
        tg_id
    )

    if not partner:

        bot.send_message(
            message.chat.id,
            """
🔎 <b>کسی پیدا نشد.</b>

چند لحظه بعد دوباره:

<code>/chat</code>
"""
        )

        return

    create_chat(
        tg_id,
        partner
    )

    bot.send_message(
        tg_id,
        """
🎉 <b>شخصی پیدا شد!</b>

💬 شروع کن به صحبت کردن.

برای شخص بعدی:
<code>/next</code>

پایان:
<code>/end</code>

گزارش:
<code>/report</code>
"""
    )

    bot.send_message(
        partner,
        """
🎉 <b>شخصی پیدا شد!</b>

💬 شروع کن به صحبت کردن.

برای شخص بعدی:
<code>/next</code>

پایان:
<code>/end</code>

گزارش:
<code>/report</code>
"""
    )


# =========================================================
# END
# =========================================================

@bot.message_handler(commands=["end"])
def end(message):

    if not check_access(message):
        return

    tg_id = message.from_user.id

    chat = active_chat(tg_id)

    if not chat:

        bot.send_message(
            message.chat.id,
            "❌ شما در چت نیستید."
        )

        return

    partner = partner_of(
        chat,
        tg_id
    )

    close_chat(
        chat["id"]
    )

    bot.send_message(
        tg_id,
        "✅ چت پایان یافت."
    )

    try:

        bot.send_message(
            partner,
            "❌ طرف مقابل چت را پایان داد."
        )

    except Exception:
        pass

    add_xp(
        tg_id,
        50
    )


# =========================================================
# NEXT
# =========================================================

@bot.message_handler(commands=["next"])
def next_chat(message):

    if not check_access(message):
        return

    tg_id = message.from_user.id

    old_chat = active_chat(
        tg_id
    )

    if old_chat:

        partner = partner_of(
            old_chat,
            tg_id
        )

        close_chat(
            old_chat["id"]
        )

        try:

            bot.send_message(
                partner,
                "❌ طرف مقابل به نفر بعدی رفت."
            )

        except Exception:
            pass

    partner = find_waiting_user(
        tg_id
    )

    if not partner:

        bot.send_message(
            tg_id,
            "🔎 فعلاً کسی پیدا نشد."
        )

        return

    create_chat(
        tg_id,
        partner
    )

    bot.send_message(
        tg_id,
        "🎉 نفر جدید پیدا شد!"
    )

    bot.send_message(
        partner,
        "🎉 نفر جدید پیدا شد!"
    )


# =========================================================
# REVEAL
# =========================================================

@bot.message_handler(commands=["reveal"])
def reveal(message):

    if not check_access(message):
        return

    chat = active_chat(
        message.from_user.id
    )

    if not chat:

        bot.send_message(
            message.chat.id,
            "❌ شما داخل چت نیستید."
        )

        return

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "✅ بله",
            callback_data=f"reveal_yes_{chat['id']}"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "❌ لغو",
            callback_data=f"reveal_no_{chat['id']}"
        )
    )

    bot.send_message(
        message.chat.id,
        """
⚠️ <b>خروج از حالت ناشناس</b>

در صورت تأیید، اطلاعات پروفایل شما برای طرف مقابل نمایش داده می‌شود.

تأیید می‌کنی؟
""",
        reply_markup=keyboard
    )


@bot.callback_query_handler(
    func=lambda call:
        call.data.startswith("reveal_")
)
def reveal_callback(call):

    parts = call.data.split("_")

    action = parts[1]

    chat_id = int(parts[2])

    chat = execute(
        """
        SELECT *
        FROM chats
        WHERE id = ?
        AND active = 1
        """,
        (chat_id,),
        False
    ).fetchone()

    if not chat:

        bot.answer_callback_query(
            call.id,
            "چت فعال نیست."
        )

        return

    tg_id = call.from_user.id

    if tg_id not in (
        chat["user1"],
        chat["user2"]
    ):

        bot.answer_callback_query(
            call.id,
            "دسترسی ندارید."
        )

        return

    if action == "no":

        bot.edit_message_text(
            "❌ لغو شد.",
            call.message.chat.id,
            call.message.message_id
        )

        return

    partner = partner_of(
        chat,
        tg_id
    )

    user = get_user(tg_id)

    bot.send_message(
        partner,
        f"""
👤 <b>اطلاعات طرف مقابل</b>

📛 نام:
<b>{user["name"]}</b>

🆔 ID:
<code>{user["public_id"]:04d}</code>

🏆 Rank:
<b>{user["rank"]}</b>

⭐ Level:
<b>{user["level"]}</b>
"""
    )

    bot.send_message(
        tg_id,
        "✅ اطلاعات شما برای طرف مقابل نمایش داده شد."
    )

    bot.answer_callback_query(
        call.id,
        "انجام شد."
    )


# =========================================================
# REPORT
# =========================================================

@bot.message_handler(commands=["report"])
def report(message):

    if not check_access(message):
        return

    chat = active_chat(
        message.from_user.id
    )

    if not chat:

        bot.send_message(
            message.chat.id,
            "❌ شما داخل چت نیستید."
        )

        return

    partner = partner_of(
        chat,
        message.from_user.id
    )

    execute(
        """
        INSERT INTO reports
        (
            reporter,
            reported,
            chat_id,
            reason,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            message.from_user.id,
            partner,
            chat["id"],
            "گزارش کاربر",
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )
    )

    bot.send_message(
        message.chat.id,
        "🚨 گزارش برای مدیریت ثبت شد."
    )


# =========================================================
# BLOCK
# =========================================================

@bot.message_handler(commands=["block"])
def block(message):

    if not check_access(message):
        return

    chat = active_chat(
        message.from_user.id
    )

    if not chat:

        bot.send_message(
            message.chat.id,
            "❌ شما داخل چت نیستید."
        )

        return

    partner = partner_of(
        chat,
        message.from_user.id
    )

    close_chat(
        chat["id"]
    )

    execute(
        """
        INSERT INTO inventory
        (
            user_id,
            item,
            amount
        )
        VALUES (?, ?, 1)
        """,
        (
            message.from_user.id,
            f"blocked:{partner}"
        )
    )

    bot.send_message(
        message.chat.id,
        "🚫 کاربر بلاک شد."
    )

    try:

        bot.send_message(
            partner,
            "❌ طرف مقابل چت را پایان داد."
        )

    except Exception:
        pass


# =========================================================
# GAMES
# =========================================================

@bot.message_handler(commands=["games"])
def games(message):

    if not check_access(message):
        return

    bot.send_message(
        message.chat.id,
        """
🎮 <b>بازی‌ها</b>

🔢 حدس عدد:

<code>/guess 5</code>

✊ سنگ کاغذ قیچی:

<code>/rps سنگ</code>
"""
    )


@bot.message_handler(commands=["guess"])
def guess(message):

    if not check_access(message):
        return

    parts = message.text.split()

    if len(parts) != 2:

        bot.send_message(
            message.chat.id,
            "مثال: <code>/guess 5</code>"
        )

        return

    try:
        number = int(parts[1])
    except:

        bot.send_message(
            message.chat.id,
            "❌ عدد وارد کن."
        )

        return

    if not 1 <= number <= 10:

        bot.send_message(
            message.chat.id,
            "عدد باید بین ۱ تا ۱۰ باشد."
        )

        return

    target = random.randint(
        1,
        10
    )

    if number == target:

        add_coins(
            message.from_user.id,
            500
        )

        add_xp(
            message.from_user.id,
            100
        )

        bot.send_message(
            message.chat.id,
            f"""
🎉 <b>بردی!</b>

عدد:
<b>{target}</b>

🪙 +500
⭐ +100 XP
"""
        )

    else:

        add_xp(
            message.from_user.id,
            20
        )

        bot.send_message(
            message.chat.id,
            f"""
❌ باختی!

عدد درست:
<b>{target}</b>

⭐ +20 XP
"""
        )


@bot.message_handler(commands=["rps"])
def rps(message):

    if not check_access(message):
        return

    parts = message.text.split()

    if len(parts) != 2:

        bot.send_message(
            message.chat.id,
            "مثال: <code>/rps سنگ</code>"
        )

        return

    user_choice = parts[1]

    choices = [
        "سنگ",
        "کاغذ",
        "قیچی"
    ]

    if user_choice not in choices:

        bot.send_message(
            message.chat.id,
            "سنگ، کاغذ یا قیچی را وارد کن."
        )

        return

    bot_choice = random.choice(
        choices
    )

    if user_choice == bot_choice:

        result = "مساوی 😐"

    elif (
        user_choice == "سنگ"
        and bot_choice == "قیچی"
    ) or (
        user_choice == "کاغذ"
        and bot_choice == "سنگ"
    ) or (
        user_choice == "قیچی"
        and bot_choice == "کاغذ"
    ):

        result = "🎉 بردی"

        add_coins(
            message.from_user.id,
            150
        )

        add_xp(
            message.from_user.id,
            50
        )

    else:

        result = "😅 باختی"

        add_xp(
            message.from_user.id,
            10
        )

    bot.send_message(
        message.chat.id,
        f"""
✊ شما: {user_choice}

🤖 ربات: {bot_choice}

<b>{result}</b>
"""
    )


# =========================================================
# MISSIONS
# =========================================================

@bot.message_handler(commands=["missions"])
def missions(message):

    if not check_access(message):
        return

    user = get_user(
        message.from_user.id
    )

    bot.send_message(
        message.chat.id,
        f"""
🎯 <b>مأموریت‌ها</b>

🏆 رتبه:
<b>{user["rank"]}</b>

1️⃣ یک چت انجام بده
🎁 100 سکه + 50 XP

2️⃣ یک بازی انجام بده
🎁 150 سکه + 75 XP

3️⃣ پاداش روزانه بگیر
🎁 200 سکه + 100 XP

برای انجام مأموریت‌ها فعالیت کن.
"""
    )


# =========================================================
# RANK
# =========================================================

@bot.message_handler(commands=["rank"])
def rank(message):

    if not check_access(message):
        return

    user = get_user(
        message.from_user.id
    )

    info = RANKS[
        user["rank"]
    ]

    bot.send_message(
        message.chat.id,
        f"""
🏆 <b>رتبه شما</b>

<b>{user["rank"]}</b>

⭐ Level:
{user["level"]}

✨ XP:
{user["xp"]}/{required_xp(user["level"])}

🎮 بازی:
{info["games"]}

🎯 مأموریت:
{info["missions"]}

🛒 تخفیف:
{info["discount"]}%
"""
    )


# =========================================================
# LEADERBOARD
# =========================================================

@bot.message_handler(commands=["leaderboard"])
def leaderboard(message):

    if not check_access(message):
        return

    rows = execute(
        """
        SELECT *
        FROM users
        WHERE banned = 0
        ORDER BY level DESC, xp DESC
        LIMIT 10
        """,
        (),
        False
    ).fetchall()

    text = "🏆 <b>برترین کاربران</b>\n\n"

    for i, user in enumerate(
        rows,
        1
    ):

        text += (
            f"{i}. "
            f"{user['name']} "
            f"• Lv.{user['level']} "
            f"• {user['rank']}\n"
        )

    bot.send_message(
        message.chat.id,
        text
    )


# =========================================================
# ADMIN PANEL
# =========================================================

@bot.message_handler(commands=["admin"])
def admin(message):

    if not admin_only(message):
        return

    bot.send_message(
        message.chat.id,
        """
👑 <b>پنل مدیریت</b>

🚫 بن:
/ban ID دلیل

✅ آن‌بن:
/unban ID

👤 اطلاعات:
/userinfo ID

🪙 سکه:
/addcoins ID مقدار
/removecoins ID مقدار

⭐ XP:
/addxp ID مقدار

🏆 رتبه:
/setrank ID Rank

📛 نام:
/setname ID نام

🚨 گزارش‌ها:
/reports

📜 لاگ چت:
/log ChatID

📊 آمار:
/stats
"""
    )


# =========================================================
# BAN
# =========================================================

@bot.message_handler(commands=["ban"])
def ban(message):

    if not admin_only(message):
        return

    parts = message.text.split(
        maxsplit=2
    )

    if len(parts) < 2:
        return

    try:
        public_id = int(parts[1])
    except:
        return

    reason = (
        parts[2]
        if len(parts) == 3
        else "بدون دلیل"
    )

    user = get_user_by_public_id(
        public_id
    )

    if not user:

        bot.send_message(
            message.chat.id,
            "❌ کاربر پیدا نشد."
        )

        return

    execute(
        """
        UPDATE users
        SET banned = 1,
            ban_reason = ?
        WHERE tg_id = ?
        """,
        (
            reason,
            user["tg_id"]
        )
    )

    # اگر داخل چت بود، چت را ببند
    chat = active_chat(
        user["tg_id"]
    )

    if chat:

        partner = partner_of(
            chat,
            user["tg_id"]
        )

        close_chat(
            chat["id"]
        )

        try:
            bot.send_message(
                partner,
                "❌ چت به دلیل مسدود شدن طرف مقابل پایان یافت."
            )
        except:
            pass

    bot.send_message(
        message.chat.id,
        f"🚫 کاربر <code>{public_id:04d}</code> بن شد."
    )


# =========================================================
# UNBAN
# =========================================================

@bot.message_handler(commands=["unban"])
def unban(message):

    if not admin_only(message):
        return

    parts = message.text.split()

    if len(parts) != 2:
        return

    try:
        public_id = int(parts[1])
    except:
        return

    user = get_user_by_public_id(
        public_id
    )

    if not user:
        return

    execute(
        """
        UPDATE users
        SET banned = 0,
            ban_reason = ''
        WHERE tg_id = ?
        """,
        (
            user["tg_id"],
        )
    )

    bot.send_message(
        message.chat.id,
        f"✅ کاربر <code>{public_id:04d}</code> آن‌بن شد."
    )


# =========================================================
# USERINFO
# =========================================================

@bot.message_handler(commands=["userinfo"])
def userinfo(message):

    if not admin_only(message):
        return

    parts = message.text.split()

    if len(parts) != 2:
        return

    user = get_user_by_public_id(
        int(parts[1])
    )

    if not user:
        return

    bot.send_message(
        message.chat.id,
        f"""
👤 <b>اطلاعات کاربر</b>

ID:
<code>{user["public_id"]:04d}</code>

Telegram ID:
<code>{user["tg_id"]}</code>

نام:
{user["name"]}

🪙 سکه:
{user["coins"]}

⭐ XP:
{user["xp"]}

Level:
{user["level"]}

Rank:
{user["rank"]}

Ban:
{bool(user["banned"])}

تاریخ ثبت‌نام:
{user["created_at"]}
"""
    )


# =========================================================
# ADMIN COINS
# =========================================================

@bot.message_handler(commands=["addcoins"])
def addcoins_admin(message):

    if not admin_only(message):
        return

    parts = message.text.split()

    if len(parts) != 3:
        return

    user = get_user_by_public_id(
        int(parts[1])
    )

    amount = int(parts[2])

    if not user:
        return

    add_coins(
        user["tg_id"],
        amount
    )

    bot.send_message(
        message.chat.id,
        "✅ سکه اضافه شد."
    )


@bot.message_handler(commands=["removecoins"])
def removecoins_admin(message):

    if not admin_only(message):
        return

    parts = message.text.split()

    if len(parts) != 3:
        return

    user = get_user_by_public_id(
        int(parts[1])
    )

    amount = int(parts[2])

    if not user:
        return

    remove_coins(
        user["tg_id"],
        amount
    )

    bot.send_message(
        message.chat.id,
        "✅ سکه کم شد."
    )


# =========================================================
# ADMIN XP
# =========================================================

@bot.message_handler(commands=["addxp"])
def addxp_admin(message):

    if not admin_only(message):
        return

    parts = message.text.split()

    if len(parts) != 3:
        return

    user = get_user_by_public_id(
        int(parts[1])
    )

    amount = int(parts[2])

    if not user:
        return

    add_xp(
        user["tg_id"],
        amount
    )

    bot.send_message(
        message.chat.id,
        "✅ XP اضافه شد."
    )


# =========================================================
# SET RANK
# =========================================================

@bot.message_handler(commands=["setrank"])
def setrank(message):

    if not admin_only(message):
        return

    parts = message.text.split()

    if len(parts) != 3:
        return

    public_id = int(parts[1])

    rank_name = parts[2]

    if rank_name not in RANKS:

        bot.send_message(
            message.chat.id,
            "رتبه‌های مجاز:\n" +
            "\n".join(
                RANKS.keys()
            )
        )

        return

    user = get_user_by_public_id(
        public_id
    )

    if not user:
        return

    execute(
        """
        UPDATE users
        SET rank = ?
        WHERE tg_id = ?
        """,
        (
            rank_name,
            user["tg_id"]
        )
    )

    bot.send_message(
        message.chat.id,
        "✅ رتبه تغییر کرد."
    )


# =========================================================
# SET NAME
# =========================================================

@bot.message_handler(commands=["setname"])
def setname(message):

    if not admin_only(message):
        return

    parts = message.text.split(
        maxsplit=2
    )

    if len(parts) != 3:
        return

    public_id = int(parts[1])

    name = parts[2]

    user = get_user_by_public_id(
        public_id
    )

    if not user:
        return

    execute(
        """
        UPDATE users
        SET name = ?
        WHERE tg_id = ?
        """,
        (
            name,
            user["tg_id"]
        )
    )

    bot.send_message(
        message.chat.id,
        "✅ نام تغییر کرد."
    )


# =========================================================
# REPORTS
# =========================================================

@bot.message_handler(commands=["reports"])
def reports(message):

    if not admin_only(message):
        return

    rows = execute(
        """
        SELECT *
        FROM reports
        WHERE status = 'open'
        ORDER BY id DESC
        LIMIT 20
        """,
        (),
        False
    ).fetchall()

    if not rows:

        bot.send_message(
            message.chat.id,
            "✅ گزارش جدیدی وجود ندارد."
        )

        return

    text = "🚨 <b>گزارش‌ها</b>\n\n"

    for row in rows:

        text += (
            f"#{row['id']}\n"
            f"Reporter: {row['reporter']}\n"
            f"Reported: {row['reported']}\n"
            f"Chat: {row['chat_id']}\n"
            f"Reason: {row['reason']}\n\n"
        )

    bot.send_message(
        message.chat.id,
        text
    )


# =========================================================
# CHAT LOG
# =========================================================

@bot.message_handler(commands=["log"])
def log_chat(message):

    if not admin_only(message):
        return

    parts = message.text.split()

    if len(parts) != 2:
        return

    chat_id = int(parts[1])

    rows = execute(
        """
        SELECT *
        FROM messages
        WHERE chat_id = ?
        ORDER BY id ASC
        """,
        (
            chat_id,
        ),
        False
    ).fetchall()

    if not rows:

        bot.send_message(
            message.chat.id,
            "❌ پیامی برای این چت ثبت نشده."
        )

        return

    text = (
        f"📜 <b>لاگ چت #{chat_id}</b>\n\n"
    )

    for row in rows:

        user = get_user(
            row["sender"]
        )

        name = (
            user["name"]
            if user
            else "کاربر"
        )

        text += (
            f"👤 <b>{name}</b>\n"
            f"{row['text']}\n"
            f"🕐 {row['created_at']}\n\n"
        )

    for i in range(
        0,
        len(text),
        4000
    ):

        bot.send_message(
            message.chat.id,
            text[i:i + 4000]
        )


# =========================================================
# STATS
# =========================================================

@bot.message_handler(commands=["stats"])
def stats(message):

    if not admin_only(message):
        return

    users = execute(
        "SELECT COUNT(*) AS c FROM users",
        (),
        False
    ).fetchone()["c"]

    banned = execute(
        """
        SELECT COUNT(*) AS c
        FROM users
        WHERE banned = 1
        """,
        (),
        False
    ).fetchone()["c"]

    chats = execute(
        """
        SELECT COUNT(*) AS c
        FROM chats
        WHERE active = 1
        """,
        (),
        False
    ).fetchone()["c"]

    bot.send_message(
        message.chat.id,
        f"""
📊 <b>آمار</b>

👥 کاربران:
{users}

🚫 بن‌شده:
{banned}

💬 چت فعال:
{chats}
"""
    )


# =========================================================
# DELETE ACCOUNT
# =========================================================

def delete_account(tg_id):

    user = get_user(tg_id)

    if not user:
        return False

    public_id = user["public_id"]

    # ذخیره فقط سابقه شماره برای جلوگیری از تداخل
    execute(
        """
        INSERT INTO deleted_accounts
        (
            old_public_id,
            deleted_at
        )
        VALUES (?, ?)
        """,
        (
            public_id,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )
    )

    # بستن چت فعال
    chat = active_chat(tg_id)

    if chat:

        partner = partner_of(
            chat,
            tg_id
        )

        close_chat(
            chat["id"]
        )

        try:

            bot.send_message(
                partner,
                "❌ طرف مقابل حساب خود را حذف کرد."
            )

        except:
            pass

    # حذف پیام‌ها
    execute(
        """
        DELETE FROM messages
        WHERE sender = ?
        OR receiver = ?
        """,
        (
            tg_id,
            tg_id
        )
    )

    # حذف گزارش‌ها
    execute(
        """
        DELETE FROM reports
        WHERE reporter = ?
        OR reported = ?
        """,
        (
            tg_id,
            tg_id
        )
    )

    # حذف inventory
    execute(
        """
        DELETE FROM inventory
        WHERE user_id = ?
        """,
        (
            tg_id,
        )
    )

    # حذف کاربر
    execute(
        """
        DELETE FROM users
        WHERE tg_id = ?
        """,
        (
            tg_id,
        )
    )

    return True


# =========================================================
# MESSAGE HANDLER
# =========================================================

@bot.message_handler(
    func=lambda m:
        m.text is not None
        and not m.text.startswith("/")
)
def normal_message(message):

    if not check_access(message):
        return

    tg_id = message.from_user.id

    chat = active_chat(
        tg_id
    )

    if not chat:
        return

    partner = partner_of(
        chat,
        tg_id
    )

    # لاگ
    execute(
        """
        INSERT INTO messages
        (
            chat_id,
            sender,
            receiver,
            text,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            chat["id"],
            tg_id,
            partner,
            message.text,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )
    )

    try:

        # فقط متن پیام فرستاده می‌شود
        # /end و دستورات اینجا نمی‌آیند
        bot.send_message(
            partner,
            message.text
        )

        add_xp(
            tg_id,
            5
        )

    except Exception:

        bot.send_message(
            tg_id,
            "❌ ارسال پیام انجام نشد."
        )


# =========================================================
# RUN
# =========================================================

print("BOT STARTED")

while True:

    try:

        bot.infinity_polling(
            timeout=30,
            long_polling_timeout=30
        )

    except Exception as error:

        print(
            "ERROR:",
            error
        )

        time.sleep(5)
