import telebot
from telebot import types
import sqlite3
import random

# =========================
# تنظیمات
# =========================

TOKEN = "8802163316:AAHJhO6ZXnVD4VzgZONCjE76YD3Zn1Pg8tM"

# آیدی عددی تلگرام خودت را اینجا بگذار
ADMIN_ID = 7723971526

# کانال اجباری
CHANNEL = "@shahab20139"
CHANNEL_LINK = "https://t.me/shahab20139"

bot = telebot.TeleBot(TOKEN)


# =========================
# دیتابیس
# =========================

db = sqlite3.connect("users.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    name TEXT,
    username4 TEXT UNIQUE,
    balance INTEGER DEFAULT 0
)
""")

db.commit()


# =========================
# توابع دیتابیس
# =========================

def get_user(user_id):
    cursor.execute(
        "SELECT * FROM users WHERE telegram_id = ?",
        (user_id,)
    )
    return cursor.fetchone()


def create_user(user_id, name):
    while True:
        username4 = str(random.randint(1000, 9999))

        cursor.execute(
            "SELECT username4 FROM users WHERE username4 = ?",
            (username4,)
        )

        if cursor.fetchone() is None:
            break

    cursor.execute(
        """
        INSERT INTO users
        (telegram_id, name, username4, balance)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, name, username4, 0)
    )

    db.commit()

    return username4


def change_balance(user_id, amount):
    cursor.execute(
        """
        UPDATE users
        SET balance = balance + ?
        WHERE telegram_id = ?
        """,
        (amount, user_id)
    )

    db.commit()


# =========================
# بررسی عضویت کانال
# =========================

def is_member(user_id):

    try:
        member = bot.get_chat_member(CHANNEL, user_id)

        return member.status in [
            "member",
            "administrator",
            "creator"
        ]

    except Exception:
        return False


# =========================
# منوی عضویت
# =========================

def join_menu(message):

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "📢 عضویت در کانال",
            url=CHANNEL_LINK
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "✅ بررسی عضویت",
            callback_data="check_join"
        )
    )

    bot.send_message(
        message.chat.id,
        "سلام عزیز ❤️\n\n"
        "برای استفاده از ربات ابتدا باید عضو کانال ما بشی.\n\n"
        "بعد از عضویت روی «✅ بررسی عضویت» بزن.",
        reply_markup=keyboard
    )


# =========================
# منوی ثبت نام
# =========================

def register_menu(message):

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.add(
        types.KeyboardButton("📝 ثبت نام")
    )

    bot.send_message(
        message.chat.id,
        "برای شروع ابتدا ثبت نام کن 👇",
        reply_markup=keyboard
    )


# =========================
# منوی اصلی
# =========================

def main_menu(message):

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=2
    )

    keyboard.add(
        types.KeyboardButton("👤 پروفایل"),
        types.KeyboardButton("🛒 فروشگاه")
    )

    keyboard.add(
        types.KeyboardButton("🎁 کد جایزه"),
        types.KeyboardButton("📞 پشتیبانی")
    )

    if message.from_user.id == ADMIN_ID:
        keyboard.add(
            types.KeyboardButton("👑 پنل مدیریت")
        )

    bot.send_message(
        message.chat.id,
        "🎉 خوش اومدی!\n\n"
        "از منوی زیر انتخاب کن:",
        reply_markup=keyboard
    )


# =========================
# START
# =========================

@bot.message_handler(commands=["start"])
def start(message):

    if not is_member(message.from_user.id):
        join_menu(message)
        return

    user = get_user(message.from_user.id)

    if user is None:
        register_menu(message)
    else:
        main_menu(message)


# =========================
# بررسی عضویت
# =========================

@bot.callback_query_handler(
    func=lambda call: call.data == "check_join"
)
def check_join(call):

    if is_member(call.from_user.id):

        bot.answer_callback_query(
            call.id,
            "✅ عضویت تأیید شد!"
        )

        user = get_user(call.from_user.id)

        if user is None:
            register_menu(call.message)
        else:
            main_menu(call.message)

    else:

        bot.answer_callback_query(
            call.id,
            "❌ هنوز عضو کانال نیستی!",
            show_alert=True
        )


# =========================
# ثبت نام
# =========================

@bot.message_handler(
    func=lambda message: message.text == "📝 ثبت نام"
)
def register(message):

    if not is_member(message.from_user.id):
        join_menu(message)
        return

    if get_user(message.from_user.id):
        main_menu(message)
        return

    msg = bot.send_message(
        message.chat.id,
        "👤 لطفاً نام خودت را وارد کن:"
    )

    bot.register_next_step_handler(
        msg,
        save_name
    )


def save_name(message):

    name = message.text.strip()

    if len(name) < 2:
        msg = bot.send_message(
            message.chat.id,
            "❌ نام خیلی کوتاه است.\nدوباره نامت را وارد کن:"
        )

        bot.register_next_step_handler(
            msg,
            save_name
        )

        return

    username4 = create_user(
        message.from_user.id,
        name
    )

    bot.send_message(
        message.chat.id,
        "🎉 ثبت نام با موفقیت انجام شد!\n\n"
        f"👤 نام: {name}\n"
        f"🆔 یوزر: {username4}\n"
        "💰 موجودی: 0 تومان"
    )

    main_menu(message)


# =========================
# پروفایل
# =========================

@bot.message_handler(
    func=lambda message: message.text == "👤 پروفایل"
)
def profile(message):

    user = get_user(message.from_user.id)

    if user is None:
        register_menu(message)
        return

    bot.send_message(
        message.chat.id,
        "👤 پروفایل شما\n\n"
        f"نام: {user[1]}\n"
        f"🆔 یوزر: {user[2]}\n"
        f"💰 موجودی: {user[3]:,} تومان"
    )


# =========================
# کد جایزه
# =========================

@bot.message_handler(
    func=lambda message: message.text == "🎁 کد جایزه"
)
def reward_menu(message):

    msg = bot.send_message(
        message.chat.id,
        "🎁 کد جایزه را وارد کن:"
    )

    bot.register_next_step_handler(
        msg,
        check_reward
    )


def check_reward(message):

    code = message.text.strip()

    user = get_user(message.from_user.id)

    if user is None:
        register_menu(message)
        return

    # کد 100
    if code == "100":

        change_balance(
            message.from_user.id,
            10000
        )

        bot.send_message(
            message.chat.id,
            "🎉 تبریک!\n\n"
            "💰 10,000 تومان به کیف پولت اضافه شد."
        )

    # کد اشتباه
    else:

        bot.send_message(
            message.chat.id,
            "❌ کد وارد شده معتبر نیست."
        )


# =========================
# فروشگاه
# =========================

@bot.message_handler(
    func=lambda message: message.text == "🛒 فروشگاه"
)
def shop(message):

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "🔥 10 CP — 10 تومان",
            callback_data="buy_10"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🔥 50 CP — 50 تومان",
            callback_data="buy_50"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🔥 100 CP — 100 تومان",
            callback_data="buy_100"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🔥 500 CP — 500 تومان",
            callback_data="buy_500"
        )
    )

    bot.send_message(
        message.chat.id,
        "🛒 فروشگاه\n\n"
        "محصول مورد نظر را انتخاب کن:",
        reply_markup=keyboard
    )


# =========================
# خرید
# =========================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("buy_")
)
def buy(call):

    cp = int(call.data.split("_")[1])
    price = cp

    user = get_user(call.from_user.id)

    if user is None:
        bot.answer_callback_query(
            call.id,
            "ابتدا ثبت نام کن!",
            show_alert=True
        )
        return

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
            callback_data=f"confirm_{cp}_{price}"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "❌ انصراف",
            callback_data="cancel_buy"
        )
    )

    bot.send_message(
        call.message.chat.id,
        f"🔥 محصول: {cp} CP\n"
        f"💰 قیمت: {price} تومان\n\n"
        "آیا خرید را تأیید می‌کنی؟",
        reply_markup=keyboard
    )


# =========================
# تأیید خرید
# =========================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("confirm_")
)
def confirm_buy(call):

    parts = call.data.split("_")

    cp = int(parts[1])
    price = int(parts[2])

    user = get_user(call.from_user.id)

    if user is None:
        return

    if user[3] < price:

        bot.answer_callback_query(
            call.id,
            "❌ موجودی کافی نیست!",
            show_alert=True
        )

        return

    change_balance(
        call.from_user.id,
        -price
    )

    bot.answer_callback_query(
        call.id,
        "✅ خرید با موفقیت انجام شد!"
    )

    bot.send_message(
        call.message.chat.id,
        f"🎉 خرید موفق!\n\n"
        f"🔥 {cp} CP خریداری شد.\n"
        f"💸 {price} تومان از کیف پول کم شد."
    )


# =========================
# انصراف
# =========================

@bot.callback_query_handler(
    func=lambda call: call.data == "cancel_buy"
)
def cancel_buy(call):

    bot.answer_callback_query(
        call.id,
        "خرید لغو شد."
    )

    bot.send_message(
        call.message.chat.id,
        "❌ خرید لغو شد."
    )


# =========================
# پنل مدیریت
# =========================

@bot.message_handler(
    func=lambda message: message.text == "👑 پنل مدیریت"
)
def admin_panel(message):

    if message.from_user.id != ADMIN_ID:

        bot.send_message(
            message.chat.id,
            "❌ دسترسی ندارید."
        )

        return

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=2
    )

    keyboard.add(
        types.KeyboardButton("👥 کاربران"),
        types.KeyboardButton("💰 افزایش موجودی")
    )

    keyboard.add(
        types.KeyboardButton("📊 آمار"),
        types.KeyboardButton("🔙 بازگشت")
    )

    bot.send_message(
        message.chat.id,
        "👑 پنل مدیریت",
        reply_markup=keyboard
    )


# =========================
# لیست کاربران
# =========================

@bot.message_handler(
    func=lambda message: message.text == "👥 کاربران"
)
def users_list(message):

    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute(
        "SELECT name, username4, balance FROM users"
    )

    users = cursor.fetchall()

    if not users:

        bot.send_message(
            message.chat.id,
            "هیچ کاربری ثبت نام نکرده."
        )

        return

    text = "👥 لیست کاربران:\n\n"

    for user in users:

        text += (
            f"👤 {user[0]}\n"
            f"🆔 {user[1]}\n"
            f"💰 {user[2]:,} تومان\n"
            "────────────\n"
        )

    bot.send_message(
        message.chat.id,
        text
    )


# =========================
# افزایش موجودی
# =========================

@bot.message_handler(
    func=lambda message: message.text == "💰 افزایش موجودی"
)
def add_balance_start(message):

    if message.from_user.id != ADMIN_ID:
        return

    msg = bot.send_message(
        message.chat.id,
        "🆔 یوزر ۴ رقمی کاربر را وارد کن:"
    )

    bot.register_next_step_handler(
        msg,
        admin_get_user
    )


def admin_get_user(message):

    username4 = message.text.strip()

    cursor.execute(
        "SELECT telegram_id, name FROM users WHERE username4 = ?",
        (username4,)
    )

    user = cursor.fetchone()

    if user is None:

        bot.send_message(
            message.chat.id,
            "❌ کاربر پیدا نشد."
        )

        return

    msg = bot.send_message(
        message.chat.id,
        f"👤 کاربر: {user[1]}\n\n"
        "💰 مقدار پولی که می‌خواهی اضافه شود را وارد کن:"
    )

    bot.register_next_step_handler(
        msg,
        lambda m: admin_add_money(m, user[0])
    )


def admin_add_money(message, user_id):

    try:
        amount = int(message.text)

        if amount <= 0:
            raise ValueError

    except ValueError:

        bot.send_message(
            message.chat.id,
            "❌ مقدار نامعتبر است."
        )

        return

    change_balance(
        user_id,
        amount
    )

    bot.send_message(
        message.chat.id,
        f"✅ {amount:,} تومان به حساب کاربر اضافه شد."
    )


# =========================
# آمار
# =========================

@bot.message_handler(
    func=lambda message: message.text == "📊 آمار"
)
def stats(message):

    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    count = cursor.fetchone()[0]

    bot.send_message(
        message.chat.id,
        f"📊 آمار ربات\n\n"
        f"👥 تعداد کاربران: {count}"
    )


# =========================
# بازگشت
# =========================

@bot.message_handler(
    func=lambda message: message.text == "🔙 بازگشت"
)
def back(message):

    if message.from_user.id == ADMIN_ID:
        main_menu(message)


# =========================
# پشتیبانی
# =========================

@bot.message_handler(
    func=lambda message: message.text == "📞 پشتیبانی"
)
def support(message):

    bot.send_message(
        message.chat.id,
        "📞 پشتیبانی\n\n"
        "برای ارتباط با پشتیبانی پیام خودت را ارسال کن."
    )


# =========================
# اجرای ربات
# =========================

print("Bot is running...")

bot.infinity_polling()
