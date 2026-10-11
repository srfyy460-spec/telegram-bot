import telebot
import sqlite3
import random
from telebot import types

# =========================================================
# تنظیمات
# =========================================================

TOKEN = "8978005144:AAGforuwqrN_oF880nVOT5VyWnSMiqxrPVM"

# کد ورود به پنل مدیریت
ADMIN_CODE = "56945378"

bot = telebot.TeleBot(TOKEN)

DB = "bot.db"

# وضعیت کاربران در چت
waiting_users = set()
active_chats = {}

# =========================================================
# دیتابیس
# =========================================================

def connect():
    return sqlite3.connect(DB)


def create_database():

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        balance INTEGER DEFAULT 0,
        rank TEXT DEFAULT 'Member'
    )
    """)

    conn.commit()
    conn.close()


create_database()


# =========================================================
# اطلاعات کاربر
# =========================================================

def get_user(telegram_id):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT telegram_id, name, username, balance, rank
    FROM users
    WHERE telegram_id=?
    """, (telegram_id,))

    user = cur.fetchone()

    conn.close()

    return user


def get_user_by_username(username):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT telegram_id, name, username, balance, rank
    FROM users
    WHERE username=?
    """, (username,))

    user = cur.fetchone()

    conn.close()

    return user


# =========================================================
# ساخت یوزر چهاررقمی
# =========================================================

def generate_username():

    while True:

        username = str(random.randint(1000, 9999))

        conn = connect()
        cur = conn.cursor()

        cur.execute(
            "SELECT username FROM users WHERE username=?",
            (username,)
        )

        exists = cur.fetchone()

        conn.close()

        if not exists:
            return username


# =========================================================
# منوی ثبت نام
# =========================================================

def register_keyboard():

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.add(
        types.KeyboardButton("📝 ثبت نام")
    )

    return keyboard


# =========================================================
# منوی اصلی
# =========================================================

def main_keyboard():

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.row(
        "💬 چت",
        "👤 پروفایل"
    )

    keyboard.row(
        "🛒 فروشگاه",
        "🎁 کد جایزه"
    )

    return keyboard


# =========================================================
# منوی چت
# =========================================================

def chat_keyboard():

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.row(
        "🔎 پیدا کردن چت"
    )

    keyboard.row(
        "❌ پایان چت",
        "⏭️ نفر بعدی"
    )

    keyboard.row(
        "🏠 منوی اصلی"
    )

    return keyboard


# =========================================================
# پنل مدیریت
# =========================================================

def admin_keyboard():

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.row(
        "👥 کاربران",
        "🔎 جستجوی کاربر"
    )

    keyboard.row(
        "💰 افزایش موجودی",
        "💸 کسر موجودی"
    )

    keyboard.row(
        "🎁 هدیه رنک",
        "📊 آمار"
    )

    keyboard.row(
        "🏠 منوی اصلی"
    )

    return keyboard


# =========================================================
# START
# =========================================================

@bot.message_handler(commands=["start"])
def start(message):

    user = get_user(message.from_user.id)

    if user:

        bot.send_message(
            message.chat.id,
            "👋 خوش برگشتی!",
            reply_markup=main_keyboard()
        )

        return

    bot.send_message(
        message.chat.id,
        "👋 سلام!\n\n"
        "برای استفاده از ربات ابتدا ثبت نام کنید.",
        reply_markup=register_keyboard()
    )


# =========================================================
# ثبت نام
# =========================================================

@bot.message_handler(
    func=lambda message: message.text == "📝 ثبت نام"
)
def register(message):

    user = get_user(message.from_user.id)

    if user:

        bot.send_message(
            message.chat.id,
            "شما قبلاً ثبت نام کرده‌اید.",
            reply_markup=main_keyboard()
        )

        return

    msg = bot.send_message(
        message.chat.id,
        "✏️ لطفاً اسم خود را وارد کنید:"
    )

    bot.register_next_step_handler(
        msg,
        save_name
    )


def save_name(message):

    name = message.text.strip()

    if not name:

        msg = bot.send_message(
            message.chat.id,
            "❌ اسم نمی‌تواند خالی باشد.\n"
            "دوباره اسم خود را وارد کنید:"
        )

        bot.register_next_step_handler(
            msg,
            save_name
        )

        return

    username = generate_username()

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO users
    (telegram_id, name, username, balance, rank)
    VALUES (?, ?, ?, ?, ?)
    """, (
        message.from_user.id,
        name,
        username,
        0,
        "Member"
    ))

    conn.commit()
    conn.close()

    bot.send_message(
        message.chat.id,
        f"✅ ثبت نام کامل شد!\n\n"
        f"👤 نام: {name}\n"
        f"🆔 یوزر: {username}\n"
        f"⭐ رنک: Member\n"
        f"💰 موجودی: 0 تومان\n\n"
        f"حالا می‌تونی وارد چت بشی.",
        reply_markup=main_keyboard()
    )


# =========================================================
# پروفایل
# =========================================================

@bot.message_handler(
    func=lambda message: message.text == "👤 پروفایل"
)
def profile(message):

    user = get_user(message.from_user.id)

    if not user:

        bot.send_message(
            message.chat.id,
            "❌ ابتدا ثبت نام کنید."
        )

        return

    telegram_id, name, username, balance, rank = user

    bot.send_message(
        message.chat.id,
        f"👤 پروفایل شما\n\n"
        f"نام: {name}\n"
        f"🆔 یوزر: {username}\n"
        f"⭐ رنک: {rank}\n"
        f"💰 موجودی: {balance:,} تومان"
    )


# =========================================================
# منوی چت
# =========================================================

@bot.message_handler(
    func=lambda message: message.text == "💬 چت"
)
def chat_menu(message):

    user = get_user(message.from_user.id)

    if not user:

        bot.send_message(
            message.chat.id,
            "❌ ابتدا ثبت نام کنید."
        )

        return

    bot.send_message(
        message.chat.id,
        "💬 بخش چت\n\n"
        "با زدن «پیدا کردن چت» یک کاربر تصادفی "
        "برای گفت‌وگو پیدا می‌شود.\n\n"
        "🔒 هویت واقعی کاربران برای یکدیگر نمایش داده نمی‌شود.",
        reply_markup=chat_keyboard()
    )


# =========================================================
# پیدا کردن چت
# =========================================================

@bot.message_handler(
    func=lambda message: message.text == "🔎 پیدا کردن چت"
)
def find_chat(message):

    user = get_user(message.from_user.id)

    if not user:
        return

    # اگر خودش در چت است
    if message.from_user.id in active_chats:

        bot.send_message(
            message.chat.id,
            "❌ شما در حال حاضر با یک نفر در چت هستید."
        )

        return

    # اگر در صف است
    if message.from_user.id in waiting_users:

        bot.send_message(
            message.chat.id,
            "⏳ شما در صف پیدا کردن چت هستید..."
        )

        return

    # پیدا کردن شخص منتظر
    partner = None

    for waiting_id in list(waiting_users):

        if waiting_id != message.from_user.id:
            partner = waiting_id
            break

    if partner is None:

        waiting_users.add(message.from_user.id)

        bot.send_message(
            message.chat.id,
            "⏳ در صف قرار گرفتی.\n\n"
            "به محض پیدا شدن یک نفر، چت شروع می‌شود."
        )

        return

    # حذف از صف
    waiting_users.discard(partner)

    # ساخت چت
    active_chats[message.from_user.id] = partner
    active_chats[partner] = message.from_user.id

    user1 = get_user(message.from_user.id)
    user2 = get_user(partner)

    name1 = user1[1]
    rank1 = user1[4]

    name2 = user2[1]
    rank2 = user2[4]

    bot.send_message(
        message.chat.id,
        f"🎉 یک نفر پیدا شد!\n\n"
        f"{name2} {rank2} گفت: 👋 سلام!\n\n"
        f"💬 حالا پیام خودت را بفرست.",
        reply_markup=chat_keyboard()
    )

    bot.send_message(
        partner,
        f"🎉 یک نفر پیدا شد!\n\n"
        f"{name1} {rank1} گفت: 👋 سلام!\n\n"
        f"💬 حالا پیام خودت را بفرست.",
        reply_markup=chat_keyboard()
    )


# =========================================================
# پایان چت
# =========================================================

@bot.message_handler(
    func=lambda message: message.text == "❌ پایان چت"
)
def end_chat(message):

    partner = active_chats.get(
        message.from_user.id
    )

    if not partner:

        bot.send_message(
            message.chat.id,
            "❌ شما در حال حاضر در چت نیستید."
        )

        return

    active_chats.pop(
        message.from_user.id,
        None
    )

    active_chats.pop(
        partner,
        None
    )

    bot.send_message(
        message.chat.id,
        "❌ چت پایان یافت.",
        reply_markup=chat_keyboard()
    )

    bot.send_message(
        partner,
        "❌ طرف مقابل چت را پایان داد.",
        reply_markup=chat_keyboard()
    )


# =========================================================
# نفر بعدی
# =========================================================

@bot.message_handler(
    func=lambda message: message.text == "⏭️ نفر بعدی"
)
def next_chat(message):

    partner = active_chats.get(
        message.from_user.id
    )

    if partner:

        active_chats.pop(
            message.from_user.id,
            None
        )

        active_chats.pop(
            partner,
            None
        )

        bot.send_message(
            partner,
            "⏭️ طرف مقابل چت را ترک کرد."
        )

    find_chat(message)


# =========================================================
# پیام‌های چت
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.from_user.id in active_chats
        and message.text not in [
            "❌ پایان چت",
            "⏭️ نفر بعدی",
            "💬 چت",
            "👤 پروفایل",
            "🛒 فروشگاه",
            "🎁 کد جایزه"
        ]
)
def relay_chat(message):

    partner = active_chats.get(
        message.from_user.id
    )

    if not partner:
        return

    sender = get_user(
        message.from_user.id
    )

    name = sender[1]
    rank = sender[4]

    text = message.text

    bot.send_message(
        partner,
        f"{name} {rank} گفت:\n"
        f"{text}"
    )


# =========================================================
# فروشگاه
# =========================================================

def shop_keyboard():

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "🥈 رنک نقره‌ای — 50,000 تومان",
            callback_data="rank_silver"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🥇 رنک طلایی — 160,000 تومان",
            callback_data="rank_gold"
        )
    )

    return keyboard


@bot.message_handler(
    func=lambda message: message.text == "🛒 فروشگاه"
)
def shop(message):

    user = get_user(message.from_user.id)

    if not user:
        return

    bot.send_message(
        message.chat.id,
        "🛒 فروشگاه رنک\n\n"
        "🥈 نقره‌ای: 50,000 تومان\n"
        "🥇 طلایی: 160,000 تومان\n\n"
        "رنک خود را انتخاب کنید:",
        reply_markup=shop_keyboard()
    )


# =========================================================
# خرید رنک
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data in [
            "rank_silver",
            "rank_gold"
        ]
)
def buy_rank(call):

    user = get_user(
        call.from_user.id
    )

    if not user:
        return

    if call.data == "rank_silver":

        rank = "Silver"
        price = 50000
        emoji = "🥈"

    else:

        rank = "Gold"
        price = 160000
        emoji = "🥇"

    balance = user[3]

    if balance < price:

        bot.answer_callback_query(
            call.id,
            "❌ موجودی کافی نیست!",
            show_alert=True
        )

        return

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "✅ تأیید خرید",
            callback_data=f"confirm_rank_{rank}"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "❌ لغو",
            callback_data="cancel_rank"
        )
    )

    bot.edit_message_text(
        f"{emoji} خرید رنک {rank}\n\n"
        f"💰 قیمت: {price:,} تومان\n"
        f"💳 موجودی شما: {balance:,} تومان\n\n"
        f"آیا خرید را تأیید می‌کنید؟",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard
    )


# =========================================================
# تأیید رنک
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data.startswith("confirm_rank_")
)
def confirm_rank(call):

    rank = call.data.replace(
        "confirm_rank_",
        ""
    )

    if rank == "Silver":

        price = 50000
        emoji = "🥈"

    elif rank == "Gold":

        price = 160000
        emoji = "🥇"

    else:
        return

    user = get_user(
        call.from_user.id
    )

    if not user:
        return

    balance = user[3]

    if balance < price:

        bot.answer_callback_query(
            call.id,
            "❌ موجودی کافی نیست!",
            show_alert=True
        )

        return

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET balance = balance - ?,
        rank = ?
    WHERE telegram_id=?
    """, (
        price,
        rank,
        call.from_user.id
    ))

    conn.commit()
    conn.close()

    new_balance = balance - price

    bot.edit_message_text(
        f"🎉 خرید موفق بود!\n\n"
        f"{emoji} رنک: {rank}\n"
        f"💰 مبلغ: {price:,} تومان\n"
        f"💳 موجودی جدید: {new_balance:,} تومان",
        call.message.chat.id,
        call.message.message_id
    )


# =========================================================
# لغو خرید
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data == "cancel_rank"
)
def cancel_rank(call):

    bot.edit_message_text(
        "❌ خرید لغو شد.",
        call.message.chat.id,
        call.message.message_id
    )


# =========================================================
# کد جایزه
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "🎁 کد جایزه"
)
def reward(message):

    msg = bot.send_message(
        message.chat.id,
        "🎁 کد جایزه را وارد کنید:"
    )

    bot.register_next_step_handler(
        msg,
        check_reward
    )


def check_reward(message):

    code = message.text.strip()

    user = get_user(
        message.from_user.id
    )

    if not user:
        return

    # جایزه
    if code == "100":

        conn = connect()
        cur = conn.cursor()

        cur.execute("""
        UPDATE users
        SET balance = balance + 10000
        WHERE telegram_id=?
        """, (
            message.from_user.id,
        ))

        conn.commit()
        conn.close()

        bot.send_message(
            message.chat.id,
            "🎉 کد درست بود!\n\n"
            "💰 10,000 تومان به کیف پول شما اضافه شد."
        )

    # مدیریت
    elif code == ADMIN_CODE:

        bot.send_message(
            message.chat.id,
            "🔐 پنل مدیریت فعال شد.",
            reply_markup=admin_keyboard()
        )

    else:

        bot.send_message(
            message.chat.id,
            "❌ کد اشتباه است."
        )


# =========================================================
# مدیریت - کاربران
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "👥 کاربران"
)
def admin_users(message):

    users = get_user(message.from_user.id)

    if not users:
        return

    if message.from_user.id not in [
        u[0] for u in get_admins()
    ]:
        return

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    SELECT name, username, rank, balance
    FROM users
    ORDER BY username
    """)

    rows = cur.fetchall()

    conn.close()

    if not rows:

        bot.send_message(
            message.chat.id,
            "هیچ کاربری وجود ندارد."
        )

        return

    text = "👥 کاربران:\n\n"

    for name, username, rank, balance in rows:

        text += (
            f"👤 {name}\n"
            f"🆔 {username}\n"
            f"⭐ {rank}\n"
            f"💰 {balance:,} تومان\n"
            f"────────────\n"
        )

    bot.send_message(
        message.chat.id,
        text
    )


# =========================================================
# مدیریت
# =========================================================

def get_admins():

    # مدیرهایی که کد مدیریت را فعال کرده‌اند
    # برای نسخه موقت در حافظه نگهداری می‌شوند.

    return [
        (x,) for x in admin_sessions
    ]


admin_sessions = set()


# =========================================================
# فعال شدن مدیریت
# =========================================================

old_check_reward = check_reward


def check_reward(message):

    code = message.text.strip()

    user = get_user(
        message.from_user.id
    )

    if not user:
        return

    if code == "100":

        conn = connect()
        cur = conn.cursor()

        cur.execute("""
        UPDATE users
        SET balance = balance + 10000
        WHERE telegram_id=?
        """, (
            message.from_user.id,
        ))

        conn.commit()
        conn.close()

        bot.send_message(
            message.chat.id,
            "🎉 کد صحیح بود!\n"
            "💰 10,000 تومان اضافه شد."
        )

    elif code == ADMIN_CODE:

        admin_sessions.add(
            message.from_user.id
        )

        bot.send_message(
            message.chat.id,
            "🔐 پنل مدیریت فعال شد.",
            reply_markup=admin_keyboard()
        )

    else:

        bot.send_message(
            message.chat.id,
            "❌ کد اشتباه است."
        )


# =========================================================
# جستجوی کاربر
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "🔎 جستجوی کاربر"
)
def search_user_start(message):

    if message.from_user.id not in admin_sessions:
        return

    msg = bot.send_message(
        message.chat.id,
        "🆔 یوزر چهاررقمی را وارد کنید:"
    )

    bot.register_next_step_handler(
        msg,
        search_user
    )


def search_user(message):

    user = get_user_by_username(
        message.text.strip()
    )

    if not user:

        bot.send_message(
            message.chat.id,
            "❌ کاربر پیدا نشد."
        )

        return

    telegram_id, name, username, balance, rank = user

    bot.send_message(
        message.chat.id,
        f"👤 اطلاعات کاربر\n\n"
        f"نام: {name}\n"
        f"🆔 یوزر: {username}\n"
        f"⭐ رنک: {rank}\n"
        f"💰 موجودی: {balance:,} تومان"
    )


# =========================================================
# افزایش موجودی
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "💰 افزایش موجودی"
)
def increase_start(message):

    if message.from_user.id not in admin_sessions:
        return

    msg = bot.send_message(
        message.chat.id,
        "🆔 یوزر کاربر را وارد کنید:"
    )

    bot.register_next_step_handler(
        msg,
        increase_user
    )


def increase_user(message):

    username = message.text.strip()

    user = get_user_by_username(username)

    if not user:

        bot.send_message(
            message.chat.id,
            "❌ کاربر پیدا نشد."
        )

        return

    msg = bot.send_message(
        message.chat.id,
        f"👤 {user[1]}\n\n"
        "💰 مقدار پولی که می‌خواهید اضافه کنید:"
    )

    bot.register_next_step_handler(
        msg,
        lambda m: do_increase(
            m,
            user[0]
        )
    )


def do_increase(message, telegram_id):

    try:
        amount = int(message.text)

        if amount <= 0:
            raise ValueError

    except:

        bot.send_message(
            message.chat.id,
            "❌ مبلغ نامعتبر است."
        )

        return

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET balance = balance + ?
    WHERE telegram_id=?
    """, (
        amount,
        telegram_id
    ))

    conn.commit()
    conn.close()

    bot.send_message(
        message.chat.id,
        "✅ موجودی افزایش پیدا کرد."
    )

    try:

        bot.send_message(
            telegram_id,
            f"💰 {amount:,} تومان به حساب شما اضافه شد."
        )

    except:
        pass


# =========================================================
# کسر موجودی
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "💸 کسر موجودی"
)
def decrease_start(message):

    if message.from_user.id not in admin_sessions:
        return

    msg = bot.send_message(
        message.chat.id,
        "🆔 یوزر کاربر را وارد کنید:"
    )

    bot.register_next_step_handler(
        msg,
        decrease_user
    )


def decrease_user(message):

    username = message.text.strip()

    user = get_user_by_username(username)

    if not user:

        bot.send_message(
            message.chat.id,
            "❌ کاربر پیدا نشد."
        )

        return

    msg = bot.send_message(
        message.chat.id,
        f"👤 {user[1]}\n"
        f"💰 موجودی فعلی: {user[3]:,} تومان\n\n"
        "مقدار کسر را وارد کنید:"
    )

    bot.register_next_step_handler(
        msg,
        lambda m: do_decrease(
            m,
            user[0],
            user[3]
        )
    )


def do_decrease(message, telegram_id, balance):

    try:

        amount = int(message.text)

        if amount <= 0:
            raise ValueError

    except:

        bot.send_message(
            message.chat.id,
            "❌ مبلغ نامعتبر است."
        )

        return

    if amount > balance:

        bot.send_message(
            message.chat.id,
            "❌ موجودی کاربر کمتر از این مقدار است."
        )

        return

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET balance = balance - ?
    WHERE telegram_id=?
    """, (
        amount,
        telegram_id
    ))

    conn.commit()
    conn.close()

    bot.send_message(
        message.chat.id,
        "✅ مبلغ از حساب کاربر کسر شد."
    )

    try:

        bot.send_message(
            telegram_id,
            f"💸 {amount:,} تومان از موجودی شما کسر شد."
        )

    except:
        pass


# =========================================================
# هدیه رنک
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "🎁 هدیه رنک"
)
def gift_rank_start(message):

    if message.from_user.id not in admin_sessions:
        return

    msg = bot.send_message(
        message.chat.id,
        "🆔 یوزر کاربر را وارد کنید:"
    )

    bot.register_next_step_handler(
        msg,
        gift_rank_user
    )


def gift_rank_user(message):

    username = message.text.strip()

    user = get_user_by_username(username)

    if not user:

        bot.send_message(
            message.chat.id,
            "❌ کاربر پیدا نشد."
        )

        return

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "🥈 نقره‌ای",
            callback_data=f"gift_Silver_{user[0]}"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🥇 طلایی",
            callback_data=f"gift_Gold_{user[0]}"
        )
    )

    bot.send_message(
        message.chat.id,
        f"👤 کاربر: {user[1]}\n\n"
        "رنک هدیه را انتخاب کنید:",
        reply_markup=keyboard
    )


@bot.callback_query_handler(
    func=lambda call:
        call.data.startswith("gift_")
)
def gift_rank(call):

    parts = call.data.split("_")

    rank = parts[1]
    telegram_id = int(parts[2])

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET rank=?
    WHERE telegram_id=?
    """, (
        rank,
        telegram_id
    ))

    conn.commit()
    conn.close()

    bot.answer_callback_query(
        call.id,
        "رنک با موفقیت هدیه داده شد!"
    )

    bot.send_message(
        call.message.chat.id,
        f"🎁 رنک {rank} به کاربر هدیه داده شد."
    )

    try:

        bot.send_message(
            telegram_id,
            f"🎉 مدیریت به شما رنک {rank} هدیه داد!"
        )

    except:
        pass


# =========================================================
# آمار
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "📊 آمار"
)
def statistics(message):

    if message.from_user.id not in admin_sessions:
        return

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM users"
    )

    users_count = cur.fetchone()[0]

    cur.execute(
        "SELECT COALESCE(SUM(balance), 0) FROM users"
    )

    total_balance = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM users WHERE rank='Gold'"
    )

    gold = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM users WHERE rank='Silver'"
    )

    silver = cur.fetchone()[0]

    conn.close()

    bot.send_message(
        message.chat.id,
        f"📊 آمار ربات\n\n"
        f"👥 کاربران: {users_count}\n"
        f"🥇 طلایی: {gold}\n"
        f"🥈 نقره‌ای: {silver}\n"
        f"💰 مجموع موجودی کاربران: "
        f"{total_balance:,} تومان"
    )


# =========================================================
# منوی اصلی
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "🏠 منوی اصلی"
)
def home(message):

    bot.send_message(
        message.chat.id,
        "🏠 منوی اصلی",
        reply_markup=main_keyboard()
    )


# =========================================================
# اجرای ربات
# =========================================================

print("BOT IS RUNNING...")

bot.infinity_polling(
    skip_pending=True,
    timeout=60,
    long_polling_timeout=60
)
