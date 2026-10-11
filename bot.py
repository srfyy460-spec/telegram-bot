import telebot
from telebot import types
import sqlite3
import time
import random

# =========================
# تنظیمات
# =========================

BOT_TOKEN = "8978005144:AAGforuwqrN_oF880nVOT5VyWnSMiqxrPVM"

ADMIN_ID = 7723971526

# برای پرداخت واقعی Telegram Payments
PAYMENT_PROVIDER_TOKEN = "توکن_درگاه_تلگرام_اینجا_بگذار"

# 30,000 تومان = 300,000 ریال
DELETE_PRICE_RIAL = 300000

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

DB = "bot.db"

# =========================
# دیتابیس
# =========================

def db():
    return sqlite3.connect(DB)

def init_db():
    con = db()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        tg_id INTEGER PRIMARY KEY,
        public_id INTEGER UNIQUE,
        name TEXT,
        username TEXT,
        coins INTEGER DEFAULT 100,
        xp INTEGER DEFAULT 0,
        rank TEXT DEFAULT 'عضو',
        banned INTEGER DEFAULT 0,
        created_at INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user1 INTEGER,
        user2 INTEGER,
        active INTEGER DEFAULT 1,
        created_at INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS waiting (
        tg_id INTEGER PRIMARY KEY,
        created_at INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        sender INTEGER,
        receiver INTEGER,
        text TEXT,
        created_at INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        tg_id INTEGER,
        item TEXT,
        amount INTEGER DEFAULT 0,
        PRIMARY KEY(tg_id, item)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reporter INTEGER,
        reported INTEGER,
        reason TEXT,
        created_at INTEGER,
        solved INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS missions (
        tg_id INTEGER,
        mission TEXT,
        progress INTEGER DEFAULT 0,
        completed INTEGER DEFAULT 0,
        PRIMARY KEY(tg_id, mission)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY CHECK(id=1),
        next_public_id INTEGER DEFAULT 1
    )
    """)

    cur.execute("SELECT id FROM settings WHERE id=1")

    if not cur.fetchone():
        cur.execute(
            "INSERT INTO settings(id,next_public_id) VALUES(1,1)"
        )

    con.commit()
    con.close()


init_db()

# =========================
# ابزارها
# =========================

def get_user(tg_id):
    con = db()
    cur = con.cursor()

    cur.execute(
        "SELECT * FROM users WHERE tg_id=?",
        (tg_id,)
    )

    user = cur.fetchone()
    con.close()

    return user


def is_banned(tg_id):
    user = get_user(tg_id)

    if not user:
        return False

    return user[6] == 1


def get_public_id(tg_id):
    user = get_user(tg_id)

    if not user:
        return None

    return user[1]


def register_user(message):
    tg_id = message.from_user.id

    if get_user(tg_id):
        return get_user(tg_id)

    con = db()
    cur = con.cursor()

    cur.execute(
        "SELECT next_public_id FROM settings WHERE id=1"
    )

    next_id = cur.fetchone()[0]

    if next_id > 100000:
        con.close()
        return None

    name = message.from_user.first_name or "کاربر"
    username = message.from_user.username or ""

    cur.execute("""
    INSERT INTO users
    (tg_id, public_id, name, username, coins, xp, rank, banned, created_at)
    VALUES (?, ?, ?, ?, 100, 0, 'عضو', 0, ?)
    """, (
        tg_id,
        next_id,
        name,
        username,
        int(time.time())
    ))

    cur.execute(
        "UPDATE settings SET next_public_id=? WHERE id=1",
        (next_id + 1,)
    )

    con.commit()
    con.close()

    return get_user(tg_id)


def update_name(tg_id, name):
    con = db()
    cur = con.cursor()

    cur.execute(
        "UPDATE users SET name=? WHERE tg_id=?",
        (name, tg_id)
    )

    con.commit()
    con.close()


def add_coins(tg_id, amount):
    con = db()
    cur = con.cursor()

    cur.execute(
        "UPDATE users SET coins=coins+? WHERE tg_id=?",
        (amount, tg_id)
    )

    con.commit()
    con.close()


def remove_coins(tg_id, amount):
    con = db()
    cur = con.cursor()

    cur.execute(
        "UPDATE users SET coins=coins-? WHERE tg_id=? AND coins>=?",
        (amount, tg_id, amount)
    )

    success = cur.rowcount > 0

    con.commit()
    con.close()

    return success


def add_xp(tg_id, amount):
    con = db()
    cur = con.cursor()

    cur.execute(
        "UPDATE users SET xp=xp+? WHERE tg_id=?",
        (amount, tg_id)
    )

    con.commit()
    con.close()

    update_rank(tg_id)


def update_rank(tg_id):
    user = get_user(tg_id)

    if not user:
        return

    xp = user[5]

    if xp >= 10000:
        rank = "الماسی"
    elif xp >= 5000:
        rank = "VIP"
    elif xp >= 2500:
        rank = "طلایی"
    elif xp >= 1000:
        rank = "نقره‌ای"
    elif xp >= 500:
        rank = "برنزی"
    else:
        rank = "عضو"

    con = db()
    cur = con.cursor()

    cur.execute(
        "UPDATE users SET rank=? WHERE tg_id=?",
        (rank, tg_id)
    )

    con.commit()
    con.close()


# =========================
# دکمه‌ها
# =========================

MAIN_BUTTONS = [
    "👤 پروفایل",
    "💬 چت ناشناس",
    "🪙 سکه‌ها",
    "🛒 فروشگاه",
    "🎁 جایزه روزانه",
    "🎯 مأموریت‌ها",
    "🎮 بازی‌ها",
    "🏆 رتبه‌بندی",
    "🆔 آیدی من",
    "✏️ تغییر نام",
    "🗑 حذف حساب",
    "❓ راهنما",
    "⚙️ تنظیمات"
]

CHAT_BUTTONS = [
    "⏭ نفر بعدی",
    "🛑 پایان چت",
    "👁 خروج از ناشناس",
    "🚨 گزارش",
    "🚫 بلاک"
]


def main_keyboard():
    kb = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=2
    )

    kb.add(
        "👤 پروفایل",
        "💬 چت ناشناس"
    )

    kb.add(
        "🪙 سکه‌ها",
        "🛒 فروشگاه"
    )

    kb.add(
        "🎁 جایزه روزانه",
        "🎯 مأموریت‌ها"
    )

    kb.add(
        "🎮 بازی‌ها",
        "🏆 رتبه‌بندی"
    )

    kb.add(
        "🆔 آیدی من",
        "✏️ تغییر نام"
    )

    kb.add(
        "🗑 حذف حساب",
        "⚙️ تنظیمات"
    )

    kb.add("❓ راهنما")

    return kb


def chat_keyboard():
    kb = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=2
    )

    kb.add(
        "⏭ نفر بعدی",
        "🛑 پایان چت"
    )

    kb.add(
        "👁 خروج از ناشناس",
        "🚨 گزارش"
    )

    kb.add("🚫 بلاک")

    return kb


def admin_keyboard():
    kb = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=2
    )

    kb.add(
        "📊 آمار",
        "🚨 گزارش‌ها"
    )

    kb.add(
        "👤 اطلاعات کاربر",
        "🚫 بن کاربر"
    )

    kb.add(
        "✅ آن‌بن کاربر",
        "🪙 افزودن سکه"
    )

    kb.add(
        "⭐ افزودن XP",
        "📜 لاگ چت"
    )

    kb.add(
        "📢 پیام همگانی"
    )

    kb.add("🏠 منوی اصلی")

    return kb


# =========================
# چک کاربر
# =========================

def check_user(message):
    user = get_user(message.from_user.id)

    if not user:
        register_user(message)
        user = get_user(message.from_user.id)

    if user and user[6] == 1:
        bot.send_message(
            message.chat.id,
            "🚫 حساب شما توسط مدیریت مسدود شده است."
        )
        return False

    return True


# =========================
# چت
# =========================

def get_active_chat(tg_id):
    con = db()
    cur = con.cursor()

    cur.execute("""
    SELECT id,user1,user2
    FROM chats
    WHERE active=1
    AND (user1=? OR user2=?)
    LIMIT 1
    """, (tg_id, tg_id))

    result = cur.fetchone()

    con.close()

    return result


def other_user(chat, tg_id):
    if chat[1] == tg_id:
        return chat[2]

    return chat[1]


def remove_waiting(tg_id):
    con = db()
    cur = con.cursor()

    cur.execute(
        "DELETE FROM waiting WHERE tg_id=?",
        (tg_id,)
    )

    con.commit()
    con.close()


def find_partner(tg_id):
    con = db()
    cur = con.cursor()

    cur.execute("""
    SELECT tg_id
    FROM waiting
    WHERE tg_id != ?
    ORDER BY created_at ASC
    LIMIT 1
    """, (tg_id,))

    result = cur.fetchone()

    if not result:
        con.close()
        return None

    partner = result[0]

    cur.execute(
        "DELETE FROM waiting WHERE tg_id IN (?,?)",
        (tg_id, partner)
    )

    cur.execute("""
    INSERT INTO chats(user1,user2,active,created_at)
    VALUES(?,?,1,?)
    """, (
        tg_id,
        partner,
        int(time.time())
    ))

    chat_id = cur.lastrowid

    con.commit()
    con.close()

    return partner, chat_id


def start_chat(message):
    tg_id = message.from_user.id

    if not check_user(message):
        return

    active = get_active_chat(tg_id)

    if active:
        bot.send_message(
            tg_id,
            "⚠️ شما همین الان داخل یک چت هستید.",
            reply_markup=chat_keyboard()
        )
        return

    partner = find_partner(tg_id)

    if partner:
        partner_id, chat_id = partner

        bot.send_message(
            tg_id,
            "✅ یک نفر پیدا شد!\n\n💬 حالا می‌توانید ناشناس صحبت کنید.",
            reply_markup=chat_keyboard()
        )

        bot.send_message(
            partner_id,
            "✅ یک نفر پیدا شد!\n\n💬 حالا می‌توانید ناشناس صحبت کنید.",
            reply_markup=chat_keyboard()
        )

    else:
        con = db()
        cur = con.cursor()

        cur.execute(
            "INSERT OR IGNORE INTO waiting(tg_id,created_at) VALUES(?,?)",
            (tg_id, int(time.time()))
        )

        con.commit()
        con.close()

        bot.send_message(
            tg_id,
            "🔎 در حال پیدا کردن یک نفر...\n\nلطفاً منتظر بمانید.",
            reply_markup=chat_keyboard()
        )


def end_chat(tg_id, notify=True):
    chat = get_active_chat(tg_id)

    if not chat:
        remove_waiting(tg_id)
        return False

    partner = other_user(chat, tg_id)

    con = db()
    cur = con.cursor()

    cur.execute(
        "UPDATE chats SET active=0 WHERE id=?",
        (chat[0],)
    )

    con.commit()
    con.close()

    if notify:
        try:
            bot.send_message(
                partner,
                "🛑 طرف مقابل چت را پایان داد.",
                reply_markup=main_keyboard()
            )
        except:
            pass

    bot.send_message(
        tg_id,
        "🛑 چت پایان یافت.",
        reply_markup=main_keyboard()
    )

    return True


# =========================
# /start
# =========================

@bot.message_handler(commands=["start"])
def start(message):
    if not get_user(message.from_user.id):
        register_user(message)

    if is_banned(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "🚫 حساب شما مسدود است."
        )
        return

    user = get_user(message.from_user.id)

    bot.send_message(
        message.chat.id,
        f"""
🌟 <b>به چت ناشناس خوش آمدی!</b>

سلام {user[2]} 👋

🆔 آیدی عمومی: <code>{user[1]:04d}</code>
🪙 سکه: {user[4]}
⭐ XP: {user[5]}
🏆 رتبه: {user[6]}

از منوی پایین استفاده کن.
""",
        reply_markup=main_keyboard()
    )


# =========================
# /
# =========================

@bot.message_handler(func=lambda m: m.text == "/")
def slash_menu(message):
    if not check_user(message):
        return

    bot.send_message(
        message.chat.id,
        """
📋 <b>دستورات ربات</b>

/start
/chat
/next
/end
/profile
/id
/coins
/shop
/daily
/missions
/games
/guess
/rps
/rank
/leaderboard
/report
/block
/reveal
/name
/help
/admin
""",
        reply_markup=main_keyboard()
    )


# =========================
# دستورات اصلی
# =========================

@bot.message_handler(commands=["chat"])
def cmd_chat(message):
    start_chat(message)


@bot.message_handler(commands=["next"])
def cmd_next(message):
    if not check_user(message):
        return

    tg_id = message.from_user.id

    end_chat(tg_id)

    time.sleep(0.3)

    start_chat(message)


@bot.message_handler(commands=["end"])
def cmd_end(message):
    if not check_user(message):
        return

    end_chat(message.from_user.id)


@bot.message_handler(commands=["profile"])
def cmd_profile(message):
    show_profile(message)


@bot.message_handler(commands=["id"])
def cmd_id(message):
    if not check_user(message):
        return

    user = get_user(message.from_user.id)

    bot.send_message(
        message.chat.id,
        f"🆔 آیدی عمومی شما:\n\n<code>{user[1]:04d}</code>"
    )


@bot.message_handler(commands=["coins"])
def cmd_coins(message):
    show_coins(message)


# =========================
# پروفایل
# =========================

def show_profile(message):
    if not check_user(message):
        return

    user = get_user(message.from_user.id)

    username = f"@{user[3]}" if user[3] else "ندارد"

    bot.send_message(
        message.chat.id,
        f"""
👤 <b>پروفایل</b>

نام: {user[2]}
🆔 آیدی عمومی: <code>{user[1]:04d}</code>
👤 یوزرنیم: {username}

🪙 سکه: {user[4]}
⭐ XP: {user[5]}
🏆 رتبه: {user[6]}
""",
        reply_markup=main_keyboard()
    )


def show_coins(message):
    if not check_user(message):
        return

    user = get_user(message.from_user.id)

    bot.send_message(
        message.chat.id,
        f"""
🪙 <b>سکه‌های شما</b>

موجودی: <b>{user[4]}</b> سکه

با سکه می‌توانی از فروشگاه امکانات مختلف بخری.
""",
        reply_markup=main_keyboard()
    )


# =========================
# فروشگاه
# =========================

@bot.message_handler(commands=["shop"])
def shop(message):
    show_shop(message)


def show_shop(message):
    if not check_user(message):
        return

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "👁 خرید خروج از ناشناس - 3000 🪙",
            callback_data="buy_reveal"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "⭐ خرید 500 XP - 1000 🪙",
            callback_data="buy_xp"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "💰 1000 سکه - 2000 🪙",
            callback_data="buy_coins"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "🗑 حذف کامل حساب - ۳۰٬۰۰۰ تومان",
            callback_data="delete_account"
        )
    )

    bot.send_message(
        message.chat.id,
        "🛒 <b>فروشگاه</b>\n\nیکی از موارد زیر را انتخاب کن:",
        reply_markup=kb
    )


@bot.callback_query_handler(func=lambda c: c.data == "buy_reveal")
def buy_reveal(call):
    tg_id = call.from_user.id

    if is_banned(tg_id):
        bot.answer_callback_query(
            call.id,
            "حساب شما مسدود است.",
            show_alert=True
        )
        return

    if not remove_coins(tg_id, 3000):
        bot.answer_callback_query(
            call.id,
            "❌ سکه کافی نداری.",
            show_alert=True
        )
        return

    con = db()
    cur = con.cursor()

    cur.execute("""
    INSERT INTO inventory(tg_id,item,amount)
    VALUES(?,?,1)
    ON CONFLICT(tg_id,item)
    DO UPDATE SET amount=amount+1
    """, (tg_id, "reveal"))

    con.commit()
    con.close()

    bot.answer_callback_query(
        call.id,
        "✅ خروج از ناشناس خریداری شد."
    )


@bot.callback_query_handler(func=lambda c: c.data == "buy_xp")
def buy_xp(call):
    tg_id = call.from_user.id

    if not remove_coins(tg_id, 1000):
        bot.answer_callback_query(
            call.id,
            "❌ سکه کافی نداری.",
            show_alert=True
        )
        return

    add_xp(tg_id, 500)

    bot.answer_callback_query(
        call.id,
        "✅ 500 XP دریافت کردی!"
    )


@bot.callback_query_handler(func=lambda c: c.data == "buy_coins")
def buy_coins(call):
    tg_id = call.from_user.id

    if not remove_coins(tg_id, 2000):
        bot.answer_callback_query(
            call.id,
            "❌ سکه کافی نداری.",
            show_alert=True
        )
        return

    add_coins(tg_id, 1000)

    bot.answer_callback_query(
        call.id,
        "✅ 1000 سکه دریافت کردی!"
    )


# =========================
# پرداخت واقعی حذف حساب
# =========================

@bot.callback_query_handler(func=lambda c: c.data == "delete_account")
def delete_account_payment(call):
    tg_id = call.from_user.id

    if is_banned(tg_id):
        bot.answer_callback_query(
            call.id,
            "حساب شما مسدود است.",
            show_alert=True
        )
        return

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "💳 پرداخت ۳۰٬۰۰۰ تومان",
            callback_data="pay_delete"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "❌ لغو",
            callback_data="cancel_delete"
        )
    )

    bot.edit_message_text(
        "⚠️ <b>هشدار</b>\n\n"
        "بعد از پرداخت، حساب شما به طور کامل حذف می‌شود "
        "و می‌توانید دوباره از ابتدا ثبت‌نام کنید.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb
    )


@bot.callback_query_handler(func=lambda c: c.data == "cancel_delete")
def cancel_delete(call):
    bot.answer_callback_query(call.id, "لغو شد.")

    bot.edit_message_text(
        "❌ حذف حساب لغو شد.",
        call.message.chat.id,
        call.message.message_id
    )


@bot.callback_query_handler(func=lambda c: c.data == "pay_delete")
def pay_delete(call):
    tg_id = call.from_user.id

    if not PAYMENT_PROVIDER_TOKEN or \
       PAYMENT_PROVIDER_TOKEN == "توکن_درگاه_تلگرام_اینجا_بگذار":

        bot.answer_callback_query(
            call.id,
            "⚠️ توکن درگاه هنوز داخل کد قرار نگرفته.",
            show_alert=True
        )
        return

    payload = f"delete_account:{tg_id}"

    prices = [
        types.LabeledPrice(
            "حذف کامل حساب",
            DELETE_PRICE_RIAL
        )
    ]

    bot.send_invoice(
        call.message.chat.id,
        "حذف کامل حساب",
        "حذف دائمی اطلاعات حساب و امکان ثبت‌نام مجدد",
        payload,
        PAYMENT_PROVIDER_TOKEN,
        "IRR",
        prices,
        start_parameter="delete-account",
        need_name=False,
        need_phone_number=False,
        need_email=False
    )

    bot.answer_callback_query(call.id)


@bot.pre_checkout_query_handler(
    func=lambda query: query.invoice_payload.startswith("delete_account:")
)
def process_pre_checkout(query):
    try:
        tg_id = int(
            query.invoice_payload.split(":")[1]
        )

        if query.from_user.id != tg_id:
            bot.answer_pre_checkout_query(
                query.id,
                ok=False,
                error_message="خطای پرداخت."
            )
            return

        bot.answer_pre_checkout_query(
            query.id,
            ok=True
        )

    except:
        bot.answer_pre_checkout_query(
            query.id,
            ok=False,
            error_message="خطا در پرداخت."
        )


@bot.message_handler(content_types=["successful_payment"])
def successful_payment(message):
    payment = message.successful_payment

    if not payment.invoice_payload.startswith("delete_account:"):
        return

    tg_id = message.from_user.id

    try:
        paid_user = int(
            payment.invoice_payload.split(":")[1]
        )
    except:
        return

    if paid_user != tg_id:
        return

    delete_user(tg_id)

    bot.send_message(
        message.chat.id,
        """
✅ <b>پرداخت موفق بود.</b>

🗑 حساب شما به طور کامل حذف شد.

اکنون می‌توانید دوباره /start را بزنید و
یک حساب جدید از ابتدا بسازید.
""",
        reply_markup=types.ReplyKeyboardRemove()
    )


# =========================
# حذف کامل حساب
# =========================

def delete_user(tg_id):
    con = db()
    cur = con.cursor()

    cur.execute(
        "DELETE FROM waiting WHERE tg_id=?",
        (tg_id,)
    )

    cur.execute(
        "DELETE FROM inventory WHERE tg_id=?",
        (tg_id,)
    )

    cur.execute(
        "DELETE FROM missions WHERE tg_id=?",
        (tg_id,)
    )

    cur.execute(
        "DELETE FROM messages WHERE sender=? OR receiver=?",
        (tg_id, tg_id)
    )

    cur.execute(
        "DELETE FROM reports WHERE reporter=? OR reported=?",
        (tg_id, tg_id)
    )

    cur.execute(
        "DELETE FROM chats WHERE user1=? OR user2=?",
        (tg_id, tg_id)
    )

    cur.execute(
        "DELETE FROM users WHERE tg_id=?",
        (tg_id,)
    )

    con.commit()
    con.close()


# =========================
# جایزه روزانه
# =========================

@bot.message_handler(commands=["daily"])
def daily(message):
    if not check_user(message):
        return

    tg_id = message.from_user.id

    # سیستم ساده جایزه
    reward = random.randint(100, 300)

    add_coins(tg_id, reward)

    bot.send_message(
        tg_id,
        f"🎁 جایزه روزانه دریافت شد!\n\n🪙 +{reward} سکه"
    )


# =========================
# مأموریت‌ها
# =========================

@bot.message_handler(commands=["missions"])
def missions(message):
    if not check_user(message):
        return

    user = get_user(message.from_user.id)

    rank = user[6]

    missions_text = f"""
🎯 <b>مأموریت‌های امروز</b>

🏆 رتبه فعلی: {rank}

1️⃣ ارسال 5 پیام
🎁 جایزه: 200 سکه

2️⃣ انجام یک چت
🎁 جایزه: 300 سکه

3️⃣ بازی کردن
🎁 جایزه: 100 XP

برای انجام مأموریت‌ها از بخش مربوطه استفاده کن.
"""

    bot.send_message(
        message.chat.id,
        missions_text
    )


# =========================
# بازی‌ها
# =========================

@bot.message_handler(commands=["games"])
def games(message):
    if not check_user(message):
        return

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "🎲 حدس عدد",
            callback_data="game_guess"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "✊🖐✌️ سنگ کاغذ قیچی",
            callback_data="game_rps"
        )
    )

    bot.send_message(
        message.chat.id,
        "🎮 <b>بازی‌ها</b>",
        reply_markup=kb
    )


@bot.callback_query_handler(func=lambda c: c.data == "game_guess")
def game_guess(call):
    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        "🎲 یک عدد بین 1 تا 5 انتخاب کردم.\n"
        "برای حدس کردن بنویس:\n\n"
        "/guess 3"
    )


@bot.message_handler(commands=["guess"])
def guess(message):
    if not check_user(message):
        return

    parts = message.text.split()

    if len(parts) != 2:
        bot.send_message(
            message.chat.id,
            "مثال:\n/guess 3"
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

    if number < 1 or number > 5:
        bot.send_message(
            message.chat.id,
            "❌ عدد باید بین 1 تا 5 باشد."
        )
        return

    answer = random.randint(1, 5)

    if number == answer:
        add_coins(message.from_user.id, 300)
        add_xp(message.from_user.id, 50)

        bot.send_message(
            message.chat.id,
            f"🎉 درست حدس زدی!\n\n"
            f"عدد: {answer}\n"
            f"🪙 +300 سکه\n"
            f"⭐ +50 XP"
        )
    else:
        bot.send_message(
            message.chat.id,
            f"❌ باختی!\nعدد درست: {answer}"
        )


@bot.callback_query_handler(func=lambda c: c.data == "game_rps")
def game_rps(call):
    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "✊ سنگ",
            callback_data="rps_rock"
        ),
        types.InlineKeyboardButton(
            "🖐 کاغذ",
            callback_data="rps_paper"
        ),
        types.InlineKeyboardButton(
            "✌️ قیچی",
            callback_data="rps_scissors"
        )
    )

    bot.edit_message_text(
        "🎮 انتخاب کن:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb
    )


@bot.callback_query_handler(
    func=lambda c: c.data.startswith("rps_")
)
def rps_game(call):
    choices = ["rock", "paper", "scissors"]

    user_choice = call.data.replace("rps_", "")

    bot_choice = random.choice(choices)

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
        result = "🎉 بردی!\n🪙 +100 سکه"
        add_coins(call.from_user.id, 100)

    else:
        result = "😢 باختی!"

    bot.answer_callback_query(call.id)

    bot.send_message(
        call.message.chat.id,
        f"""
🎮 نتیجه:

تو: {names[user_choice]}
ربات: {names[bot_choice]}

{result}
"""
    )


@bot.message_handler(commands=["rps"])
def rps_command(message):
    game_rps(
        types.SimpleNamespace(
            data="rps_menu",
            from_user=message.from_user,
            message=message
        )
    )


# =========================
# رتبه‌بندی
# =========================

@bot.message_handler(commands=["rank"])
def rank(message):
    if not check_user(message):
        return

    user = get_user(message.from_user.id)

    bot.send_message(
        message.chat.id,
        f"""
🏆 <b>رتبه شما</b>

{user[6]}

⭐ XP: {user[5]}
"""
    )


@bot.message_handler(commands=["leaderboard"])
def leaderboard(message):
    if not check_user(message):
        return

    con = db()
    cur = con.cursor()

    cur.execute("""
    SELECT public_id,name,xp,rank
    FROM users
    ORDER BY xp DESC
    LIMIT 10
    """)

    users = cur.fetchall()

    con.close()

    text = "🏆 <b>برترین کاربران</b>\n\n"

    for i, user in enumerate(users, 1):
        text += (
            f"{i}. {user[1]} "
            f"#{user[0]:04d} — "
            f"{user[2]} XP — {user[3]}\n"
        )

    bot.send_message(
        message.chat.id,
        text
    )


# =========================
# تغییر نام
# =========================

@bot.message_handler(commands=["name"])
def name_command(message):
    if not check_user(message):
        return

    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        bot.send_message(
            message.chat.id,
            "مثال:\n/name شاهین"
        )
        return

    new_name = parts[1].strip()

    if len(new_name) > 30:
        bot.send_message(
            message.chat.id,
            "❌ نام خیلی طولانی است."
        )
        return

    update_name(
        message.from_user.id,
        new_name
    )

    bot.send_message(
        message.chat.id,
        f"✅ نام شما به <b>{new_name}</b> تغییر کرد."
    )


# =========================
# خروج از ناشناس
# =========================

@bot.message_handler(commands=["reveal"])
def reveal(message):
    if not check_user(message):
        return

    tg_id = message.from_user.id
    chat = get_active_chat(tg_id)

    if not chat:
        bot.send_message(
            tg_id,
            "❌ داخل چت نیستی."
        )
        return

    con = db()
    cur = con.cursor()

    cur.execute("""
    SELECT amount FROM inventory
    WHERE tg_id=? AND item='reveal'
    """, (tg_id,))

    item = cur.fetchone()

    if not item or item[0] <= 0:
        con.close()

        bot.send_message(
            tg_id,
            "❌ برای خروج از ناشناس باید از فروشگاه گزینه خروج از ناشناس را بخری."
        )
        return

    cur.execute("""
    UPDATE inventory
    SET amount=amount-1
    WHERE tg_id=? AND item='reveal'
    """, (tg_id,))

    con.commit()
    con.close()

    partner = other_user(chat, tg_id)

    user = get_user(tg_id)

    username = (
        f"@{user[3]}"
        if user[3]
        else "ندارد"
    )

    info = f"""
👁 <b>طرف مقابل از حالت ناشناس خارج شد.</b>

👤 نام: {user[2]}
🆔 آیدی عمومی: {user[1]:04d}
👤 یوزرنیم: {username}
🏆 رتبه: {user[6]}
⭐ XP: {user[5]}
"""

    bot.send_message(
        partner,
        info
    )

    bot.send_message(
        tg_id,
        "✅ اطلاعات پروفایل برای طرف مقابل ارسال شد."
    )


# =========================
# گزارش
# =========================

@bot.message_handler(commands=["report"])
def report(message):
    if not check_user(message):
        return

    chat = get_active_chat(message.from_user.id)

    if not chat:
        bot.send_message(
            message.chat.id,
            "❌ داخل چت نیستی."
        )
        return

    partner = other_user(
        chat,
        message.from_user.id
    )

    reason = "گزارش توسط کاربر"

    con = db()
    cur = con.cursor()

    cur.execute("""
    INSERT INTO reports
    (reporter,reported,reason,created_at)
    VALUES(?,?,?,?)
    """, (
        message.from_user.id,
        partner,
        reason,
        int(time.time())
    ))

    con.commit()
    con.close()

    bot.send_message(
        message.chat.id,
        "🚨 گزارش ثبت شد."
    )


# =========================
# بلاک
# =========================

@bot.message_handler(commands=["block"])
def block(message):
    if not check_user(message):
        return

    chat = get_active_chat(message.from_user.id)

    if not chat:
        bot.send_message(
            message.chat.id,
            "❌ داخل چت نیستی."
        )
        return

    partner = other_user(
        chat,
        message.from_user.id
    )

    # اینجا گزارش بلاک ثبت می‌شود
    con = db()
    cur = con.cursor()

    cur.execute("""
    INSERT INTO reports
    (reporter,reported,reason,created_at)
    VALUES(?,?,?,?,?)
    """.replace("(?,?,?,?,?)", "(?,?,?,?)"), (
        message.from_user.id,
        partner,
        "بلاک",
        int(time.time())
    ))

    con.commit()
    con.close()

    end_chat(message.from_user.id)

    bot.send_message(
        message.chat.id,
        "🚫 کاربر بلاک شد و چت پایان یافت."
    )


# =========================
# راهنما
# =========================

@bot.message_handler(commands=["help"])
def help_command(message):
    if not check_user(message):
        return

    bot.send_message(
        message.chat.id,
        """
❓ <b>راهنمای ربات</b>

💬 چت ناشناس:
برای پیدا کردن یک نفر روی «چت ناشناس» بزن.

⏭ نفر بعدی:
چت فعلی را تمام می‌کند و نفر دیگری پیدا می‌کند.

🛑 پایان چت:
چت را تمام می‌کند.

🪙 سکه:
برای خرید امکانات فروشگاه استفاده می‌شود.

🎮 بازی:
با بازی کردن می‌توانی سکه و XP بگیری.

👁 خروج از ناشناس:
اطلاعات پروفایلت را برای طرف مقابل نمایش می‌دهد.
"""
    )


# =========================
# ادمین
# =========================

def is_admin(tg_id):
    return tg_id == ADMIN_ID


@bot.message_handler(commands=["admin"])
def admin(message):
    if not is_admin(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "⛔ دسترسی ندارید."
        )
        return

    bot.send_message(
        message.chat.id,
        "🛠 <b>پنل مدیریت</b>",
        reply_markup=admin_keyboard()
    )


@bot.message_handler(commands=["stats"])
def stats(message):
    if not is_admin(message.from_user.id):
        return

    con = db()
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM users WHERE banned=1"
    )
    banned = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM chats WHERE active=1"
    )
    chats = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM reports WHERE solved=0"
    )
    reports = cur.fetchone()[0]

    con.close()

    bot.send_message(
        message.chat.id,
        f"""
📊 <b>آمار ربات</b>

👥 کاربران: {users}
🚫 بن‌شده: {banned}
💬 چت فعال: {chats}
🚨 گزارش‌های باز: {reports}
"""
    )


@bot.message_handler(commands=["ban"])
def ban(message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()

    if len(parts) < 2:
        bot.send_message(
            message.chat.id,
            "مثال:\n/ban 1234"
        )
        return

    try:
        public_id = int(parts[1])
    except:
        return

    con = db()
    cur = con.cursor()

    cur.execute(
        "UPDATE users SET banned=1 WHERE public_id=?",
        (public_id,)
    )

    changed = cur.rowcount

    con.commit()
    con.close()

    if changed:
        bot.send_message(
            message.chat.id,
            "🚫 کاربر بن شد."
        )
    else:
        bot.send_message(
            message.chat.id,
            "❌ کاربر پیدا نشد."
        )


@bot.message_handler(commands=["unban"])
def unban(message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()

    if len(parts) < 2:
        return

    try:
        public_id = int(parts[1])
    except:
        return

    con = db()
    cur = con.cursor()

    cur.execute(
        "UPDATE users SET banned=0 WHERE public_id=?",
        (public_id,)
    )

    changed = cur.rowcount

    con.commit()
    con.close()

    bot.send_message(
        message.chat.id,
        "✅ کاربر آزاد شد."
        if changed
        else "❌ کاربر پیدا نشد."
    )


@bot.message_handler(commands=["addcoins"])
def admin_addcoins(message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()

    if len(parts) != 3:
        bot.send_message(
            message.chat.id,
            "مثال:\n/addcoins 0001 5000"
        )
        return

    try:
        public_id = int(parts[1])
        amount = int(parts[2])
    except:
        return

    con = db()
    cur = con.cursor()

    cur.execute(
        "UPDATE users SET coins=coins+? WHERE public_id=?",
        (amount, public_id)
    )

    changed = cur.rowcount

    con.commit()
    con.close()

    bot.send_message(
        message.chat.id,
        "✅ سکه اضافه شد."
        if changed
        else "❌ کاربر پیدا نشد."
    )


# =========================
# دکمه‌های اصلی
# =========================

@bot.message_handler(
    func=lambda m: m.text == "👤 پروفایل"
)
def button_profile(message):
    show_profile(message)


@bot.message_handler(
    func=lambda m: m.text == "💬 چت ناشناس"
)
def button_chat(message):
    start_chat(message)


@bot.message_handler(
    func=lambda m: m.text == "🪙 سکه‌ها"
)
def button_coins(message):
    show_coins(message)


@bot.message_handler(
    func=lambda m: m.text == "🛒 فروشگاه"
)
def button_shop(message):
    show_shop(message)


@bot.message_handler(
    func=lambda m: m.text == "🎁 جایزه روزانه"
)
def button_daily(message):
    daily(message)


@bot.message_handler(
    func=lambda m: m.text == "🎯 مأموریت‌ها"
)
def button_missions(message):
    missions(message)


@bot.message_handler(
    func=lambda m: m.text == "🎮 بازی‌ها"
)
def button_games(message):
    games(message)


@bot.message_handler(
    func=lambda m: m.text == "🏆 رتبه‌بندی"
)
def button_rank(message):
    leaderboard(message)


@bot.message_handler(
    func=lambda m: m.text == "🆔 آیدی من"
)
def button_id(message):
    cmd_id(message)


@bot.message_handler(
    func=lambda m: m.text == "✏️ تغییر نام"
)
def button_name(message):
    bot.send_message(
        message.chat.id,
        "✏️ برای تغییر نام بنویس:\n\n/name نام جدید"
    )


@bot.message_handler(
    func=lambda m: m.text == "🗑 حذف حساب"
)
def button_delete(message):
    if not check_user(message):
        return

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "🗑 ادامه حذف حساب",
            callback_data="delete_account"
        )
    )

    bot.send_message(
        message.chat.id,
        "⚠️ حذف حساب دائمی است.",
        reply_markup=kb
    )


@bot.message_handler(
    func=lambda m: m.text == "❓ راهنما"
)
def button_help(message):
    help_command(message)


@bot.message_handler(
    func=lambda m: m.text == "⚙️ تنظیمات"
)
def button_settings(message):
    bot.send_message(
        message.chat.id,
        """
⚙️ <b>تنظیمات</b>

✏️ تغییر نام:
 /name نام جدید

🗑 حذف حساب:
از دکمه «حذف حساب» استفاده کن.
"""
    )


# =========================
# دکمه‌های داخل چت
# =========================

@bot.message_handler(
    func=lambda m: m.text == "⏭ نفر بعدی"
)
def button_next(message):
    cmd_next(message)


@bot.message_handler(
    func=lambda m: m.text == "🛑 پایان چت"
)
def button_end(message):
    cmd_end(message)


@bot.message_handler(
    func=lambda m: m.text == "👁 خروج از ناشناس"
)
def button_reveal(message):
    reveal(message)


@bot.message_handler(
    func=lambda m: m.text == "🚨 گزارش"
)
def button_report(message):
    report(message)


@bot.message_handler(
    func=lambda m: m.text == "🚫 بلاک"
)
def button_block(message):
    block(message)


# =========================
# دکمه‌های ادمین
# =========================

@bot.message_handler(
    func=lambda m: m.text == "📊 آمار"
)
def admin_stats_button(message):
    if is_admin(message.from_user.id):
        stats(message)


@bot.message_handler(
    func=lambda m: m.text == "🏠 منوی اصلی"
)
def admin_home(message):
    if is_admin(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "🏠 منوی اصلی",
            reply_markup=main_keyboard()
        )


# =========================
# پیام‌های عادی
# =========================

IGNORED_BUTTONS = set(
    MAIN_BUTTONS +
    CHAT_BUTTONS +
    [
        "📊 آمار",
        "🚨 گزارش‌ها",
        "👤 اطلاعات کاربر",
        "🚫 بن کاربر",
        "✅ آن‌بن کاربر",
        "🪙 افزودن سکه",
        "⭐ افزودن XP",
        "📜 لاگ چت",
        "📢 پیام همگانی",
        "🏠 منوی اصلی"
    ]
)


@bot.message_handler(
    content_types=["text"]
)
def normal_message(message):
    text = message.text

    # مهم:
    # هیچ دکمه یا دستور به طرف مقابل فرستاده نمی‌شود
    if text in IGNORED_BUTTONS:
        return

    if text.startswith("/"):
        return

    if not check_user(message):
        return

    tg_id = message.from_user.id

    chat = get_active_chat(tg_id)

    if not chat:
        bot.send_message(
            tg_id,
            "💬 برای شروع چت، روی «چت ناشناس» بزن.",
            reply_markup=main_keyboard()
        )
        return

    partner = other_user(chat, tg_id)

    con = db()
    cur = con.cursor()

    cur.execute("""
    INSERT INTO messages
    (chat_id,sender,receiver,text,created_at)
    VALUES(?,?,?,?,?)
    """, (
        chat[0],
        tg_id,
        partner,
        text,
        int(time.time())
    ))

    con.commit()
    con.close()

    add_xp(tg_id, 2)

    try:
        bot.send_message(
            partner,
            text,
            reply_markup=chat_keyboard()
        )
    except:
        end_chat(tg_id)


# =========================
# شروع ربات
# =========================

print("BOT STARTED")

bot.infinity_polling(
    skip_pending=True,
    timeout=60,
    long_polling_timeout=60
)
