import telebot
from telebot import types
import random
from datetime import date

# ==================================================
# تنظیمات
# ==================================================

BOT_TOKEN = "8978005144:AAGforuwqrN_oF880nVOT5VyWnSMiqxrPVM"

# آیدی عددی تلگرام ادمین
ADMIN_ID = 7723971526

bot = telebot.TeleBot(BOT_TOKEN)

# ==================================================
# دیتای موقت
# ==================================================

users = {}
waiting_users = []
active_chats = {}
reports = []

# ==================================================
# ساخت کد کاربری
# 0001 تا 100000
# ==================================================

def generate_code():
    used_codes = {u["code"] for u in users.values()}

    for number in range(1, 100001):
        code = f"{number:04d}"

        if code not in used_codes:
            return code

    return None


# ==================================================
# ساخت کاربر
# ==================================================

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
        "coins": 0,
        "balance": 0,
        "streak": 1,
        "last_daily": str(date.today()),
        "messages": 0,
        "chats": 0,
        "referrals": 0,
        "banned": False
    }

    return True


# ==================================================
# XP
# ==================================================

def xp_needed(level):
    return level * 250


def add_xp(user_id, amount):

    if user_id not in users:
        return

    user = users[user_id]

    user["xp"] += amount

    while user["xp"] >= xp_needed(user["level"]):

        user["xp"] -= xp_needed(user["level"])
        user["level"] += 1

        reward = user["level"] * 100
        user["coins"] += reward

        try:
            bot.send_message(
                user_id,
                f"🎉 تبریک!\n\n"
                f"⭐ به Level {user['level']} رسیدی!\n"
                f"🪙 پاداش: {reward} سکه"
            )
        except:
            pass


# ==================================================
# ابزار ادمین
# ==================================================

def is_admin(user_id):
    return user_id == ADMIN_ID


def is_banned(user_id):

    return (
        user_id in users
        and users[user_id]["banned"]
    )


# ==================================================
# منوی اصلی
# ==================================================

def main_keyboard(user_id=None):

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

    if user_id == ADMIN_ID:
        kb.row("👑 مدیریت")

    return kb


# ==================================================
# START
# ==================================================

@bot.message_handler(commands=["start"])
def start(message):

    user_id = message.from_user.id

    if is_banned(user_id):

        bot.send_message(
            message.chat.id,
            "🚫 شما از استفاده از این بات محروم شده‌اید."
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

    # پاداش روزانه
    today = str(date.today())

    if not is_new and user["last_daily"] != today:

        user["last_daily"] = today
        user["streak"] += 1

        user["coins"] += 50

        add_xp(user_id, 20)

        bot.send_message(
            message.chat.id,
            f"🎁 پاداش روزانه دریافت شد!\n\n"
            f"🪙 +50 سکه\n"
            f"⭐ +20 XP\n"
            f"🔥 استریک: {user['streak']} روز"
        )

    if is_new:

        bot.send_message(
            message.chat.id,
            f"""
🎉 به «چت ناشناس» خوش اومدی!

🆔 کد کاربری شما:
{user['code']}

اینجا می‌تونی با افراد جدید
به صورت ناشناس چت کنی، بازی کنی،
XP بگیری و رتبه‌ات رو بالا ببری. 🔥
"""
        )

    bot.send_message(
        message.chat.id,
        "🏠 منوی اصلی:",
        reply_markup=main_keyboard(user_id)
    )


# ==================================================
# پروفایل
# ==================================================

@bot.message_handler(
    func=lambda m: m.text == "👤 پروفایل"
)
def profile(message):

    user_id = message.from_user.id

    if user_id not in users:
        return

    user = users[user_id]

    needed = xp_needed(user["level"])

    progress = int(
        (user["xp"] / needed) * 10
    )

    progress = min(progress, 10)

    bar = (
        "🟦" * progress
        + "⬜" * (10 - progress)
    )

    text = f"""
╭━━━━━━━━━━━━━━╮
       👤 پروفایل من
╰━━━━━━━━━━━━━━╯

👤 نام: {user['name']}
🆔 کد کاربری: {user['code']}

👑 رتبه: {user['rank']}
⭐ Level: {user['level']}

✨ XP: {user['xp']} / {needed}
{bar}

🪙 سکه: {user['coins']}
💰 موجودی: {user['balance']}

🔥 استریک: {user['streak']} روز

💬 تعداد چت‌ها: {user['chats']}
📨 تعداد پیام‌ها: {user['messages']}

🏅 وضعیت: کاربر فعال
"""

    bot.send_message(
        message.chat.id,
        text
    )


# ==================================================
# کیف پول
# ==================================================

@bot.message_handler(
    func=lambda m: m.text == "🪙 کیف پول"
)
def wallet(message):

    user_id = message.from_user.id

    if user_id not in users:
        return

    user = users[user_id]

    bot.send_message(
        message.chat.id,
        f"""
🪙 کیف پول

💰 موجودی:
{user['balance']}

🪙 سکه:
{user['coins']}

👑 رتبه:
{user['rank']}
"""
    )


# ==================================================
# مأموریت‌ها
# ==================================================

@bot.message_handler(
    func=lambda m: m.text == "🎯 مأموریت‌ها"
)
def missions(message):

    bot.send_message(
        message.chat.id,
        """
🎯 مأموریت‌های امروز

💬 ارسال 10 پیام
🎁 پاداش: 100 XP

👥 پیدا کردن یک چت جدید
🎁 پاداش: 50 XP

🎮 انجام یک بازی
🎁 پاداش: 50 سکه

🔥 ورود روزانه
🎁 پاداش: 50 سکه
"""
    )


# ==================================================
# جوایز
# ==================================================

@bot.message_handler(
    func=lambda m: m.text == "🎁 جوایز"
)
def rewards(message):

    bot.send_message(
        message.chat.id,
        """
🎁 جوایز

⭐ با افزایش Level و فعالیت بیشتر
می‌تونی جوایز بیشتری دریافت کنی.

🔥 هر روز وارد شو تا استریکت بیشتر بشه!
"""
    )


# ==================================================
# بازی‌ها
# ==================================================

@bot.message_handler(
    func=lambda m: m.text == "🎮 بازی‌ها"
)
def games(message):

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "🎯 حدس عدد",
            callback_data="guess"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "✊ سنگ 🖐 کاغذ ✌️ قیچی",
            callback_data="rps"
        )
    )

    bot.send_message(
        message.chat.id,
        "🎮 یک بازی انتخاب کن:",
        reply_markup=kb
    )


# ==================================================
# حدس عدد
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "guess"
)
def guess_game(call):

    user_id = call.from_user.id

    if user_id not in users:
        return

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

    bot.edit_message_text(
        "🎯 من یک عدد بین 1 تا 5 انتخاب کردم!\n\n"
        "حدست رو بزن:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb
    )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("guess_")
)
def guess_result(call):

    parts = call.data.split("_")

    selected = int(parts[1])
    number = int(parts[2])

    user_id = call.from_user.id

    if selected == number:

        users[user_id]["coins"] += 100

        add_xp(
            user_id,
            50
        )

        text = (
            "🎉 درست حدس زدی!\n\n"
            f"🔢 عدد: {number}\n"
            "🪙 +100 سکه\n"
            "⭐ +50 XP"
        )

    else:

        text = (
            "❌ اشتباه بود!\n\n"
            f"🔢 عدد درست: {number}"
        )

    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id
    )


# ==================================================
# سنگ کاغذ قیچی
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "rps"
)
def rps_game(call):

    kb = types.InlineKeyboardMarkup()

    kb.row(
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

    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        "🎮 انتخاب کن:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb
    )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("rps_")
)
def rps_result(call):

    choices = [
        "rock",
        "paper",
        "scissors"
    ]

    user_choice = call.data.replace(
        "rps_",
        ""
    )

    bot_choice = random.choice(
        choices
    )

    names = {
        "rock": "✊ سنگ",
        "paper": "🖐 کاغذ",
        "scissors": "✌️ قیچی"
    }

    if user_choice == bot_choice:

        result = "🤝 مساوی شد!"

    elif (
        (user_choice == "rock"
         and bot_choice == "scissors")
        or
        (user_choice == "paper"
         and bot_choice == "rock")
        or
        (user_choice == "scissors"
         and bot_choice == "paper")
    ):

        users[call.from_user.id]["coins"] += 100

        add_xp(
            call.from_user.id,
            50
        )

        result = (
            "🎉 تو بردی!\n"
            "🪙 +100 سکه\n"
            "⭐ +50 XP"
        )

    else:

        result = "😅 باختی!"

    bot.answer_callback_query(
        call.id
    )

    bot.edit_message_text(
        f"""
🎮 نتیجه

👤 تو: {names[user_choice]}
🤖 بات: {names[bot_choice]}

{result}
""",
        call.message.chat.id,
        call.message.message_id
    )


# ==================================================
# رتبه‌بندی
# ==================================================

@bot.message_handler(
    func=lambda m: m.text == "🏆 رتبه‌بندی"
)
def leaderboard(message):

    if not users:

        bot.send_message(
            message.chat.id,
            "هنوز کاربری وجود ندارد."
        )

        return

    ranking = sorted(
        users.values(),
        key=lambda x: (
            x["level"],
            x["xp"]
        ),
        reverse=True
    )

    text = "🏆 رتبه‌بندی کاربران\n\n"

    for index, user in enumerate(
        ranking[:10],
        1
    ):

        text += (
            f"{index}. 👤 {user['name']} "
            f"— Level {user['level']} "
            f"⭐ {user['xp']} XP\n"
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

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "🥈 Silver - 50,000",
            callback_data="shop_silver"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "🥇 Gold - 160,000",
            callback_data="shop_gold"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "💎 Diamond - 300,000",
            callback_data="shop_diamond"
        )
    )

    bot.send_message(
        message.chat.id,
        "🛒 فروشگاه رتبه‌ها:",
        reply_markup=kb
    )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("shop_")
)
def buy_rank(call):

    user_id = call.from_user.id

    if user_id not in users:
        return

    prices = {
        "shop_silver": (
            50000,
            "Silver"
        ),
        "shop_gold": (
            160000,
            "Gold"
        ),
        "shop_diamond": (
            300000,
            "Diamond"
        )
    }

    if call.data not in prices:
        return

    price, rank = prices[call.data]

    user = users[user_id]

    if user["balance"] < price:

        bot.answer_callback_query(
            call.id,
            "❌ موجودی کافی نیست!",
            show_alert=True
        )

        return

    user["balance"] -= price
    user["rank"] = rank

    bot.answer_callback_query(
        call.id,
        "✅ خرید موفق بود!"
    )

    bot.send_message(
        user_id,
        f"""
🎉 خرید موفق!

👑 رتبه جدید:
{rank}

💰 مبلغ پرداختی:
{price:,}
"""
    )


# ==================================================
# دعوت دوستان
# ==================================================

@bot.message_handler(
    func=lambda m: m.text == "👥 دعوت دوستان"
)
def referrals(message):

    user_id = message.from_user.id

    if user_id not in users:
        return

    bot_info = bot.get_me()

    link = (
        f"https://t.me/"
        f"{bot_info.username}"
        f"?start=ref{user_id}"
    )

    bot.send_message(
        message.chat.id,
        f"""
👥 دعوت دوستان

🔗 لینک دعوت اختصاصی تو:

{link}

🎁 با دعوت دوستان می‌تونی
پاداش دریافت کنی.
"""
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

🔔 اعلان‌ها: فعال
🕵️ حالت ناشناس: فعال
🔒 حریم خصوصی: فعال

نسخه آزمایشی
"""
    )


# ==================================================
# شروع چت ناشناس
# ==================================================

@bot.message_handler(
    func=lambda m: m.text == "💬 چت"
)
def chat_menu(message):

    user_id = message.from_user.id

    if user_id not in users:
        return

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "🔎 پیدا کردن چت",
            callback_data="find_chat"
        )
    )

    bot.send_message(
        message.chat.id,
        """
💬 چت ناشناس

با یک نفر به صورت ناشناس
وارد گفتگو شو.

نام و رتبه انتخابی کاربر
برای طرف مقابل نمایش داده می‌شود.
""",
        reply_markup=kb
    )


# ==================================================
# پیدا کردن چت
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "find_chat"
)
def find_chat(call):

    user_id = call.from_user.id

    if user_id in active_chats:

        bot.answer_callback_query(
            call.id,
            "❌ شما همین الان داخل یک چت هستید!",
            show_alert=True
        )

        return

    # اگر قبلاً در صف است
    if user_id in waiting_users:

        bot.answer_callback_query(
            call.id,
            "⏳ شما در صف هستید.",
            show_alert=True
        )

        return

    # پیدا کردن نفر اول صف
    partner_id = None

    for waiting_id in waiting_users:

        if waiting_id != user_id:
            partner_id = waiting_id
            break

    if partner_id is None:

        waiting_users.append(user_id)

        bot.answer_callback_query(
            call.id
        )

        bot.send_message(
            user_id,
            "🔎 در حال پیدا کردن یک نفر...\n\n"
            "⏳ لطفاً صبر کن."
        )

        return

    # حذف نفر دوم از صف
    if user_id in waiting_users:
        waiting_users.remove(user_id)

    if partner_id in waiting_users:
        waiting_users.remove(partner_id)

    # ایجاد چت
    active_chats[user_id] = partner_id
    active_chats[partner_id] = user_id

    users[user_id]["chats"] += 1
    users[partner_id]["chats"] += 1

    bot.answer_callback_query(
        call.id
    )

    bot.send_message(
        user_id,
        """
🎉 یک نفر پیدا شد!

💬 چت شما شروع شد.

برای پایان دادن:
 /end

برای گزارش:
 /report
"""
    )

    bot.send_message(
        partner_id,
        """
🎉 یک نفر پیدا شد!

💬 چت شما شروع شد.

برای پایان دادن:
 /end

برای گزارش:
 /report
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
            message.chat.id,
            "❌ شما داخل چت ناشناس نیستید."
        )

        return

    partner_id = active_chats.get(
        user_id
    )

    # قطع ارتباط
    active_chats.pop(
        user_id,
        None
    )

    active_chats.pop(
        partner_id,
        None
    )

    bot.send_message(
        user_id,
        """
🛑 چت پایان یافت.

برای پیدا کردن یک نفر جدید:
💬 چت
➡️ 🔎 پیدا کردن چت
"""
    )

    if partner_id:

        bot.send_message(
            partner_id,
            """
🛑 طرف مقابل چت را پایان داد.

برای پیدا کردن یک نفر جدید:
💬 چت
➡️ 🔎 پیدا کردن چت
"""
        )


# ==================================================
# گزارش
# ==================================================

@bot.message_handler(
    commands=["report"]
)
def report_user(message):

    user_id = message.from_user.id

    if user_id not in active_chats:

        bot.send_message(
            message.chat.id,
            "❌ شما داخل چت ناشناس نیستید."
        )

        return

    partner_id = active_chats[user_id]

    reports.append({
        "reporter": user_id,
        "reported": partner_id
    })

    bot.send_message(
        message.chat.id,
        """
🚨 گزارش ثبت شد.

گزارش شما برای مدیریت ارسال شد.
"""
    )


# ==================================================
# پیام‌های داخل چت ناشناس
#
# نکته مهم:
# هیچ پیام شروع‌شده با / ارسال نمی‌شود.
# ==================================================

@bot.message_handler(
    func=lambda m: (
        m.from_user.id in active_chats
        and m.text is not None
        and not m.text.startswith("/")
    )
)
def anonymous_chat(message):

    user_id = message.from_user.id

    partner_id = active_chats.get(
        user_id
    )

    if not partner_id:
        return

    if partner_id not in active_chats:

        active_chats.pop(
            user_id,
            None
        )

        bot.send_message(
            user_id,
            "❌ این چت دیگر فعال نیست."
        )

        return

    user = users.get(user_id)

    if not user:
        return

    user["messages"] += 1

    add_xp(
        user_id,
        5
    )

    bot.send_message(
        partner_id,
        f"""
👤 {user['name']}

{message.text}
"""
    )


# ==================================================
# مدیریت
# ==================================================

def admin_panel(message):

    if not is_admin(message.from_user.id):

        bot.send_message(
            message.chat.id,
            "⛔ دسترسی غیرمجاز."
        )

        return

    kb = types.InlineKeyboardMarkup()

    kb.row(
        types.InlineKeyboardButton(
            "📊 آمار",
            callback_data="admin_stats"
        ),
        types.InlineKeyboardButton(
            "👥 کاربران",
            callback_data="admin_users"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            "🔎 جستجوی کاربر",
            callback_data="admin_search"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            "💰 افزایش پول",
            callback_data="admin_add_money"
        ),
        types.InlineKeyboardButton(
            "💸 کاهش پول",
            callback_data="admin_remove_money"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            "⭐ تغییر XP",
            callback_data="admin_xp"
        ),
        types.InlineKeyboardButton(
            "🪙 تغییر سکه",
            callback_data="admin_coins"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            "👑 تغییر رتبه",
            callback_data="admin_rank"
        ),
        types.InlineKeyboardButton(
            "🚫 بن کاربر",
            callback_data="admin_ban"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            "📢 پیام همگانی",
            callback_data="admin_broadcast"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            "🚨 گزارش‌ها",
            callback_data="admin_reports"
        )
    )

    bot.send_message(
        message.chat.id,
        "👑 پنل مدیریت\n\nیک گزینه را انتخاب کن:",
        reply_markup=kb
    )


@bot.message_handler(
    commands=["admin"]
)
def admin_command(message):

    admin_panel(message)


@bot.message_handler(
    func=lambda m: m.text == "👑 مدیریت"
)
def admin_button(message):

    admin_panel(message)


# ==================================================
# آمار ادمین
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "admin_stats"
)
def admin_stats(call):

    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(
        call.id
    )

    bot.send_message(
        call.message.chat.id,
        f"""
📊 آمار بات

👥 کاربران:
{len(users)}

⏳ در صف چت:
{len(waiting_users)}

💬 چت‌های فعال:
{len(active_chats) // 2}

🚨 گزارش‌ها:
{len(reports)}
"""
    )


# ==================================================
# تعداد کاربران
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "admin_users"
)
def admin_users(call):

    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(
        call.id
    )

    if not users:

        bot.send_message(
            call.message.chat.id,
            "👥 هنوز کاربری ثبت نشده."
        )

        return

    text = "👥 کاربران:\n\n"

    for user in list(users.values())[:50]:

        text += (
            f"🆔 {user['code']} | "
            f"{user['name']} | "
            f"Level {user['level']}\n"
        )

    bot.send_message(
        call.message.chat.id,
        text
    )


# ==================================================
# جستجوی کاربر
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "admin_search"
)
def admin_search(call):

    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(
        call.id
    )

    msg = bot.send_message(
        call.message.chat.id,
        "🔎 کد کاربری را وارد کن:\nمثلاً 0001"
    )

    bot.register_next_step_handler(
        msg,
        search_user_result
    )


def search_user_result(message):

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
            "❌ کاربر پیدا نشد."
        )

        return

    bot.send_message(
        message.chat.id,
        f"""
👤 اطلاعات کاربر

🆔 کد:
{found['code']}

👤 نام:
{found['name']}

📱 Telegram ID:
{found['id']}

👑 رتبه:
{found['rank']}

⭐ Level:
{found['level']}

✨ XP:
{found['xp']}

🪙 سکه:
{found['coins']}

💰 موجودی:
{found['balance']}

🔥 استریک:
{found['streak']}

🚫 بن:
{"بله" if found["banned"] else "خیر"}
"""
    )


# ==================================================
# افزایش پول
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "admin_add_money"
)
def admin_add_money(call):

    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(
        call.id
    )

    msg = bot.send_message(
        call.message.chat.id,
        "💰 به این شکل وارد کن:\n\n"
        "کد کاربر مبلغ\n\n"
        "مثال:\n"
        "0001 50000"
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
            "❌ فرمت اشتباه است."
        )

        return

    target = None

    for user in users.values():

        if user["code"] == code:
            target = user
            break

    if not target:

        bot.send_message(
            message.chat.id,
            "❌ کاربر پیدا نشد."
        )

        return

    target["balance"] += amount

    bot.send_message(
        message.chat.id,
        f"✅ {amount:,} به موجودی کاربر {code} اضافه شد."
    )


# ==================================================
# کاهش پول
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "admin_remove_money"
)
def admin_remove_money(call):

    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(
        call.id
    )

    msg = bot.send_message(
        call.message.chat.id,
        "💸 به این شکل وارد کن:\n\n"
        "کد کاربر مبلغ\n\n"
        "مثال:\n"
        "0001 50000"
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

        bot.send_message(
            message.chat.id,
            "❌ فرمت اشتباه است."
        )

        return

    target = None

    for user in users.values():

        if user["code"] == code:
            target = user
            break

    if not target:

        bot.send_message(
            message.chat.id,
            "❌ کاربر پیدا نشد."
        )

        return

    target["balance"] = max(
        0,
        target["balance"] - amount
    )

    bot.send_message(
        message.chat.id,
        f"✅ {amount:,} از موجودی کاربر {code} کم شد."
    )


# ==================================================
# تغییر XP
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "admin_xp"
)
def admin_xp(call):

    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(
        call.id
    )

    msg = bot.send_message(
        call.message.chat.id,
        "⭐ به این شکل وارد کن:\n\n"
        "کد کاربر مقدار XP\n\n"
        "مثال:\n"
        "0001 500"
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

        bot.send_message(
            message.chat.id,
            "❌ فرمت اشتباه است."
        )

        return

    target = None

    for user in users.values():

        if user["code"] == code:
            target = user
            break

    if not target:

        bot.send_message(
            message.chat.id,
            "❌ کاربر پیدا نشد."
        )

        return

    add_xp(
        target["id"],
        amount
    )

    bot.send_message(
        message.chat.id,
        f"✅ {amount} XP به کاربر {code} اضافه شد."
    )


# ==================================================
# تغییر سکه
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "admin_coins"
)
def admin_coins(call):

    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(
        call.id
    )

    msg = bot.send_message(
        call.message.chat.id,
        "🪙 به این شکل وارد کن:\n\n"
        "کد کاربر مقدار\n\n"
        "مثال:\n"
        "0001 1000"
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

        bot.send_message(
            message.chat.id,
            "❌ فرمت اشتباه است."
        )

        return

    target = None

    for user in users.values():

        if user["code"] == code:
            target = user
            break

    if not target:

        bot.send_message(
            message.chat.id,
            "❌ کاربر پیدا نشد."
        )

        return

    target["coins"] += amount

    if target["coins"] < 0:
        target["coins"] = 0

    bot.send_message(
        message.chat.id,
        f"✅ سکه کاربر {code} تغییر کرد."
    )


# ==================================================
# تغییر رتبه
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "admin_rank"
)
def admin_rank(call):

    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(
        call.id
    )

    msg = bot.send_message(
        call.message.chat.id,
        "👑 به این شکل وارد کن:\n\n"
        "کد کاربر رتبه\n\n"
        "مثال:\n"
        "0001 Gold"
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

        bot.send_message(
            message.chat.id,
            "❌ فرمت اشتباه است."
        )

        return

    target = None

    for user in users.values():

        if user["code"] == code:
            target = user
            break

    if not target:

        bot.send_message(
            message.chat.id,
            "❌ کاربر پیدا نشد."
        )

        return

    target["rank"] = rank

    bot.send_message(
        message.chat.id,
        f"👑 رتبه کاربر {code} شد: {rank}"
    )


# ==================================================
# بن کاربر
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "admin_ban"
)
def admin_ban(call):

    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(
        call.id
    )

    msg = bot.send_message(
        call.message.chat.id,
        "🚫 کد کاربر را وارد کن:"
    )

    bot.register_next_step_handler(
        msg,
        process_ban
    )


def process_ban(message):

    if not is_admin(message.from_user.id):
        return

    code = message.text.strip()

    target = None

    for user in users.values():

        if user["code"] == code:
            target = user
            break

    if not target:

        bot.send_message(
            message.chat.id,
            "❌ کاربر پیدا نشد."
        )

        return

    target["banned"] = not target["banned"]

    status = (
        "🚫 بن شد"
        if target["banned"]
        else "✅ از بن خارج شد"
    )

    bot.send_message(
        message.chat.id,
        f"کاربر {code}: {status}"
    )


# ==================================================
# پیام همگانی
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "admin_broadcast"
)
def admin_broadcast(call):

    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(
        call.id
    )

    msg = bot.send_message(
        call.message.chat.id,
        "📢 پیام همگانی را بنویس:"
    )

    bot.register_next_step_handler(
        msg,
        process_broadcast
    )


def process_broadcast(message):

    if not is_admin(message.from_user.id):
        return

    success = 0

    for user_id in list(users.keys()):

        try:

            bot.send_message(
                user_id,
                f"📢 پیام مدیریت:\n\n{message.text}"
            )

            success += 1

        except:
            pass

    bot.send_message(
        message.chat.id,
        f"✅ پیام برای {success} کاربر ارسال شد."
    )


# ==================================================
# گزارش‌ها
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "admin_reports"
)
def admin_reports(call):

    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(
        call.id
    )

    if not reports:

        bot.send_message(
            call.message.chat.id,
            "🚨 گزارشی وجود ندارد."
        )

        return

    text = "🚨 گزارش‌ها\n\n"

    for index, report in enumerate(
        reports,
        1
    ):

        reporter = users.get(
            report["reporter"]
        )

        reported = users.get(
            report["reported"]
        )

        reporter_code = (
            reporter["code"]
            if reporter
            else "نامشخص"
        )

        reported_code = (
            reported["code"]
            if reported
            else "نامشخص"
        )

        text += (
            f"{index}. "
            f"گزارش‌دهنده: {reporter_code}\n"
            f"متهم: {reported_code}\n\n"
        )

    bot.send_message(
        call.message.chat.id,
        text
    )


# ==================================================
# اجرای بات
# ==================================================

print("Bot is running...")

bot.infinity_polling(
    skip_pending=True
)
