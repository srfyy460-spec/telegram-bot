import os
import random
from datetime import datetime, timedelta

import telebot
from telebot import types

# =========================
# تنظیمات
# =========================

TOKEN = os.getenv("BOT_TOKEN", "TOKEN_HERE")
ADMIN_ID = 7723971526

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# =========================
# دیتای موقت
# =========================

users = {}
waiting_users = []
active_chats = {}

reports = []
reviews = []
suggestions = []
admin_actions = []

giveaways = []
challenges = []

states = {}
games = {}

# =========================
# رنک‌ها
# =========================

RANKS = {
    "bronze": {
        "title": "🥉 برنز",
        "priority": 1,
        "price": 0
    },

    "silver": {
        "title": "🥈 نقره‌ای",
        "priority": 2,
        "price": 50000
    },

    "gold": {
        "title": "🥇 طلایی",
        "priority": 3,
        "price": 150000
    },

    "diamond": {
        "title": "💎 الماسی",
        "priority": 4,
        "price": 500000
    },

    "vip": {
        "title": "👑 VIP",
        "priority": 5,
        "price": 1500000
    },

    "moderator": {
        "title": "Moderator",
        "priority": 100,
        "price": 0,
        "special": True
    }
}

# =========================
# ابزارها
# =========================

def now():
    return datetime.now()


def is_admin(user_id):
    return user_id == ADMIN_ID


def ensure_user(tg_user):

    user_id = tg_user.id

    if user_id not in users:

        users[user_id] = {

            "id": user_id,

            "username": tg_user.username or "",

            "first_name": tg_user.first_name or "",

            "last_name": tg_user.last_name or "",

            "phone": "",

            "code": f"{len(users) + 1:04d}",

            "coins": 100,

            # فقط اعتبار مجازی
            "balance": 0,

            "xp": 0,

            "level": 1,

            "ranks": [
                {
                    "name": "bronze",
                    "expires": now() + timedelta(days=30)
                }
            ],

            "messages": 0,

            "chats": 0,

            "referrals": 0,

            "warnings": 0,

            "banned_until": None,

            "created_at": now(),

            "last_activity": now(),

            "anonymous": True,

            "photo_file_id": None
        }

    else:

        users[user_id]["username"] = (
            tg_user.username or users[user_id]["username"]
        )

        users[user_id]["first_name"] = (
            tg_user.first_name or users[user_id]["first_name"]
        )

        users[user_id]["last_name"] = (
            tg_user.last_name or users[user_id]["last_name"]
        )

        users[user_id]["last_activity"] = now()

    return users[user_id]


def active_ranks(user_id):

    user = users[user_id]

    valid = []

    for rank in user["ranks"]:

        if rank["expires"] > now():
            valid.append(rank)

    user["ranks"] = valid

    return valid


def visible_rank(user_id):

    ranks = active_ranks(user_id)

    if not ranks:
        return "bronze"

    return max(
        ranks,
        key=lambda x: RANKS[x["name"]]["priority"]
    )["name"]


def rank_title(user_id):

    return RANKS[
        visible_rank(user_id)
    ]["title"]


def display_name(user_id):

    user = users.get(user_id, {})

    return (
        user.get("first_name")
        or user.get("username")
        or str(user_id)
    )


def level_up(user):

    needed = user["level"] * 100

    while user["xp"] >= needed:

        user["xp"] -= needed

        user["level"] += 1

        needed = user["level"] * 100


def add_xp(user_id, amount):

    user = users[user_id]

    old_level = user["level"]

    user["xp"] += amount

    level_up(user)

    if user["level"] > old_level:

        notify_user(
            user_id,
            f"🎉 تبریک!\n"
            f"به سطح <b>{user['level']}</b> رسیدی."
        )


def banned(user_id):

    user = users.get(user_id)

    if not user:
        return False

    until = user.get("banned_until")

    if until is None:
        return False

    # بن دائمی
    if until is False:
        return True

    if until <= now():

        user["banned_until"] = None

        return False

    return True


def notify_user(user_id, text):

    try:

        bot.send_message(
            user_id,
            text
        )

    except Exception:

        pass


def admin_log(
    action,
    target_id=None,
    old=None,
    new=None,
    note=""
):

    admin_actions.append({

        "admin": ADMIN_ID,

        "target": target_id,

        "action": action,

        "old": old,

        "new": new,

        "note": note,

        "time": now()
    })


# =========================
# منوی اصلی
# =========================

def main_menu(user_id):

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    keyboard.row(
        "💬 چت",
        "👤 پروفایل"
    )

    keyboard.row(
        "🪙 سکه",
        "⭐ رنک‌ها"
    )

    keyboard.row(
        "🎮 بازی",
        "🎯 مأموریت‌ها"
    )

    keyboard.row(
        "🎁 قرعه‌کشی",
        "🏆 چالش‌ها"
    )

    keyboard.row(
        "📊 آمار",
        "💡 پیشنهاد/نظر"
    )

    keyboard.row(
        "🚫 پایان چت",
        "❓ راهنما"
    )

    if is_admin(user_id):

        keyboard.row(
            "🛠 پنل مدیریت"
        )

    return keyboard


# =========================
# پنل مدیریت
# =========================

def admin_menu():

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    buttons = [

        "📊 داشبورد",
        "👥 کاربران",

        "🔎 جستجوی کاربر",
        "🚨 گزارش‌ها",

        "🛡️ ناظران",
        "⚠️ هشدارها",

        "🪙 مدیریت سکه",
        "💰 مدیریت اعتبار",

        "⭐ مدیریت XP",
        "🏆 مدیریت رنک",

        "🎁 قرعه‌کشی",
        "🎯 چالش‌ها",

        "📢 پیام همگانی",
        "📣 اعلان‌ها",

        "💬 نظرات",
        "💡 پیشنهادات",

        "📈 آمار",
        "📋 لاگ مدیریت",

        "💬 چت‌های فعال",
        "🔍 جستجوی پیام",

        "🚫 مسدود/رفع",
        "⏱️ بن زمان‌دار",

        "🎟️ جوایز",
        "🎮 مدیریت بازی‌ها",

        "🎯 مدیریت مأموریت‌ها",
        "🏅 تنظیم رنک‌ها",

        "🧹 پاکسازی",
        "⚙️ تنظیمات بات",

        "🔐 امنیت",
        "📤 خروجی آمار",

        "⬅️ بازگشت"
    ]

    for i in range(0, len(buttons), 2):

        keyboard.row(
            *buttons[i:i + 2]
        )

    return keyboard


# =========================
# START
# =========================

@bot.message_handler(commands=["start"])
def start(message):

    user = ensure_user(
        message.from_user
    )

    if banned(message.from_user.id):

        bot.reply_to(
            message,
            "🚫 حساب شما مسدود یا محدود است."
        )

        return

    bot.send_message(

        message.chat.id,

        f"سلام <b>{user['first_name'] or 'دوست من'}</b> 👋\n\n"

        f"به <b>چت ناشناس</b> خوش اومدی! 🤍\n\n"

        f"🔢 کد حساب: "
        f"<code>{user['code']}</code>\n"

        f"🪙 سکه: "
        f"{user['coins']}\n"

        f"🏆 رنک: "
        f"{rank_title(user['id'])}",

        reply_markup=main_menu(
            user["id"]
        )
    )


# =========================
# پروفایل
# =========================

@bot.message_handler(
    func=lambda m: m.text == "👤 پروفایل"
)
def profile(message):

    user = ensure_user(
        message.from_user
    )

    ranks = active_ranks(
        user["id"]
    )

    rank_list = []

    for rank in ranks:

        rank_list.append(
            f"• {RANKS[rank['name']]['title']} "
            f"تا {rank['expires'].strftime('%Y-%m-%d')}"
        )

    if not rank_list:

        rank_list.append(
            "• بدون رنک"
        )

    text = (

        "👤 <b>پروفایل شما</b>\n\n"

        f"نام: "
        f"{user['first_name']} "
        f"{user['last_name']}\n"

        f"یوزرنیم: "
        f"@{user['username'] or 'ندارد'}\n"

        f"🔢 کد حساب: "
        f"<code>{user['code']}</code>\n"

        f"⭐ سطح: "
        f"{user['level']}\n"

        f"XP: "
        f"{user['xp']}\n"

        f"🪙 سکه: "
        f"{user['coins']}\n"

        f"💰 اعتبار مجازی: "
        f"{user['balance']:,} تومان\n"

        f"💬 پیام‌ها: "
        f"{user['messages']}\n"

        f"👥 چت‌ها: "
        f"{user['chats']}\n"

        f"🎁 دعوت‌ها: "
        f"{user['referrals']}\n"

        f"⚠️ هشدارها: "
        f"{user['warnings']}\n\n"

        "🏆 <b>رنک‌های فعال:</b>\n"

        + "\n".join(rank_list)

        + "\n\n"
        "🔒 اعتبار تومان فقط مجازی است "
        "و قابل برداشت پول واقعی نیست."
    )

    bot.send_message(
        message.chat.id,
        text
    )


# =========================
# سکه
# =========================

@bot.message_handler(
    func=lambda m: m.text == "🪙 سکه"
)
def coins(message):

    user = ensure_user(
        message.from_user
    )

    bot.send_message(

        message.chat.id,

        f"🪙 سکه: "
        f"<b>{user['coins']}</b>\n\n"

        f"💰 اعتبار مجازی: "
        f"<b>{user['balance']:,}</b> تومان\n\n"

        "⚠️ این اعتبار قابل برداشت "
        "و تبدیل به پول واقعی نیست."
    )


# =========================
# رنک‌ها
# =========================

@bot.message_handler(
    func=lambda m: m.text == "⭐ رنک‌ها"
)
def ranks(message):

    ensure_user(
        message.from_user
    )

    text = (
        "🏆 <b>فروشگاه رنک</b>\n\n"
        "تمام رنک‌های خریداری‌شده "
        "۳۰ روز فعال هستند.\n\n"
    )

    keyboard = types.InlineKeyboardMarkup()

    for key, rank in RANKS.items():

        if key == "moderator":
            continue

        text += (
            f"{rank['title']} — "
            f"{rank['price']:,} سکه\n"
        )

        keyboard.add(

            types.InlineKeyboardButton(

                f"خرید {rank['title']}",

                callback_data=f"buy_rank:{key}"
            )
        )

    text += (
        "\n🛡️ Moderator فقط توسط مدیریت "
        "فعال می‌شود."
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=keyboard
    )


@bot.callback_query_handler(
    func=lambda c: c.data.startswith("buy_rank:")
)
def buy_rank(call):

    user = ensure_user(
        call.from_user
    )

    rank_name = call.data.split(
        ":",
        1
    )[1]

    rank = RANKS[rank_name]

    if user["coins"] < rank["price"]:

        bot.answer_callback_query(
            call.id,
            "❌ سکه کافی نیست.",
            show_alert=True
        )

        return

    user["coins"] -= rank["price"]

    user["ranks"].append({

        "name": rank_name,

        "expires":
            now() + timedelta(days=30)
    })

    bot.answer_callback_query(
        call.id,
        "✅ رنک خریداری شد."
    )

    bot.send_message(

        call.from_user.id,

        f"🎉 رنک "
        f"<b>{rank['title']}</b> "
        f"برای ۳۰ روز فعال شد."
    )


# =========================
# چت
# =========================

@bot.message_handler(
    func=lambda m: m.text == "💬 چت"
)
def start_chat(message):

    user = ensure_user(
        message.from_user
    )

    uid = user["id"]

    if banned(uid):

        bot.send_message(
            uid,
            "🚫 شما اجازه چت ندارید."
        )

        return

    if uid in active_chats:

        bot.send_message(
            uid,
            "💬 شما همین الان داخل چت هستید."
        )

        return

    if uid not in waiting_users:

        waiting_users.append(uid)

    if len(waiting_users) >= 2:

        first = waiting_users.pop(0)

        second = waiting_users.pop(0)

        if first == second:
            return

        active_chats[first] = second

        active_chats[second] = first

        users[first]["chats"] += 1

        users[second]["chats"] += 1

        bot.send_message(
            first,
            "✅ یک نفر پیدا شد!\n\n"
            "پیامت رو بفرست 💬\n"
            "برای خروج: 🚫 پایان چت"
        )

        bot.send_message(
            second,
            "✅ یک نفر پیدا شد!\n\n"
            "پیامت رو بفرست 💬\n"
            "برای خروج: 🚫 پایان چت"
        )

    else:

        bot.send_message(
            uid,
            "🔎 در حال پیدا کردن یک نفر..."
        )


# =========================
# پایان چت
# =========================

@bot.message_handler(
    func=lambda m: m.text == "🚫 پایان چت"
)
def end_chat(message):

    uid = ensure_user(
        message.from_user
    )["id"]

    partner = active_chats.pop(
        uid,
        None
    )

    if partner:

        active_chats.pop(
            partner,
            None
        )

        bot.send_message(
            partner,
            "❌ طرف مقابل چت را پایان داد."
        )

        bot.send_message(
            uid,
            "❌ چت پایان یافت."
        )

    else:

        if uid in waiting_users:
            waiting_users.remove(uid)

        bot.send_message(
            uid,
            "چت فعالی ندارید."
        )


# =========================
# انتقال پیام
# =========================

def relay_message(message):

    uid = message.from_user.id

    if uid not in active_chats:
        return False

    partner = active_chats[uid]

    users[uid]["messages"] += 1

    add_xp(
        uid,
        2
    )

    try:

        if message.content_type == "text":

            bot.send_message(
                partner,
                f"🕵️ ناشناس:\n\n"
                f"{message.text}"
            )

        elif message.content_type == "photo":

            bot.send_photo(
                partner,
                message.photo[-1].file_id,
                caption=message.caption or ""
            )

        elif message.content_type == "video":

            bot.send_video(
                partner,
                message.video.file_id,
                caption=message.caption or ""
            )

        elif message.content_type == "voice":

            bot.send_voice(
                partner,
                message.voice.file_id
            )

        elif message.content_type == "document":

            bot.send_document(
                partner,
                message.document.file_id,
                caption=message.caption or ""
            )

        else:

            bot.copy_message(
                partner,
                message.chat.id,
                message.message_id
            )

        return True

    except Exception:

        bot.send_message(
            uid,
            "⚠️ ارسال پیام ناموفق بود."
        )

        return True


# =========================
# بازی
# =========================

@bot.message_handler(
    func=lambda m: m.text == "🎮 بازی"
)
def game(message):

    user = ensure_user(
        message.from_user
    )

    number = random.randint(
        1,
        5
    )

    games[user["id"]] = number

    states[user["id"]] = {
        "type": "guess"
    }

    bot.send_message(

        user["id"],

        "🎮 <b>حدس عدد</b>\n\n"

        "یک عدد بین ۱ تا ۵ بفرست.\n\n"

        "🎁 جایزه برد:\n"
        "🪙 ۲۰ سکه\n"
        "⭐ ۱۰ XP"
    )


# =========================
# مأموریت
# =========================

@bot.message_handler(
    func=lambda m: m.text == "🎯 مأموریت‌ها"
)
def missions(message):

    ensure_user(
        message.from_user
    )

    bot.send_message(

        message.chat.id,

        "🎯 <b>مأموریت‌ها</b>\n\n"

        "1️⃣ ارسال ۱۰ پیام\n"
        "🎁 جایزه: ۵۰ سکه\n\n"

        "2️⃣ انجام ۳ چت\n"
        "🎁 جایزه: ۷۵ سکه\n\n"

        "3️⃣ ورود روزانه\n"
        "🎁 جایزه: ۵۰ سکه"
    )


# =========================
# قرعه‌کشی
# =========================

@bot.message_handler(
    func=lambda m: m.text == "🎁 قرعه‌کشی"
)
def giveaways_list(message):

    ensure_user(
        message.from_user
    )

    if not giveaways:

        bot.send_message(
            message.chat.id,
            "🎁 فعلاً قرعه‌کشی فعالی وجود ندارد."
        )

        return

    for giveaway in giveaways:

        bot.send_message(

            message.chat.id,

            f"🎁 <b>{giveaway['title']}</b>\n\n"

            f"{giveaway['description']}\n\n"

            f"🏆 جایزه: "
            f"{giveaway['prize']}\n"

            f"👥 شرکت‌کنندگان: "
            f"{len(giveaway['entries'])}"
        )


# =========================
# چالش‌ها
# =========================

@bot.message_handler(
    func=lambda m: m.text == "🏆 چالش‌ها"
)
def challenges_list(message):

    ensure_user(
        message.from_user
    )

    if not challenges:

        bot.send_message(
            message.chat.id,
            "🏆 فعلاً چالشی فعال نیست."
        )

        return

    for challenge in challenges:

        bot.send_message(

            message.chat.id,

            f"🏆 <b>{challenge['title']}</b>\n\n"

            f"{challenge['description']}\n\n"

            f"نوع: {challenge['kind']}\n"

            f"جایزه: {challenge['prize']}"
        )


# =========================
# آمار
# =========================

@bot.message_handler(
    func=lambda m: m.text == "📊 آمار"
)
def stats(message):

    user = ensure_user(
        message.from_user
    )

    bot.send_message(

        message.chat.id,

        "📊 <b>آمار شما</b>\n\n"

        f"⭐ سطح: {user['level']}\n"

        f"XP: {user['xp']}\n"

        f"💬 پیام‌ها: {user['messages']}\n"

        f"👥 چت‌ها: {user['chats']}\n"

        f"🎁 دعوت‌ها: {user['referrals']}"
    )


# =========================
# پیشنهاد و نظر
# =========================

@bot.message_handler(
    func=lambda m: m.text == "💡 پیشنهاد/نظر"
)
def feedback(message):

    ensure_user(
        message.from_user
    )

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(

        types.InlineKeyboardButton(
            "💬 ثبت نظر",
            callback_data="feedback:review"
        )
    )

    keyboard.add(

        types.InlineKeyboardButton(
            "💡 ارسال پیشنهاد",
            callback_data="feedback:suggestion"
        )
    )

    bot.send_message(
        message.chat.id,
        "یکی را انتخاب کن:",
        reply_markup=keyboard
    )


@bot.callback_query_handler(
    func=lambda c: c.data.startswith("feedback:")
)
def feedback_type(call):

    kind = call.data.split(
        ":",
        1
    )[1]

    states[call.from_user.id] = {
        "type": kind
    }

    bot.answer_callback_query(
        call.id
    )

    bot.send_message(
        call.from_user.id,
        "✍️ متن خودت را بفرست:"
    )


# =========================
# راهنما
# =========================

@bot.message_handler(
    func=lambda m: m.text == "❓ راهنما"
)
def help_command(message):

    bot.send_message(

        message.chat.id,

        "❓ <b>راهنمای چت ناشناس</b>\n\n"

        "💬 چت — پیدا کردن فرد برای گفتگو\n"
        "👤 پروفایل — اطلاعات حساب\n"
        "🪙 سکه — موجودی\n"
        "⭐ رنک‌ها — خرید رنک\n"
        "🎮 بازی — بازی و دریافت جایزه\n"
        "🎯 مأموریت‌ها — مأموریت‌ها\n"
        "🎁 قرعه‌کشی — قرعه‌کشی‌ها\n"
        "🏆 چالش‌ها — چالش‌ها\n"
        "📊 آمار — آمار حساب\n\n"

        "/daily — جایزه روزانه\n"
        "/report — گزارش تخلف\n"
        "/end — پایان چت"
    )


# =========================
# پنل مدیریت
# =========================

@bot.message_handler(
    func=lambda m: m.text == "🛠 پنل مدیریت"
)
def admin_panel(message):

    if not is_admin(
        message.from_user.id
    ):
        return

    bot.send_message(

        message.chat.id,

        "🛠 <b>پنل مدیریت</b>\n\n"
        "یک گزینه را انتخاب کن:",

        reply_markup=admin_menu()
    )


# =========================
# داشبورد مدیریت
# =========================

@bot.message_handler(
    func=lambda m: m.text == "📊 داشبورد"
)
def admin_dashboard(message):

    if not is_admin(
        message.from_user.id
    ):
        return

    bot.send_message(

        message.chat.id,

        "📊 <b>داشبورد</b>\n\n"

        f"👥 کاربران: {len(users)}\n"

        f"💬 چت‌های فعال: "
        f"{len(active_chats) // 2}\n"

        f"🚨 گزارش‌ها: "
        f"{len(reports)}\n"

        f"💬 نظرات: "
        f"{len(reviews)}\n"

        f"💡 پیشنهادات: "
        f"{len(suggestions)}\n"

        f"🎁 قرعه‌کشی‌ها: "
        f"{len(giveaways)}\n"

        f"🏆 چالش‌ها: "
        f"{len(challenges)}"
    )


# =========================
# کاربران
# =========================

@bot.message_handler(
    func=lambda m: m.text == "👥 کاربران"
)
def admin_users(message):

    if not is_admin(
        message.from_user.id
    ):
        return

    if not users:

        bot.send_message(
            message.chat.id,
            "کاربری وجود ندارد."
        )

        return

    text = "👥 <b>کاربران</b>\n\n"

    for user in list(users.values())[:50]:

        text += (

            f"🔢 {user['code']}\n"

            f"ID: <code>{user['id']}</code>\n"

            f"نام: {display_name(user['id'])}\n"

            f"رنک: {rank_title(user['id'])}\n\n"
        )

    bot.send_message(
        message.chat.id,
        text
    )


# =========================
# جستجوی کاربر
# =========================

@bot.message_handler(
    func=lambda m: m.text == "🔎 جستجوی کاربر"
)
def search_user_start(message):

    if not is_admin(
        message.from_user.id
    ):
        return

    states[
        message.from_user.id
    ] = {
        "type": "admin_search"
    }

    bot.send_message(

        message.chat.id,

        "🔎 کد حساب یا Telegram ID کاربر را بفرست:"
    )


def find_user(value):

    try:

        user_id = int(value)

        if user_id in users:

            return users[user_id]

    except:

        pass

    for user in users.values():

        if user["code"] == value:

            return user

    return None


# =========================
# مدیریت سکه
# =========================

@bot.message_handler(
    func=lambda m: m.text == "🪙 مدیریت سکه"
)
def admin_coins(message):

    if not is_admin(
        message.from_user.id
    ):
        return

    states[
        message.from_user.id
    ] = {
        "type": "admin_coins"
    }

    bot.send_message(

        message.chat.id,

        "فرمت:\n\n"
        "<code>ID مقدار</code>\n\n"
        "مثال:\n"
        "<code>123456789 500</code>"
    )


# =========================
# مدیریت اعتبار
# =========================

@bot.message_handler(
    func=lambda m: m.text == "💰 مدیریت اعتبار"
)
def admin_balance(message):

    if not is_admin(
        message.from_user.id
    ):
        return

    states[
        message.from_user.id
    ] = {
        "type": "admin_balance"
    }

    bot.send_message(

        message.chat.id,

        "فرمت:\n\n"
        "<code>ID مقدار</code>\n\n"
        "مثال:\n"
        "<code>123456789 500000</code>"
    )


# =========================
# مدیریت XP
# =========================

@bot.message_handler(
    func=lambda m: m.text == "⭐ مدیریت XP"
)
def admin_xp(message):

    if not is_admin(
        message.from_user.id
    ):
        return

    states[
        message.from_user.id
    ] = {
        "type": "admin_xp"
    }

    bot.send_message(

        message.chat.id,

        "فرمت:\n\n"
        "<code>ID مقدار_XP</code>"
    )


# =========================
# مدیریت رنک
# =========================

@bot.message_handler(
    func=lambda m: m.text == "🏆 مدیریت رنک"
)
def admin_rank(message):

    if not is_admin(
        message.from_user.id
    ):
        return

    states[
        message.from_user.id
    ] = {
        "type": "admin_rank"
    }

    bot.send_message(

        message.chat.id,

        "فرمت:\n\n"
        "<code>ID rank</code>\n\n"

        "مثال:\n"
        "<code>123456789 vip</code>\n\n"

        "رنک‌ها:\n"
        "bronze\n"
        "silver\n"
        "gold\n"
        "diamond\n"
        "vip\n"
        "moderator"
    )


# =========================
# نظرات مدیریت
# =========================

@bot.message_handler(
    func=lambda m: m.text == "💬 نظرات"
)
def admin_reviews(message):

    if not is_admin(
        message.from_user.id
    ):
        return

    if not reviews:

        bot.send_message(
            message.chat.id,
            "💬 نظری ثبت نشده."
        )

        return

    for review in reviews[-30:]:

        bot.send_message(

            message.chat.id,

            f"👤 کاربر: "
            f"{review['user']}\n\n"

            f"💬 {review['text']}\n\n"

            f"🕒 {review['time']}"
        )


# =========================
# پیشنهادات مدیریت
# =========================

@bot.message_handler(
    func=lambda m: m.text == "💡 پیشنهادات"
)
def admin_suggestions(message):

    if not is_admin(
        message.from_user.id
    ):
        return

    if not suggestions:

        bot.send_message(
            message.chat.id,
            "💡 پیشنهادی ثبت نشده."
        )

        return

    for suggestion in suggestions[-30:]:

        bot.send_message(

            message.chat.id,

            f"👤 کاربر: "
            f"{suggestion['user']}\n\n"

            f"💡 {suggestion['text']}\n\n"

            f"🕒 {suggestion['time']}"
        )


# =========================
# لاگ مدیریت
# =========================

@bot.message_handler(
    func=lambda m: m.text == "📋 لاگ مدیریت"
)
def admin_logs(message):

    if not is_admin(
        message.from_user.id
    ):
        return

    if not admin_actions:

        bot.send_message(
            message.chat.id,
            "📋 هنوز لاگی ثبت نشده."
        )

        return

    text = "📋 <b>آخرین اقدامات مدیریت</b>\n\n"

    for log in admin_actions[-30:]:

        text += (

            f"🕒 {log['time']}\n"

            f"کاربر: {log['target']}\n"

            f"عملیات: {log['action']}\n"

            f"قدیم: {log['old']}\n"

            f"جدید: {log['new']}\n\n"
        )

    bot.send_message(
        message.chat.id,
        text
    )


# =========================
# چت‌های فعال
# =========================

@bot.message_handler(
    func=lambda m: m.text == "💬 چت‌های فعال"
)
def active_chats_admin(message):

    if not is_admin(
        message.from_user.id
    ):
        return

    if not active_chats:

        bot.send_message(
            message.chat.id,
            "💬 هیچ چت فعالی وجود ندارد."
        )

        return

    pairs = set()

    text = "💬 <b>چت‌های فعال</b>\n\n"

    for a, b in active_chats.items():

        pair = tuple(
            sorted([a, b])
        )

        if pair in pairs:
            continue

        pairs.add(pair)

        text += (
            f"<code>{a}</code> ↔ "
            f"<code>{b}</code>\n"
        )

    bot.send_message(
        message.chat.id,
        text
    )


# =========================
# گزارش
# =========================

@bot.message_handler(
    commands=["report"]
)
def report(message):

    ensure_user(
        message.from_user
    )

    states[
        message.from_user.id
    ] = {
        "type": "report_message"
    }

    bot.reply_to(

        message,

        "🚨 اول پیام متخلف را "
        "فوروارد یا ارسال کن."
    )


# =========================
# پردازش پیام‌ها
# =========================

@bot.message_handler(
    content_types=[
        "text",
        "photo",
        "video",
        "voice",
        "document"
    ]
)
def all_messages(message):

    uid = message.from_user.id

    ensure_user(
        message.from_user
    )

    # اگر کاربر در چت است،
    # پیام را برای طرف مقابل بفرست
    if relay_message(message):

        return

    # بازی
    if uid in games:

        try:

            answer = int(
                message.text
            )

        except:

            bot.send_message(
                uid,
                "❌ فقط یک عدد بین ۱ تا ۵ بفرست."
            )

            return

        correct = games.pop(uid)

        if answer == correct:

            users[uid]["coins"] += 20

            add_xp(
                uid,
                10
            )

            bot.send_message(
                uid,
                "🎉 درست حدس زدی!\n\n"
                "🪙 +۲۰ سکه\n"
                "⭐ +۱۰ XP"
            )

        else:

            bot.send_message(
                uid,
                f"❌ اشتباه بود!\n"
                f"عدد درست: {correct}"
            )

        return

    # Stateهای بعدی اینجا پردازش می‌شوند
    state = states.get(uid)

    if state:

        state_type = state["type"]

        # نظر
        if state_type == "review":

            reviews.append({

                "user": uid,

                "text": message.text or "",

                "time": now()
            })

            states.pop(uid)

            bot.send_message(
                uid,
                "✅ نظر شما ثبت شد."
            )

            return

        # پیشنهاد
        if state_type == "suggestion":

            suggestions.append({

                "user": uid,

                "text": message.text or "",

                "time": now()
            })

            states.pop(uid)

            bot.send_message(
                uid,
                "✅ پیشنهاد شما ثبت شد."
            )

            return

        # جستجوی کاربر توسط ادمین
        if (
            state_type == "admin_search"
            and is_admin(uid)
        ):

            user = find_user(
                message.text
            )

            states.pop(uid)

            if not user:

                bot.send_message(
                    uid,
                    "❌ کاربر پیدا نشد."
                )

                return

            ranks = active_ranks(
                user["id"]
            )

            rank_names = ", ".join(

                RANKS[
                    r["name"]
                ]["title"]

                for r in ranks
            )

            bot.send_message(

                uid,

                "👤 <b>اطلاعات کامل کاربر</b>\n\n"

                f"Telegram ID: "
                f"<code>{user['id']}</code>\n"

                f"Username: "
                f"@{user['username'] or 'ندارد'}\n"

                f"نام: "
                f"{user['first_name']} "
                f"{user['last_name']}\n"

                f"شماره تلفن: "
                f"{user['phone'] or 'ثبت نشده'}\n"

                f"کد حساب: "
                f"{user['code']}\n"

                f"رنک‌ها: "
                f"{rank_names or 'ندارد'}\n"

                f"سطح: "
                f"{user['level']}\n"

                f"XP: "
                f"{user['xp']}\n"

                f"سکه: "
                f"{user['coins']}\n"

                f"اعتبار مجازی: "
                f"{user['balance']:,} تومان\n"

                f"چت‌ها: "
                f"{user['chats']}\n"

                f"پیام‌ها: "
                f"{user['messages']}\n"

                f"دعوت‌ها: "
                f"{user['referrals']}\n"

                f"هشدارها: "
                f"{user['warnings']}\n"

                f"بن: "
                f"{'بله' if banned(user['id']) else 'خیر'}\n\n"

                f"عضویت: "
                f"{user['created_at']}\n"

                f"آخرین فعالیت: "
                f"{user['last_activity']}"
            )

            return

        # مدیریت سکه
        if (
            state_type == "admin_coins"
            and is_admin(uid)
        ):

            parts = message.text.split()

            if len(parts) != 2:

                bot.send_message(
                    uid,
                    "❌ فرمت اشتباه."
                )

                return

            user = find_user(
                parts[0]
            )

            try:

                amount = int(
                    parts[1]
                )

            except:

                bot.send_message(
                    uid,
                    "❌ مقدار باید عدد باشد."
                )

                return

            if not user:

                bot.send_message(
                    uid,
                    "❌ کاربر پیدا نشد."
                )

                return

            old = user["coins"]

            user["coins"] += amount

            admin_log(
                "coins",
                user["id"],
                old,
                user["coins"],
                amount
            )

            if amount >= 0:

                notify_user(

                    user["id"],

                    f"🪙 {amount:,} سکه "
                    "از طرف مدیریت به حساب شما اضافه شد."
                )

            else:

                notify_user(

                    user["id"],

                    f"🪙 {abs(amount):,} سکه "
                    "از حساب شما کم شد."
                )

            states.pop(uid)

            bot.send_message(
                uid,
                "✅ انجام شد."
            )

            return

        # مدیریت اعتبار
        if (
            state_type == "admin_balance"
            and is_admin(uid)
        ):

            parts = message.text.split()

            if len(parts) != 2:
                return

            user = find_user(
                parts[0]
            )

            try:

                amount = int(
                    parts[1]
                )

            except:

                return

            if not user:
                return

            old = user["balance"]

            user["balance"] += amount

            admin_log(
                "balance",
                user["id"],
                old,
                user["balance"],
                amount
            )

            if amount >= 0:

                notify_user(

                    user["id"],

                    f"💰 {amount:,} تومان "
                    "اعتبار مجازی به حساب شما اضافه شد."
                )

            else:

                notify_user(

                    user["id"],

                    f"💰 {abs(amount):,} تومان "
                    "اعتبار مجازی از حساب شما کم شد."
                )

            states.pop(uid)

            bot.send_message(
                uid,
                "✅ انجام شد."
            )

            return

        # مدیریت XP
        if (
            state_type == "admin_xp"
            and is_admin(uid)
        ):

            parts = message.text.split()

            if len(parts) != 2:
                return

            user = find_user(
                parts[0]
            )

            try:

                amount = int(
                    parts[1]
                )

            except:

                return

            if not user:
                return

            old = user["xp"]

            user["xp"] += amount

            level_up(user)

            admin_log(
                "xp",
                user["id"],
                old,
                user["xp"],
                amount
            )

            notify_user(

                user["id"],

                f"⭐ {abs(amount):,} XP "
                f"{'اضافه' if amount >= 0 else 'کم'} شد."
            )

            states.pop(uid)

            bot.send_message(
                uid,
                "✅ انجام شد."
            )

            return

        # مدیریت رنک
        if (
            state_type == "admin_rank"
            and is_admin(uid)
        ):

            parts = message.text.split()

            if len(parts) != 2:
                return

            user = find_user(
                parts[0]
            )

            rank_name = parts[1].lower()

            if (
                not user
                or rank_name not in RANKS
            ):

                bot.send_message(
                    uid,
                    "❌ کاربر یا رنک نامعتبر است."
                )

                return

            user["ranks"].append({

                "name": rank_name,

                "expires":
                    now() + timedelta(days=30)
            })

            admin_log(
                "rank",
                user["id"],
                None,
                rank_name
            )

            notify_user(

                user["id"],

                f"🏆 رنک "
                f"<b>{RANKS[rank_name]['title']}</b> "
                "توسط مدیریت برای شما فعال شد.\n"
                "⏳ مدت: ۳۰ روز"
            )

            states.pop(uid)

            bot.send_message(
                uid,
                "✅ رنک اضافه شد."
            )

            return

    # اگر چت فعال نبود
    bot.send_message(

        uid,

        "از منوی پایین یک گزینه را انتخاب کن 👇",
        reply_markup=main_menu(uid)
    )


# =========================
# جایزه روزانه
# =========================

@bot.message_handler(
    commands=["daily"]
)
def daily(message):

    user = ensure_user(
        message.from_user
    )

    last = user.get(
        "last_daily"
    )

    if (
        last
        and
        (now() - last).total_seconds()
        < 86400
    ):

        bot.reply_to(
            message,
            "⏳ جایزه امروز را قبلاً گرفتی."
        )

        return

    user["last_daily"] = now()

    user["coins"] += 50

    add_xp(
        user["id"],
        10
    )

    bot.reply_to(

        message,

        "🎁 جایزه روزانه گرفتی!\n\n"
        "🪙 +۵۰ سکه\n"
        "⭐ +۱۰ XP"
    )


# =========================
# پایان
# =========================

print(
    "🤖 Anonymous Chat Bot Started..."
)

bot.infinity_polling(
    skip_pending=True
)