# -*- coding: utf-8 -*-
# چت ناشناس | نسخه تک‌فایلی
# کتابخانه:
# pip install pyTelegramBotAPI

import os
import telebot
from telebot import types
from supabase import create_client, Client
from datetime import datetime, timedelta
import random
import threading
import time
import re

# ============================================================
# فقط این قسمت را تغییر بده
# ============================================================

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7723971526
BOT_USERNAME = "chat_iranian_bot"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in GitHub Secrets")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL or SUPABASE_KEY is not set in GitHub Secrets")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    raise RuntimeError(f"Supabase connection setup failed: {e}")

# ============================================================
# تنظیمات
# ============================================================

BOT_NAME = "چت ناشناس"
WELCOME_COINS = 100
ONLINE_MINUTES = 10
ACCOUNT_CODE_MAX = 100000

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ============================================================
# Supabase - ذخیره و بازیابی اطلاعات اصلی کاربران
# ============================================================

def db_user_payload(u):
    """فقط ستون‌هایی را می‌فرستیم که در جدول users این پروژه ساخته شده‌اند."""
    payload = {
        "telegram_id": int(u["id"]),
        "username": u.get("username") or "",
        "first_name": u.get("name") or "کاربر",
        "phone": u.get("phone"),
        "profile_photo": u.get("photo"),
        "account_code": u.get("code"),
        "coins": int(u.get("coins", 0)),
        "balance": int(u.get("balance", 0)),
        "xp": int(u.get("xp", 0)),
        "level": int(u.get("level", 1)),
        "banned": bool(u.get("banned", False)),
        "last_activity": u.get("last_activity", now()).isoformat() if hasattr(u.get("last_activity", now()), "isoformat") else u.get("last_activity"),
    }
    return payload


def db_save_user(uid):
    try:
        u = users.get(uid)
        if not u:
            return False
        supabase.table("users").update(db_user_payload(u)).eq("telegram_id", int(uid)).execute()
        return True
    except Exception as e:
        print(f"[DB] save user {uid} failed: {e}")
        return False


def db_insert_user(u):
    try:
        result = supabase.table("users").insert(db_user_payload(u)).execute()
        row = (result.data or [None])[0]
        if row:
            u["_db_id"] = row.get("id")
        return bool(row)
    except Exception as e:
        print(f"[DB] insert user {u.get('id')} failed: {e}")
        return False


def db_load_users():
    """کاربران را در شروع بات از Supabase داخل حافظه می‌آورد."""
    try:
        result = supabase.table("users").select("*").execute()
        rows = result.data or []
        loaded = 0
        for row in rows:
            telegram_id = row.get("telegram_id")
            if telegram_id is None:
                continue
            uid = int(telegram_id)
            created = row.get("created_at")
            last_activity = row.get("last_activity")
            try:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00")) if created else now()
            except Exception:
                created_dt = now()
            try:
                last_dt = datetime.fromisoformat(last_activity.replace("Z", "+00:00")) if last_activity else now()
            except Exception:
                last_dt = now()

            users[uid] = {
                "id": uid,
                "_db_id": row.get("id"),
                "username": row.get("username") or "",
                "name": row.get("first_name") or "کاربر",
                "code": row.get("account_code") or "",
                "coins": int(row.get("coins") or 0),
                "balance": int(row.get("balance") or 0),
                "xp": int(row.get("xp") or 0),
                "level": int(row.get("level") or 1),
                "ranks": [],
                "phone": row.get("phone"),
                "photo": row.get("profile_photo"),
                "anonymous": True,
                "banned": bool(row.get("banned", False)),
                "warnings": 0,
                "messages": 0,
                "chats": 0,
                "wins": 0,
                "referrals": 0,
                "joined": created_dt,
                "last_activity": last_dt,
                "game_wins": 0,
                "game_plays": 0,
                "daily_last": None,
                "daily_streak": 0,
                "mission_progress": {},
                "_role_keys": set(),
            }
            user_last_activity[uid] = last_dt
            loaded += 1

        print(f"[DB] Loaded {loaded} users from Supabase")
        return True
    except Exception as e:
        print(f"[DB] load users failed: {e}")
        return False


def db_save_rank_assignment(uid, rank_key, expires):
    """رنک خریداری/اعطا شده را در user_ranks ثبت می‌کند."""
    try:
        u = users.get(uid)
        if not u or not u.get("_db_id"):
            return False
        rank_rows = supabase.table("ranks").select("id").eq("key", rank_key).limit(1).execute().data or []
        if not rank_rows:
            return False
        payload = {
            "user_id": u["_db_id"],
            "rank_id": rank_rows[0]["id"],
            "expires_at": expires.isoformat() if expires else None,
        }
        supabase.table("user_ranks").insert(payload).execute()
        return True
    except Exception as e:
        print(f"[DB] save rank {uid}/{rank_key} failed: {e}")
        return False


def db_load_ranks_and_roles():
    """رنک‌ها و نقش‌های مدیریتی را از جداول Supabase می‌خواند."""
    try:
        rank_rows = supabase.table("ranks").select("*").execute().data or []
        rank_by_id = {str(r.get("id")): r for r in rank_rows if r.get("id") is not None}

        user_rank_rows = supabase.table("user_ranks").select("*").execute().data or []
        db_to_uid = {str(u.get("_db_id")): uid for uid, u in users.items() if u.get("_db_id") is not None}
        for rr in user_rank_rows:
            uid = db_to_uid.get(str(rr.get("user_id")))
            if uid is None:
                continue
            rank_row = rank_by_id.get(str(rr.get("rank_id")), {})
            rank_key = rank_row.get("key") or rank_row.get("slug") or rank_row.get("code")
            if not rank_key or rank_key not in RANKS:
                continue
            expires = rr.get("expires_at")
            exp_dt = None
            if expires:
                try:
                    exp_dt = datetime.fromisoformat(str(expires).replace("Z", "+00:00"))
                except Exception:
                    exp_dt = None
            users[uid]["ranks"].append({"rank": rank_key, "expires": exp_dt})

        role_rows = supabase.table("roles").select("*").execute().data or []
        role_key_by_id = {}
        for role in role_rows:
            rid = role.get("id")
            key = role.get("key") or role.get("name")
            if rid is not None and key:
                role_key_by_id[str(rid)] = str(key)

        user_role_rows = supabase.table("user_roles").select("*").execute().data or []
        for ur in user_role_rows:
            uid = db_to_uid.get(str(ur.get("user_id")))
            if uid is None:
                continue
            key = role_key_by_id.get(str(ur.get("role_id")))
            if key:
                users[uid].setdefault("_role_keys", set()).add(key)

        print("[DB] Loaded ranks and roles")
    except Exception as e:
        print(f"[DB] load ranks/roles failed: {e}")


def db_sync_user(uid):
    """ذخیره امن تغییرات کاربر؛ خطای دیتابیس بات را متوقف نمی‌کند."""
    try:
        db_save_user(uid)
        return True
    except Exception:
        return False

# ============================================================
# حافظه موقت
# توجه: با ری‌استارت شدن بات همه اطلاعات پاک می‌شود.
# ============================================================

users = {}
chats = {}
waiting_users = []
reports = []
warnings = []
admin_logs = []
reviews = []
suggestions = []
transactions = []
messages_log = []
blocks = {}
temp_bans = {}
giveaways = {}
challenges = {}
missions = {}
ratings = []

pending = {}
user_last_activity = {}

# ============================================================
# رنک‌ها
# ============================================================

RANKS = {
    "member": {
        "name": "ممبر",
        "price": 0,
        "days": 0,
        "priority": 0
    },
    "silver": {
        "name": "🥈 سیلور",
        "price": 500,
        "days": 30,
        "priority": 10
    },
    "gold": {
        "name": "🥇 گلد",
        "price": 1600,
        "days": 30,
        "priority": 20
    },
    "diamond": {
        "name": "💎 دایموند",
        "price": 3500,
        "days": 30,
        "priority": 30
    },
    "vip": {
        "name": "👑 VIP",
        "price": 7000,
        "days": 30,
        "priority": 40
    },
    "moderator": {
        "name": "Moderator",
        "price": 0,
        "days": 0,
        "priority": 100
    }
}

# ============================================================
# ابزارها
# ============================================================

def now():
    return datetime.now()


def touch(uid):
    user_last_activity[uid] = now()


def is_admin(uid):
    return uid == ADMIN_ID


def is_banned(uid):
    if uid in temp_bans:
        if now() < temp_bans[uid]["until"]:
            return True
        del temp_bans[uid]

    if uid in users:
        return users[uid].get("banned", False)

    return False


def is_moderator(uid):
    if is_admin(uid):
        return True

    u = users.get(uid)
    if not u:
        return False

    roles = u.get("_role_keys", set())
    if roles.intersection({"moderator", "senior_moderator", "senior_inspector", "manager", "owner"}):
        return True

    # سازگاری با نسخه قدیمی
    for r in u.get("ranks", []):
        if r["rank"] == "moderator":
            if r.get("expires") is None or now() < r["expires"]:
                return True

    return False


def generate_code():
    used = {u["code"] for u in users.values()}

    for i in range(1, ACCOUNT_CODE_MAX + 1):
        code = f"{i:04d}"
        if code not in used:
            return code

    return None


def get_user(uid):
    return users.get(uid)


def create_user(message, referral=None):
    uid = message.from_user.id

    if uid in users:
        return users[uid]

    code = generate_code()

    if not code:
        return None

    username = message.from_user.username or ""
    first_name = message.from_user.first_name or "کاربر"

    users[uid] = {
        "id": uid,
        "username": username,
        "name": first_name,
        "code": code,
        "coins": WELCOME_COINS,
        "balance": 0,
        "xp": 0,
        "level": 1,
        "ranks": [],
        "phone": None,
        "photo": None,
        "anonymous": True,
        "banned": False,
        "warnings": 0,
        "messages": 0,
        "chats": 0,
        "wins": 0,
        "referrals": 0,
        "joined": now(),
        "last_activity": now(),
        "game_wins": 0,
        "game_plays": 0,
        "daily_last": None,
        "daily_streak": 0,
        "mission_progress": {},
        "_role_keys": set(),
    }

    if not db_insert_user(users[uid]):
        # اگر کاربر قبلاً در دیتابیس وجود داشته ولی حافظه خالی بوده، دوباره از دیتابیس می‌خوانیم.
        try:
            row = (supabase.table("users").select("*").eq("telegram_id", int(uid)).limit(1).execute().data or [None])[0]
            if row:
                users[uid]["_db_id"] = row.get("id")
                users[uid]["code"] = row.get("account_code") or users[uid]["code"]
                users[uid]["coins"] = int(row.get("coins") or users[uid]["coins"])
                users[uid]["balance"] = int(row.get("balance") or 0)
                users[uid]["xp"] = int(row.get("xp") or 0)
                users[uid]["level"] = int(row.get("level") or 1)
        except Exception as e:
            print(f"[DB] recovery for user {uid} failed: {e}")

    admin_log(
        "ثبت کاربر",
        uid,
        f"کد حساب: {code}"
    )

    if referral:
        inviter = find_by_code(referral)
        if inviter and inviter != uid:
            users[inviter]["referrals"] += 1
            users[inviter]["coins"] += 50
            add_xp(inviter, 25)

            notify(
                inviter,
                "🎁 <b>جایزه دعوت</b>\n\n"
                "یک کاربر با لینک دعوت شما وارد شد.\n"
                "🪙 +50 سکه\n"
                "⭐ +25 XP"
            )

    return users[uid]


def ensure_user(message):
    uid = message.from_user.id

    if uid not in users:
        return create_user(message)

    users[uid]["username"] = message.from_user.username or users[uid]["username"]
    users[uid]["name"] = message.from_user.first_name or users[uid]["name"]

    touch(uid)
    users[uid]["last_activity"] = now()
    db_sync_user(uid)

    return users[uid]


def find_by_code(code):
    code = str(code).strip()

    for uid, u in users.items():
        if u["code"] == code:
            return uid

    return None


def find_user(value):
    value = str(value).strip()

    if value.isdigit():
        uid = int(value)

        if uid in users:
            return uid

        uid2 = find_by_code(value)
        if uid2:
            return uid2

    value = value.lstrip("@").lower()

    for uid, u in users.items():
        if u["username"].lower() == value:
            return uid

    for uid, u in users.items():
        if u["name"].lower() == value:
            return uid

    return None


def display_name(uid):
    u = users.get(uid)

    if not u:
        return "کاربر"

    return u["name"]


def visible_rank(uid):
    u = users.get(uid)

    if not u:
        return None

    active = []

    for r in u["ranks"]:
        if r["rank"] == "moderator":
            continue

        expires = r.get("expires")

        if expires and now() < expires:
            active.append(r)

    if not active:
        return "ممبر"

    active.sort(
        key=lambda x: RANKS[x["rank"]]["priority"],
        reverse=True
    )

    return RANKS[active[0]["rank"]]["name"]


def all_ranks_text(uid):
    u = users.get(uid)

    if not u:
        return "ممبر"

    result = []

    for r in u["ranks"]:
        rank_name = RANKS[r["rank"]]["name"]

        if r.get("expires"):
            remain = r["expires"] - now()
            days = max(0, remain.days)
            result.append(f"{rank_name} — {days} روز")
        else:
            result.append(rank_name)

    if is_moderator(uid):
        result.append("🛡 ناظر")

    return "\n".join(result) if result else "ممبر"


def notify(uid, text):
    try:
        bot.send_message(uid, text)
    except Exception:
        pass


def admin_log(action, target=None, details=""):
    admin_logs.append({
        "admin": ADMIN_ID,
        "target": target,
        "action": action,
        "details": details,
        "time": now()
    })


def transaction(uid, kind, amount, reason=""):
    transactions.append({
        "uid": uid,
        "kind": kind,
        "amount": amount,
        "reason": reason,
        "time": now()
    })


# ============================================================
# XP و Level
# ============================================================

def xp_needed(level):
    return level * 100


def add_xp(uid, amount):
    if uid not in users:
        return

    if amount < 0:
        return

    u = users[uid]
    u["xp"] += amount

    while u["xp"] >= xp_needed(u["level"]):
        u["xp"] -= xp_needed(u["level"])
        u["level"] += 1

        notify(
            uid,
            f"🎉 <b>لول آپ شد!</b>\n\n"
            f"سطح جدید: {u['level']}"
        )

    db_sync_user(uid)


# ============================================================
# منو
# ============================================================

def main_menu(uid):
    kb = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=2
    )

    kb.add(
        types.KeyboardButton("💬 چت"),
        types.KeyboardButton("👤 پروفایل")
    )

    kb.add(
        types.KeyboardButton("🪙 سکه"),
        types.KeyboardButton("⭐ رنک‌ها")
    )

    kb.add(
        types.KeyboardButton("🎮 بازی"),
        types.KeyboardButton("🎯 مأموریت‌ها")
    )

    kb.add(
        types.KeyboardButton("🎁 جوایز"),
        types.KeyboardButton("🏆 چالش‌ها")
    )

    kb.add(
        types.KeyboardButton("👥 دعوت دوستان"),
        types.KeyboardButton("⚙️ تنظیمات")
    )

    kb.add(
        types.KeyboardButton("❓ راهنما"),
        types.KeyboardButton("📝 نظر و پیشنهاد")
    )

    if is_admin(uid):
        kb.add(types.KeyboardButton("🛠 پنل مدیریت"))

    elif is_moderator(uid):
        kb.add(types.KeyboardButton("🛡 پنل ناظر"))

    return kb


def admin_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)

    buttons = [
        ("📊 داشبورد", "admin_dashboard"),
        ("👥 کاربران", "admin_users"),
        ("🔎 جستجوی کاربر", "admin_search"),
        ("🚨 گزارش‌ها", "admin_reports"),
        ("🛡 ناظران", "admin_mods"),
        ("⚠️ هشدارها", "admin_warnings"),
        ("🪙 مدیریت سکه", "admin_coins"),
        ("💰 مدیریت اعتبار", "admin_balance"),
        ("⭐ مدیریت XP", "admin_xp"),
        ("🏆 مدیریت رنک", "admin_rank"),
        ("🎁 قرعه‌کشی", "admin_giveaway"),
        ("🎯 چالش‌ها", "admin_challenge"),
        ("📢 پیام همگانی", "admin_broadcast"),
        ("📣 اعلان", "admin_announce"),
        ("💬 نظرات", "admin_reviews"),
        ("💡 پیشنهادات", "admin_suggestions"),
        ("📈 آمار", "admin_stats"),
        ("📋 لاگ مدیریت", "admin_logs"),
        ("💬 چت‌های فعال", "admin_chats"),
        ("🔍 پیام‌ها", "admin_messages"),
        ("🚫 مسدود کردن", "admin_ban"),
        ("🔓 رفع مسدودی", "admin_unban"),
        ("⏱ بن موقت", "admin_tempban"),
        ("🎟 جوایز", "admin_rewards"),
        ("🎮 بازی‌ها", "admin_games"),
        ("🎯 مأموریت‌ها", "admin_missions"),
        ("🏅 تنظیم رنک", "admin_rank_settings"),
        ("🧹 پاکسازی", "admin_cleanup"),
        ("⚙️ تنظیمات بات", "admin_settings"),
        ("🔐 امنیت", "admin_security"),
        ("📤 خروجی آمار", "admin_export"),
    ]

    for title, data in buttons:
        kb.add(types.InlineKeyboardButton(title, callback_data=data))

    return kb


def moderator_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)

    kb.add(
        types.InlineKeyboardButton(
            "💬 چت‌های فعال",
            callback_data="mod_chats"
        ),
        types.InlineKeyboardButton(
            "🚫 مسدود موقت",
            callback_data="mod_ban"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "⚠️ هشدار",
            callback_data="mod_warn"
        ),
        types.InlineKeyboardButton(
            "🚨 گزارش‌ها",
            callback_data="mod_reports"
        )
    )

    return kb


# ============================================================
# /start
# ============================================================

@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id

    args = message.text.split(maxsplit=1)

    referral = None

    if len(args) > 1:
        ref = args[1]

        if ref.startswith("ref_"):
            referral = ref[4:]

    new_user = uid not in users

    u = ensure_user(message)

    if new_user:
        bot.send_message(
            uid,
            "👋 <b>به چت ناشناس خوش اومدی!</b>\n\n"
            "اینجا می‌تونی با آدم‌های جدید آشنا بشی.\n\n"
            f"🆔 کد حساب شما: <code>{u['code']}</code>\n"
            f"🪙 سکه هدیه: {WELCOME_COINS}\n\n"
            "برای شروع از منوی پایین استفاده کن.",
            reply_markup=main_menu(uid)
        )
    else:
        bot.send_message(
            uid,
            "👋 دوباره خوش اومدی!",
            reply_markup=main_menu(uid)
        )


# ============================================================
# پروفایل
# ============================================================

def send_profile(uid):
    u = users[uid]

    rank = visible_rank(uid)

    text = (
        "👤 <b>پروفایل شما</b>\n\n"
        f"👤 نام: {u['name']}\n"
        f"🆔 کد: <code>{u['code']}</code>\n"
        f"⭐ سطح: {u['level']}\n"
        f"✨ XP: {u['xp']}/{xp_needed(u['level'])}\n"
        f"🪙 سکه: {u['coins']}\n"
        f"💰 اعتبار مجازی: {u['balance']:,} تومان\n"
        f"🏅 رنک نمایشی: {rank}\n\n"
        "<b>رنک‌های فعال:</b>\n"
        f"{all_ranks_text(uid)}"
    )

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "🖼 تغییر عکس",
            callback_data="profile_photo"
        ),
        types.InlineKeyboardButton(
            "🕵️ حالت ناشناس",
            callback_data="profile_anon"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "👁 حالت عادی",
            callback_data="profile_normal"
        )
    )

    bot.send_message(
        uid,
        text,
        reply_markup=kb
    )


# ============================================================
# سکه
# ============================================================

def coins_page(uid):
    u = users[uid]

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "🎁 جایزه روزانه",
            callback_data="daily"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "🛒 فروشگاه رنک",
            callback_data="rank_shop"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "👥 دعوت دوستان",
            callback_data="referral"
        )
    )

    bot.send_message(
        uid,
        "🪙 <b>کیف پول سکه</b>\n\n"
        f"موجودی: <b>{u['coins']}</b> سکه\n"
        f"💰 اعتبار مجازی: {u['balance']:,} تومان\n\n"
        "⚠️ اعتبار داخل بات مجازی است و امکان برداشت وجه واقعی ندارد.",
        reply_markup=kb
    )


# ============================================================
# چت
# ============================================================

def start_chat(uid):
    if is_banned(uid):
        bot.send_message(
            uid,
            "🚫 حساب شما مسدود است."
        )
        return

    if uid in chats:
        bot.send_message(
            uid,
            "❌ شما همین الان داخل یک چت هستید.\n"
            "برای پایان: /end"
        )
        return

    if uid in waiting_users:
        bot.send_message(
            uid,
            "⏳ در صف پیدا کردن مخاطب هستی..."
        )
        return

    # پیدا کردن نفر مناسب
    partner = None

    for x in waiting_users:
        if x != uid and not is_banned(x):
            partner = x
            break

    if partner:
        waiting_users.remove(partner)

        chat_id = f"{min(uid, partner)}_{max(uid, partner)}"

        chats[uid] = {
            "partner": partner,
            "chat_id": chat_id,
            "started": now()
        }

        chats[partner] = {
            "partner": uid,
            "chat_id": chat_id,
            "started": now()
        }

        users[uid]["chats"] += 1
        users[partner]["chats"] += 1

        add_xp(uid, 10)
        add_xp(partner, 10)

        send_chat_started(uid, partner)
        send_chat_started(partner, uid)

    else:
        waiting_users.append(uid)

        bot.send_message(
            uid,
            "🔎 <b>در حال پیدا کردن مخاطب...</b>\n\n"
            "به محض پیدا شدن یک نفر، چت شروع می‌شود.\n\n"
            "برای لغو صف: /cancel"
        )


def send_chat_started(uid, partner):
    u = users[uid]

    if u["anonymous"]:
        text = (
            "💬 <b>مخاطب پیدا شد!</b>\n\n"
            "🕵️ حالت ناشناس فعال است.\n"
            "هویت شما نمایش داده نمی‌شود.\n\n"
            "برای پایان: /end\n"
            "برای گزارش: /report\n"
            "برای مسدود کردن: /block"
        )
    else:
        p = users[partner]

        rank = visible_rank(partner)

        text = (
            "💬 <b>مخاطب پیدا شد!</b>\n\n"
            f"👤 {p['name']}\n"
            f"🏅 {rank}\n\n"
            "برای پایان: /end\n"
            "برای گزارش: /report\n"
            "برای مسدود کردن: /block"
        )

    bot.send_message(uid, text)


def end_chat(uid):
    if uid not in chats:
        bot.send_message(
            uid,
            "❌ شما داخل چتی نیستید."
        )
        return

    partner = chats[uid]["partner"]

    chat_id = chats[uid]["chat_id"]

    chats.pop(uid, None)
    chats.pop(partner, None)

    bot.send_message(
        uid,
        "🔴 چت پایان یافت.",
        reply_markup=main_menu(uid)
    )

    if partner in users:
        bot.send_message(
            partner,
            "🔴 مخاطب چت را پایان داد.",
            reply_markup=main_menu(partner)
        )

        ask_rating(partner, uid, chat_id)

    ask_rating(uid, partner, chat_id)


def ask_rating(uid, target, chat_id):
    if uid not in users:
        return

    kb = types.InlineKeyboardMarkup(row_width=5)

    for i in range(1, 6):
        kb.add(
            types.InlineKeyboardButton(
                str(i),
                callback_data=f"rate:{target}:{chat_id}:{i}"
            )
        )

    bot.send_message(
        uid,
        "⭐ <b>به این چت امتیاز بده:</b>\n"
        "۱ تا ۵",
        reply_markup=kb
    )


# ============================================================
# گزارش
# ============================================================

def start_report(uid):
    if uid not in chats:
        bot.send_message(
            uid,
            "❌ برای گزارش باید داخل چت باشید."
        )
        return

    pending[uid] = {
        "type": "report_message",
        "target": chats[uid]["partner"]
    }

    bot.send_message(
        uid,
        "🚨 <b>گزارش کاربر</b>\n\n"
        "اول پیام مشکل‌دار را همینجا بفرست یا فوروارد کن.\n\n"
        "می‌تواند متن، عکس، ویدیو یا فایل باشد."
    )


def finish_report_message(message):
    uid = message.from_user.id

    data = pending.get(uid)

    if not data:
        return

    target = data["target"]

    report = {
        "id": len(reports) + 1,
        "reporter": uid,
        "target": target,
        "message_id": message.message_id,
        "chat_id": message.chat.id,
        "text": message.text or message.caption or "",
        "content_type": message.content_type,
        "reason": None,
        "time": now(),
        "status": "new"
    }

    reports.append(report)

    pending[uid] = {
        "type": "report_reason",
        "report_id": report["id"]
    }

    kb = types.InlineKeyboardMarkup(row_width=2)

    reasons = [
        ("فحاشی", "profanity"),
        ("تهدید", "threat"),
        ("اسپم", "spam"),
        ("محتوای نامناسب", "inappropriate"),
        ("محتوای غیرقانونی", "illegal"),
        ("سایر", "other")
    ]

    for title, key in reasons:
        kb.add(
            types.InlineKeyboardButton(
                title,
                callback_data=f"report_reason:{key}"
            )
        )

    bot.send_message(
        uid,
        "دلیل گزارش را انتخاب کن:",
        reply_markup=kb
    )


# ============================================================
# بلاک
# ============================================================

def block_user(uid):
    if uid not in chats:
        bot.send_message(
            uid,
            "❌ داخل چت نیستی."
        )
        return

    target = chats[uid]["partner"]

    blocks.setdefault(uid, set())
    blocks[uid].add(target)

    admin_log(
        "بلاک کاربر",
        target,
        f"توسط {uid}"
    )

    bot.send_message(
        uid,
        "🚫 کاربر مسدود شد."
    )

    end_chat(uid)


# ============================================================
# رنک
# ============================================================

def rank_shop(uid):
    kb = types.InlineKeyboardMarkup(row_width=1)

    for key, r in RANKS.items():

        if key in ("member", "moderator"):
            continue

        kb.add(
            types.InlineKeyboardButton(
                f"{r['name']} | {r['price']} سکه | {r['days']} روز",
                callback_data=f"buy_rank:{key}"
            )
        )

    bot.send_message(
        uid,
        "🏆 <b>فروشگاه رنک</b>\n\n"
        "رنک‌ها با سکه خریداری می‌شوند.\n"
        "رنک‌ها ۳۰ روز فعال هستند.\n"
        "اگر چند رنک داشته باشید، همه حفظ می‌شوند.",
        reply_markup=kb
    )


def buy_rank(uid, rank):
    if rank not in RANKS:
        return

    r = RANKS[rank]

    if users[uid]["coins"] < r["price"]:
        bot.send_message(
            uid,
            "❌ سکه کافی نداری."
        )
        return

    users[uid]["coins"] -= r["price"]
    db_sync_user(uid)

    expires = now() + timedelta(days=r["days"])

    users[uid]["ranks"].append({
        "rank": rank,
        "expires": expires
    })
    db_save_rank_assignment(uid, rank, expires)
    db_sync_user(uid)

    transaction(
        uid,
        "خرید رنک",
        -r["price"],
        rank
    )

    bot.send_message(
        uid,
        f"🎉 <b>{r['name']}</b> خریداری شد!\n\n"
        f"⏳ مدت: {r['days']} روز\n"
        f"🪙 هزینه: {r['price']} سکه"
    )


# ============================================================
# روزانه
# ============================================================

def daily(uid):
    u = users[uid]

    today = now().date()

    if u["daily_last"] == today:
        bot.send_message(
            uid,
            "⏳ جایزه امروز را قبلاً گرفتی."
        )
        return

    if u["daily_last"] == today - timedelta(days=1):
        u["daily_streak"] += 1
    else:
        u["daily_streak"] = 1

    reward = 50 + (u["daily_streak"] * 10)

    u["coins"] += reward
    u["daily_last"] = today
    db_sync_user(uid)

    add_xp(uid, 20)

    bot.send_message(
        uid,
        "🎁 <b>جایزه روزانه</b>\n\n"
        f"🪙 +{reward} سکه\n"
        f"🔥 استریک: {u['daily_streak']}"
    )


# ============================================================
# دعوت
# ============================================================

def referral_page(uid):
    code = users[uid]["code"]

    bot.send_message(
        uid,
        "👥 <b>دعوت دوستان</b>\n\n"
        "لینک اختصاصی شما:\n"
        f"<code>https://t.me/{BOT_USERNAME}?start=ref_{code}</code>\n\n"
        "با هر عضو جدید:\n"
        "🪙 +50 سکه\n"
        "⭐ +25 XP"
    )


# ============================================================
# بازی
# ============================================================

def game_menu(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)

    kb.add(
        types.InlineKeyboardButton(
            "🎲 حدس عدد",
            callback_data="game_guess"
        ),
        types.InlineKeyboardButton(
            "🪙 شیر یا خط",
            callback_data="game_coin"
        )
    )

    bot.send_message(
        uid,
        "🎮 <b>بازی‌ها</b>\n\n"
        "بازی کن و XP و سکه بگیر.",
        reply_markup=kb
    )


def coin_game(uid):
    u = users[uid]

    result = random.choice(["شیر", "خط"])

    u["game_plays"] += 1

    reward = random.randint(5, 20)

    u["coins"] += reward
    db_sync_user(uid)
    add_xp(uid, 5)

    bot.send_message(
        uid,
        "🪙 <b>شیر یا خط</b>\n\n"
        f"نتیجه: <b>{result}</b>\n"
        f"🪙 جایزه: +{reward}"
    )


def guess_game(uid):
    number = random.randint(1, 5)

    pending[uid] = {
        "type": "guess",
        "number": number
    }

    bot.send_message(
        uid,
        "🎲 یک عدد بین ۱ تا ۵ حدس بزن."
    )


# ============================================================
# مأموریت‌ها
# ============================================================

def mission_page(uid):
    u = users[uid]

    text = (
        "🎯 <b>مأموریت‌ها</b>\n\n"
        "💬 انجام ۳ چت\n"
        f"پیشرفت: {min(u['chats'], 3)}/3\n\n"
        "💬 ارسال ۲۰ پیام\n"
        f"پیشرفت: {min(u['messages'], 20)}/20\n\n"
        "👥 دعوت ۲ نفر\n"
        f"پیشرفت: {min(u['referrals'], 2)}/2"
    )

    bot.send_message(uid, text)


# ============================================================
# تنظیمات
# ============================================================

def settings_page(uid):
    u = users[uid]

    kb = types.InlineKeyboardMarkup(row_width=2)

    kb.add(
        types.InlineKeyboardButton(
            "🕵️ ناشناس",
            callback_data="profile_anon"
        ),
        types.InlineKeyboardButton(
            "👁 عادی",
            callback_data="profile_normal"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "🖼 عکس پروفایل",
            callback_data="profile_photo"
        )
    )

    bot.send_message(
        uid,
        "⚙️ <b>تنظیمات</b>\n\n"
        f"حالت فعلی: {'ناشناس' if u['anonymous'] else 'عادی'}",
        reply_markup=kb
    )


# ============================================================
# نظر و پیشنهاد
# ============================================================

def review_page(uid):
    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "⭐ ثبت نظر",
            callback_data="new_review"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "💡 پیشنهاد",
            callback_data="new_suggestion"
        )
    )

    bot.send_message(
        uid,
        "📝 <b>نظر و پیشنهاد</b>\n\n"
        "نظر شما به مدیریت ارسال می‌شود.",
        reply_markup=kb
    )


# ============================================================
# پنل مدیریت
# ============================================================

def admin_panel(uid):
    if not is_admin(uid):
        return

    bot.send_message(
        uid,
        "🛠 <b>پنل مدیریت</b>\n\n"
        "یک گزینه را انتخاب کن:",
        reply_markup=admin_menu()
    )


def admin_dashboard(uid):
    text = (
        "📊 <b>داشبورد</b>\n\n"
        f"👥 کاربران: {len(users)}\n"
        f"💬 چت‌های فعال: {len(chats)//2}\n"
        f"⏳ صف چت: {len(waiting_users)}\n"
        f"🚨 گزارش‌ها: {len(reports)}\n"
        f"⚠️ هشدارها: {len(warnings)}\n"
        f"📝 نظرات: {len(reviews)}\n"
        f"💡 پیشنهادات: {len(suggestions)}\n"
        f"📋 لاگ‌ها: {len(admin_logs)}"
    )

    bot.send_message(uid, text)


def admin_users(uid):
    if not users:
        bot.send_message(uid, "کاربری وجود ندارد.")
        return

    text = "👥 <b>کاربران</b>\n\n"

    for i, (user_id, u) in enumerate(users.items()):
        if i >= 30:
            break

        text += (
            f"• {u['name']} | "
            f"<code>{u['code']}</code> | "
            f"{u['coins']} سکه\n"
        )

    bot.send_message(uid, text)


def admin_search_start(uid):
    pending[uid] = {
        "type": "admin_search"
    }

    bot.send_message(
        uid,
        "🔎 کد حساب، آیدی عددی، یوزرنیم یا نام کاربر را بفرست."
    )


def show_admin_user(admin, target):
    u = users[target]

    text = (
        "👤 <b>اطلاعات کاربر</b>\n\n"
        f"نام: {u['name']}\n"
        f"Username: @{u['username'] or '-'}\n"
        f"Telegram ID: <code>{u['id']}</code>\n"
        f"کد حساب: <code>{u['code']}</code>\n"
        f"تلفن: {u['phone'] or 'ثبت نشده'}\n"
        f"سکه: {u['coins']}\n"
        f"اعتبار: {u['balance']:,}\n"
        f"XP: {u['xp']}\n"
        f"Level: {u['level']}\n"
        f"رنک‌ها:\n{all_ranks_text(target)}\n\n"
        f"چت‌ها: {u['chats']}\n"
        f"پیام‌ها: {u['messages']}\n"
        f"دعوت‌ها: {u['referrals']}\n"
        f"هشدار: {u['warnings']}\n"
        f"مسدود: {'بله' if u['banned'] else 'خیر'}"
    )

    kb = types.InlineKeyboardMarkup(row_width=2)

    kb.add(
        types.InlineKeyboardButton(
            "🪙 +سکه",
            callback_data=f"target_coin_add:{target}"
        ),
        types.InlineKeyboardButton(
            "🪙 -سکه",
            callback_data=f"target_coin_sub:{target}"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "💰 +اعتبار",
            callback_data=f"target_balance_add:{target}"
        ),
        types.InlineKeyboardButton(
            "💰 -اعتبار",
            callback_data=f"target_balance_sub:{target}"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "⭐ +XP",
            callback_data=f"target_xp_add:{target}"
        ),
        types.InlineKeyboardButton(
            "🏆 رنک",
            callback_data=f"target_rank:{target}"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "🚫 بن",
            callback_data=f"target_ban:{target}"
        ),
        types.InlineKeyboardButton(
            "🔓 رفع بن",
            callback_data=f"target_unban:{target}"
        )
    )

    bot.send_message(
        admin,
        text,
        reply_markup=kb
    )


# ============================================================
# مدیریت گزارش‌ها
# ============================================================

def admin_reports(uid):
    if not reports:
        bot.send_message(uid, "🚨 گزارشی وجود ندارد.")
        return

    for r in reports[-20:]:
        text = (
            f"🚨 <b>گزارش #{r['id']}</b>\n\n"
            f"گزارش‌دهنده: <code>{r['reporter']}</code>\n"
            f"متهم: <code>{r['target']}</code>\n"
            f"دلیل: {r['reason'] or 'انتخاب نشده'}\n"
            f"نوع پیام: {r['content_type']}\n"
            f"وضعیت: {r['status']}\n"
            f"زمان: {r['time']}"
        )

        bot.send_message(uid, text)


# ============================================================
# مدیریت ناظران
# ============================================================

def admin_mods(uid):
    text = "🛡 <b>ناظران</b>\n\n"

    found = False

    for user_id, u in users.items():
        if is_moderator(user_id) and not is_admin(user_id):
            found = True

            text += (
                f"👤 {u['name']}\n"
                f"🆔 <code>{u['id']}</code>\n"
                f"کد: {u['code']}\n\n"
            )

    if not found:
        text += "ناظری وجود ندارد."

    bot.send_message(uid, text)


# ============================================================
# مدیریت هشدار
# ============================================================

def admin_warnings(uid):
    if not warnings:
        bot.send_message(uid, "⚠️ هشداری ثبت نشده.")
        return

    text = "⚠️ <b>هشدارها</b>\n\n"

    for w in warnings[-30:]:
        text += (
            f"کاربر: {w['target']}\n"
            f"دلیل: {w['reason']}\n"
            f"مدیر: {w['admin']}\n"
            f"زمان: {w['time']}\n\n"
        )

    bot.send_message(uid, text)


# ============================================================
# مدیریت سکه
# ============================================================

def admin_coins_start(uid):
    pending[uid] = {
        "type": "admin_coins"
    }

    bot.send_message(
        uid,
        "🪙 به این شکل بفرست:\n\n"
        "<code>کدکاربر مقدار</code>\n\n"
        "مثال:\n"
        "<code>0001 500</code>\n"
        "برای کم کردن:\n"
        "<code>0001 -500</code>"
    )


def admin_balance_start(uid):
    pending[uid] = {
        "type": "admin_balance"
    }

    bot.send_message(
        uid,
        "💰 کد کاربر و مقدار اعتبار را بفرست.\n\n"
        "مثال:\n"
        "<code>0001 500000</code>"
    )


def admin_xp_start(uid):
    pending[uid] = {
        "type": "admin_xp"
    }

    bot.send_message(
        uid,
        "⭐ کد کاربر و مقدار XP را بفرست.\n\n"
        "<code>0001 100</code>"
    )


# ============================================================
# بن مدیریت
# ============================================================

def admin_ban_start(uid):
    pending[uid] = {
        "type": "admin_ban"
    }

    bot.send_message(
        uid,
        "🚫 کد کاربر را بفرست."
    )


def admin_unban_start(uid):
    pending[uid] = {
        "type": "admin_unban"
    }

    bot.send_message(
        uid,
        "🔓 کد کاربر را بفرست."
    )


# ============================================================
# مدیریت اعتبار / XP
# ============================================================

def apply_coin_change(target, amount):
    old = users[target]["coins"]

    users[target]["coins"] = max(
        0,
        users[target]["coins"] + amount
    )
    db_sync_user(target)

    transaction(
        target,
        "coins",
        amount,
        "تغییر توسط مدیریت"
    )

    notify(
        target,
        "🪙 <b>تغییر موجودی سکه</b>\n\n"
        f"مقدار تغییر: {amount:+}\n"
        f"موجودی جدید: {users[target]['coins']}"
    )

    admin_log(
        "تغییر سکه",
        target,
        f"{old} -> {users[target]['coins']}"
    )


def apply_balance_change(target, amount):
    old = users[target]["balance"]

    users[target]["balance"] = max(
        0,
        users[target]["balance"] + amount
    )
    db_sync_user(target)

    transaction(
        target,
        "balance",
        amount,
        "تغییر توسط مدیریت"
    )

    notify(
        target,
        "💰 <b>اعتبار مجازی شما تغییر کرد</b>\n\n"
        f"تغییر: {amount:+,} تومان\n"
        f"موجودی جدید: {users[target]['balance']:,} تومان"
    )

    admin_log(
        "تغییر اعتبار",
        target,
        f"{old} -> {users[target]['balance']}"
    )


# ============================================================
# رنک مدیریت
# ============================================================

def admin_rank_start(uid):
    pending[uid] = {
        "type": "admin_rank"
    }

    bot.send_message(
        uid,
        "🏆 این فرمت را بفرست:\n\n"
        "<code>0001 gold</code>\n\n"
        "رنک‌ها:\n"
        "silver\n"
        "gold\n"
        "diamond\n"
        "vip\n"
        "moderator"
    )


def give_rank_admin(target, rank):
    if rank not in RANKS:
        return False

    if rank == "moderator":
        expires = None
    else:
        expires = now() + timedelta(days=30)

    users[target]["ranks"].append({
        "rank": rank,
        "expires": expires
    })
    db_save_rank_assignment(target, rank, expires)
    db_sync_user(target)

    notify(
        target,
        f"🏆 <b>رنک جدید دریافت کردی</b>\n\n"
        f"{RANKS[rank]['name']}"
    )

    admin_log(
        "اعطای رنک",
        target,
        rank
    )

    return True


# ============================================================
# قرعه‌کشی
# ============================================================

def giveaway_menu(uid):
    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "🎁 قرعه‌کشی‌های فعال",
            callback_data="giveaways_active"
        )
    )

    bot.send_message(
        uid,
        "🎁 <b>قرعه‌کشی</b>",
        reply_markup=kb
    )


def create_giveaway_start(uid):
    pending[uid] = {
        "type": "giveaway_title",
        "data": {}
    }

    bot.send_message(
        uid,
        "🎁 عنوان قرعه‌کشی را بفرست."
    )


def show_giveaways(uid):
    active = [
        x for x in giveaways.values()
        if x["status"] == "active"
    ]

    if not active:
        bot.send_message(
            uid,
            "فعلاً قرعه‌کشی فعالی وجود ندارد."
        )
        return

    for g in active:
        kb = types.InlineKeyboardMarkup()

        kb.add(
            types.InlineKeyboardButton(
                "🎟 شرکت می‌کنم",
                callback_data=f"join_giveaway:{g['id']}"
            )
        )

        bot.send_message(
            uid,
            f"🎁 <b>{g['title']}</b>\n\n"
            f"{g['description']}\n\n"
            f"🏆 جایزه: {g['prize']}\n"
            f"👥 برنده‌ها: {g['winners']}\n"
            f"⏳ پایان: {g['end']}",
            reply_markup=kb
        )


# ============================================================
# چالش‌ها
# ============================================================

def challenge_menu(uid):
    active = [
        x for x in challenges.values()
        if x["status"] == "active"
    ]

    if not active:
        bot.send_message(
            uid,
            "🏆 چالش فعالی وجود ندارد."
        )
        return

    for c in active:
        bot.send_message(
            uid,
            f"🏆 <b>{c['title']}</b>\n\n"
            f"{c['description']}\n\n"
            f"🎯 نوع: {c['type']}\n"
            f"🎁 جایزه: {c['prize']} سکه\n"
            f"⏳ پایان: {c['end']}"
        )


def create_challenge_start(uid):
    pending[uid] = {
        "type": "challenge_title",
        "data": {}
    }

    bot.send_message(
        uid,
        "🏆 عنوان چالش را بفرست."
    )


# ============================================================
# نظر ادمین
# ============================================================

def admin_reviews(uid):
    if not reviews:
        bot.send_message(uid, "💬 نظری ثبت نشده.")
        return

    for r in reviews[-30:]:
        bot.send_message(
            uid,
            "💬 <b>نظر</b>\n\n"
            f"کاربر: {r['uid']}\n"
            f"{r['text']}\n"
            f"زمان: {r['time']}"
        )


def admin_suggestions(uid):
    if not suggestions:
        bot.send_message(uid, "💡 پیشنهادی ثبت نشده.")
        return

    for s in suggestions[-30:]:
        bot.send_message(
            uid,
            "💡 <b>پیشنهاد</b>\n\n"
            f"کاربر: {s['uid']}\n"
            f"{s['text']}\n"
            f"زمان: {s['time']}"
        )


# ============================================================
# پیام همگانی
# ============================================================

def broadcast_start(uid):
    pending[uid] = {
        "type": "broadcast"
    }

    bot.send_message(
        uid,
        "📢 متن پیام همگانی را بفرست."
    )


def broadcast(text):
    count = 0

    for uid in list(users.keys()):
        try:
            bot.send_message(uid, text)
            count += 1
        except Exception:
            pass

    return count


# ============================================================
# آمار
# ============================================================

def admin_stats(uid):
    total_coins = sum(
        u["coins"] for u in users.values()
    )

    total_balance = sum(
        u["balance"] for u in users.values()
    )

    total_messages = sum(
        u["messages"] for u in users.values()
    )

    bot.send_message(
        uid,
        "📈 <b>آمار کامل</b>\n\n"
        f"👥 کاربران: {len(users)}\n"
        f"💬 پیام‌ها: {total_messages}\n"
        f"💬 چت فعال: {len(chats)//2}\n"
        f"🪙 کل سکه کاربران: {total_coins}\n"
        f"💰 کل اعتبار مجازی: {total_balance:,}\n"
        f"🚨 گزارش‌ها: {len(reports)}\n"
        f"🎁 قرعه‌کشی‌ها: {len(giveaways)}\n"
        f"🏆 چالش‌ها: {len(challenges)}"
    )


# ============================================================
# چت‌های فعال
# ============================================================

def admin_chats(uid):
    if not chats:
        bot.send_message(
            uid,
            "💬 چت فعالی وجود ندارد."
        )
        return

    text = "💬 <b>چت‌های فعال</b>\n\n"

    seen = set()

    for user_id, data in chats.items():
        partner = data["partner"]

        key = tuple(sorted([user_id, partner]))

        if key in seen:
            continue

        seen.add(key)

        text += (
            f"👤 {user_id} ↔ {partner}\n"
            f"🆔 {data['chat_id']}\n\n"
        )

    bot.send_message(uid, text)


# ============================================================
# پیام‌ها
# ============================================================

def admin_messages(uid):
    if not messages_log:
        bot.send_message(
            uid,
            "🔍 پیامی ثبت نشده."
        )
        return

    for m in messages_log[-30:]:
        bot.send_message(
            uid,
            f"💬 {m['from']} → {m['to']}\n"
            f"نوع: {m['type']}\n"
            f"متن: {m['text'][:500]}\n"
            f"زمان: {m['time']}"
        )


# ============================================================
# لاگ
# ============================================================

def admin_logs_page(uid):
    if not admin_logs:
        bot.send_message(
            uid,
            "📋 لاگی وجود ندارد."
        )
        return

    for log in admin_logs[-30:]:
        bot.send_message(
            uid,
            f"📋 <b>{log['action']}</b>\n\n"
            f"هدف: {log['target']}\n"
            f"جزئیات: {log['details']}\n"
            f"زمان: {log['time']}"
        )


# ============================================================
# ناظر
# ============================================================

def moderator_ban(uid):
    if not is_moderator(uid):
        return

    pending[uid] = {
        "type": "mod_ban"
    }

    bot.send_message(
        uid,
        "🛡 کد کاربر و مدت دقیقه را بفرست.\n\n"
        "مثال:\n"
        "<code>0001 60</code>"
    )


def moderator_warn(uid):
    if not is_moderator(uid):
        return

    pending[uid] = {
        "type": "mod_warn"
    }

    bot.send_message(
        uid,
        "🛡 کد کاربر و دلیل هشدار را بفرست.\n\n"
        "مثال:\n"
        "<code>0001 توهین</code>"
    )


# ============================================================
# هندلر callback
# ============================================================

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    uid = call.from_user.id

    if uid not in users:
        bot.answer_callback_query(
            call.id,
            "اول /start را بزن."
        )
        return

    data = call.data

    # --------------------------
    # عمومی
    # --------------------------

    if data == "daily":
        daily(uid)

    elif data == "rank_shop":
        rank_shop(uid)

    elif data == "referral":
        referral_page(uid)

    elif data == "profile_photo":
        pending[uid] = {
            "type": "profile_photo"
        }

        bot.send_message(
            uid,
            "🖼 عکس موردنظر را بفرست."
        )

    elif data == "profile_anon":
        users[uid]["anonymous"] = True

        bot.answer_callback_query(
            call.id,
            "حالت ناشناس فعال شد."
        )

        bot.send_message(
            uid,
            "🕵️ حالت ناشناس فعال شد."
        )

    elif data == "profile_normal":
        users[uid]["anonymous"] = False

        bot.answer_callback_query(
            call.id,
            "حالت عادی فعال شد."
        )

        bot.send_message(
            uid,
            "👁 حالت عادی فعال شد."
        )

    elif data.startswith("buy_rank:"):
        rank = data.split(":", 1)[1]
        buy_rank(uid, rank)

    elif data == "game_coin":
        coin_game(uid)

    elif data == "game_guess":
        guess_game(uid)

    elif data == "giveaways_active":
        show_giveaways(uid)

    elif data.startswith("join_giveaway:"):
        gid = int(data.split(":")[1])

        if gid not in giveaways:
            bot.answer_callback_query(
                call.id,
                "وجود ندارد."
            )
            return

        g = giveaways[gid]

        if uid not in g["entries"]:
            g["entries"].append(uid)

            bot.answer_callback_query(
                call.id,
                "ثبت شد!"
            )

            bot.send_message(
                uid,
                "🎟 در قرعه‌کشی ثبت شدی!"
            )
        else:
            bot.answer_callback_query(
                call.id,
                "قبلاً ثبت شده‌ای."
            )

    elif data.startswith("rate:"):
        parts = data.split(":")

        target = int(parts[1])
        chat_id = parts[2]
        score = int(parts[3])

        ratings.append({
            "from": uid,
            "to": target,
            "score": score,
            "chat": chat_id,
            "time": now()
        })

        add_xp(uid, 5)

        bot.answer_callback_query(
            call.id,
            "امتیاز ثبت شد ❤️"
        )

        bot.edit_message_text(
            "⭐ امتیاز شما ثبت شد.",
            uid,
            call.message.message_id
        )

    # --------------------------
    # گزارش
    # --------------------------

    elif data.startswith("report_reason:"):
        reason = data.split(":", 1)[1]

        p = pending.get(uid)

        if not p:
            return

        report_id = p["report_id"]

        for r in reports:
            if r["id"] == report_id:
                r["reason"] = reason
                r["status"] = "new"
                break

        pending.pop(uid, None)

        bot.send_message(
            uid,
            "🚨 گزارش با موفقیت ثبت شد."
        )

        notify(
            ADMIN_ID,
            f"🚨 <b>گزارش جدید</b>\n\n"
            f"شماره گزارش: #{report_id}\n"
            f"گزارش‌دهنده: {uid}\n"
            f"دلیل: {reason}"
        )

    # --------------------------
    # مدیریت
    # --------------------------

    elif data.startswith("target_coin_add:"):
        if not is_admin(uid):
            return

        target = int(data.split(":")[1])

        pending[uid] = {
            "type": "quick_coin",
            "target": target,
            "sign": 1
        }

        bot.send_message(
            uid,
            "مقدار سکه را بفرست."
        )

    elif data.startswith("target_coin_sub:"):
        if not is_admin(uid):
            return

        target = int(data.split(":")[1])

        pending[uid] = {
            "type": "quick_coin",
            "target": target,
            "sign": -1
        }

        bot.send_message(
            uid,
            "مقدار سکه را بفرست."
        )

    elif data.startswith("target_balance_add:"):
        if not is_admin(uid):
            return

        target = int(data.split(":")[1])

        pending[uid] = {
            "type": "quick_balance",
            "target": target,
            "sign": 1
        }

        bot.send_message(
            uid,
            "مقدار اعتبار را بفرست."
        )

    elif data.startswith("target_balance_sub:"):
        if not is_admin(uid):
            return

        target = int(data.split(":")[1])

        pending[uid] = {
            "type": "quick_balance",
            "target": target,
            "sign": -1
        }

        bot.send_message(
            uid,
            "مقدار اعتبار را بفرست."
        )

    elif data.startswith("target_xp_add:"):
        if not is_admin(uid):
            return

        target = int(data.split(":")[1])

        pending[uid] = {
            "type": "quick_xp",
            "target": target
        }

        bot.send_message(
            uid,
            "مقدار XP را بفرست."
        )

    elif data.startswith("target_rank:"):
        if not is_admin(uid):
            return

        target = int(data.split(":")[1])

        pending[uid] = {
            "type": "quick_rank",
            "target": target
        }

        bot.send_message(
            uid,
            "رنک را بفرست:\n"
            "silver / gold / diamond / vip / moderator"
        )

    elif data.startswith("target_ban:"):
        if not is_admin(uid):
            return

        target = int(data.split(":")[1])

        if target in users:
            users[target]["banned"] = True

            notify(
                target,
                "🚫 حساب شما توسط مدیریت مسدود شد."
            )

            admin_log(
                "بن دائمی",
                target
            )

            bot.send_message(
                uid,
                "🚫 کاربر مسدود شد."
            )

    elif data.startswith("target_unban:"):
        if not is_admin(uid):
            return

        target = int(data.split(":")[1])

        if target in users:
            users[target]["banned"] = False

            notify(
                target,
                "🔓 حساب شما از مسدودی خارج شد."
            )

            admin_log(
                "رفع بن",
                target
            )

            bot.send_message(
                uid,
                "🔓 رفع مسدودی شد."
            )

    # --------------------------
    # پنل مدیریت
    # --------------------------

    elif data == "admin_dashboard":
        if is_admin(uid):
            admin_dashboard(uid)

    elif data == "admin_users":
        if is_admin(uid):
            admin_users(uid)

    elif data == "admin_search":
        if is_admin(uid):
            admin_search_start(uid)

    elif data == "admin_reports":
        if is_admin(uid):
            admin_reports(uid)

    elif data == "admin_mods":
        if is_admin(uid):
            admin_mods(uid)

    elif data == "admin_warnings":
        if is_admin(uid):
            admin_warnings(uid)

    elif data == "admin_coins":
        if is_admin(uid):
            admin_coins_start(uid)

    elif data == "admin_balance":
        if is_admin(uid):
            admin_balance_start(uid)

    elif data == "admin_xp":
        if is_admin(uid):
            admin_xp_start(uid)

    elif data == "admin_rank":
        if is_admin(uid):
            admin_rank_start(uid)

    elif data == "admin_giveaway":
        if is_admin(uid):
            create_giveaway_start(uid)

    elif data == "admin_challenge":
        if is_admin(uid):
            create_challenge_start(uid)

    elif data == "admin_broadcast":
        if is_admin(uid):
            broadcast_start(uid)

    elif data == "admin_reviews":
        if is_admin(uid):
            admin_reviews(uid)

    elif data == "admin_suggestions":
        if is_admin(uid):
            admin_suggestions(uid)

    elif data == "admin_stats":
        if is_admin(uid):
            admin_stats(uid)

    elif data == "admin_logs":
        if is_admin(uid):
            admin_logs_page(uid)

    elif data == "admin_chats":
        if is_admin(uid):
            admin_chats(uid)

    elif data == "admin_messages":
        if is_admin(uid):
            admin_messages(uid)

    elif data == "admin_ban":
        if is_admin(uid):
            admin_ban_start(uid)

    elif data == "admin_unban":
        if is_admin(uid):
            admin_unban_start(uid)

    elif data == "admin_tempban":
        if is_admin(uid):
            pending[uid] = {"type": "admin_tempban"}

            bot.send_message(
                uid,
                "کد کاربر، مدت دقیقه و دلیل:\n\n"
                "<code>0001 60 اسپم</code>"
            )

    elif data == "admin_rewards":
        bot.send_message(
            uid,
            "🎟 مدیریت جوایز آماده است."
        )

    elif data == "admin_games":
        bot.send_message(
            uid,
            "🎮 مدیریت بازی‌ها آماده است."
        )

    elif data == "admin_missions":
        bot.send_message(
            uid,
            "🎯 مدیریت مأموریت‌ها آماده است."
        )

    elif data == "admin_rank_settings":
        bot.send_message(
            uid,
            "🏅 تنظیمات رنک‌ها در بخش RANKS بالای کد قرار دارد."
        )

    elif data == "admin_cleanup":
        bot.send_message(
            uid,
            "🧹 برای پاکسازی از دستورات مدیریتی استفاده کن."
        )

    elif data == "admin_settings":
        bot.send_message(
            uid,
            "⚙️ تنظیمات اصلی بات در ابتدای فایل قرار دارد."
        )

    elif data == "admin_security":
        bot.send_message(
            uid,
            "🔐 <b>امنیت</b>\n\n"
            "✅ توکن بات از GitHub Secret خوانده می‌شود.\n"
            "✅ کلید Supabase از GitHub Secret خوانده می‌شود.\n"
            "✅ اطلاعات اصلی کاربران در Supabase ذخیره می‌شود."
        )

    elif data == "admin_export":
        text = "uid,code,name,coins,balance,xp,level\n"

        for u in users.values():
            text += (
                f"{u['id']},"
                f"{u['code']},"
                f"{u['name']},"
                f"{u['coins']},"
                f"{u['balance']},"
                f"{u['xp']},"
                f"{u['level']}\n"
            )

        bot.send_document(
            uid,
            ("users.csv", text.encode("utf-8"))
        )

    # --------------------------
    # ناظر
    # --------------------------

    elif data == "mod_chats":
        if is_moderator(uid):
            admin_chats(uid)

    elif data == "mod_ban":
        if is_moderator(uid):
            moderator_ban(uid)

    elif data == "mod_warn":
        if is_moderator(uid):
            moderator_warn(uid)

    elif data == "mod_reports":
        if is_moderator(uid):
            admin_reports(uid)

    elif data == "new_review":
        pending[uid] = {
            "type": "review"
        }

        bot.send_message(
            uid,
            "⭐ نظر خودت را بفرست."
        )

    elif data == "new_suggestion":
        pending[uid] = {
            "type": "suggestion"
        }

        bot.send_message(
            uid,
            "💡 پیشنهادت را بفرست."
        )

    bot.answer_callback_query(call.id)


# ============================================================
# دریافت عکس پروفایل
# ============================================================

@bot.message_handler(content_types=["photo"])
def photo_handler(message):
    uid = message.from_user.id

    if uid not in users:
        ensure_user(message)

    touch(uid)

    p = pending.get(uid)

    # عکس پروفایل
    if p and p.get("type") == "profile_photo":
        file_id = message.photo[-1].file_id

        users[uid]["photo"] = file_id

        pending.pop(uid, None)

        bot.send_message(
            uid,
            "🖼 عکس پروفایل ذخیره شد."
        )
        return

    # گزارش
    if p and p.get("type") == "report_message":
        finish_report_message(message)
        return

    # چت
    if uid in chats:
        partner = chats[uid]["partner"]

        bot.send_photo(
            partner,
            message.photo[-1].file_id,
            caption=(
                "🕵️ پیام تصویری از مخاطب\n\n"
                f"🏅 {visible_rank(uid)}"
            )
        )

        users[uid]["messages"] += 1

        messages_log.append({
            "from": uid,
            "to": partner,
            "type": "photo",
            "text": message.caption or "",
            "time": now()
        })

        return


# ============================================================
# فایل / ویدیو / صدا
# ============================================================

@bot.message_handler(
    content_types=[
        "video",
        "document",
        "voice",
        "audio",
        "animation"
    ]
)
def media_handler(message):
    uid = message.from_user.id

    if uid not in users:
        ensure_user(message)

    touch(uid)

    p = pending.get(uid)

    if p and p.get("type") == "report_message":
        finish_report_message(message)
        return

    if uid not in chats:
        bot.send_message(
            uid,
            "برای ارسال این نوع پیام باید داخل چت باشید."
        )
        return

    partner = chats[uid]["partner"]

    try:
        if message.content_type == "video":
            bot.send_video(
                partner,
                message.video.file_id,
                caption=message.caption or ""
            )

        elif message.content_type == "document":
            bot.send_document(
                partner,
                message.document.file_id,
                caption=message.caption or ""
            )

        elif message.content_type == "voice":
            bot.send_voice(
                partner,
                message.voice.file_id
            )

        elif message.content_type == "audio":
            bot.send_audio(
                partner,
                message.audio.file_id
            )

        elif message.content_type == "animation":
            bot.send_animation(
                partner,
                message.animation.file_id
            )

        users[uid]["messages"] += 1

        messages_log.append({
            "from": uid,
            "to": partner,
            "type": message.content_type,
            "text": message.caption or "",
            "time": now()
        })

    except Exception:
        bot.send_message(
            uid,
            "❌ ارسال پیام انجام نشد."
        )


# ============================================================
# پیام‌های متنی
# ============================================================

@bot.message_handler(content_types=["text"])
def text_handler(message):
    uid = message.from_user.id
    text = message.text.strip()

    if uid not in users:
        ensure_user(message)

    touch(uid)

    # --------------------------
    # بن
    # --------------------------

    if is_banned(uid):
        bot.send_message(
            uid,
            "🚫 حساب شما مسدود است."
        )
        return

    # --------------------------
    # دستورات
    # --------------------------

    if text == "/end":
        end_chat(uid)
        return

    if text == "/cancel":
        if uid in waiting_users:
            waiting_users.remove(uid)

            bot.send_message(
                uid,
                "❌ از صف خارج شدی."
            )
        else:
            bot.send_message(
                uid,
                "شما در صف نیستی."
            )
        return

    if text == "/block":
        block_user(uid)
        return

    if text == "/report":
        start_report(uid)
        return

    if text == "/daily":
        daily(uid)
        return

    if text == "/profile":
        send_profile(uid)
        return

    if text == "/shop":
        rank_shop(uid)
        return

    if text == "/chat":
        start_chat(uid)
        return

    if text == "/help":
        bot.send_message(
            uid,
            "❓ <b>راهنما</b>\n\n"
            "/start\n"
            "/chat\n"
            "/end\n"
            "/cancel\n"
            "/profile\n"
            "/shop\n"
            "/daily\n"
            "/report\n"
            "/block\n"
            "/help\n"
            "/privacy"
        )
        return

    if text == "/privacy":
        bot.send_message(
            uid,
            "🔐 <b>حریم خصوصی</b>\n\n"
            "بات اطلاعاتی را که برای عملکرد سرویس لازم است "
            "ذخیره می‌کند.\n\n"
            "شماره تلفن فقط در صورتی در اختیار بات قرار می‌گیرد "
            "که خود کاربر آن را ارسال کند."
        )
        return

    # --------------------------
    # منو
    # --------------------------

    if text == "💬 چت":
        start_chat(uid)
        return

    if text == "👤 پروفایل":
        send_profile(uid)
        return

    if text == "🪙 سکه":
        coins_page(uid)
        return

    if text == "⭐ رنک‌ها":
        rank_shop(uid)
        return

    if text == "🎮 بازی":
        game_menu(uid)
        return

    if text == "🎯 مأموریت‌ها":
        mission_page(uid)
        return

    if text == "🎁 جوایز":
        giveaway_menu(uid)
        return

    if text == "🏆 چالش‌ها":
        challenge_menu(uid)
        return

    if text == "👥 دعوت دوستان":
        referral_page(uid)
        return

    if text == "⚙️ تنظیمات":
        settings_page(uid)
        return

    if text == "❓ راهنما":
        bot.send_message(
            uid,
            "❓ <b>راهنما</b>\n\n"
            "💬 چت: ورود به صف چت ناشناس\n"
            "👤 پروفایل: مشاهده حساب\n"
            "🪙 سکه: موجودی و جایزه\n"
            "⭐ رنک‌ها: خرید رنک\n"
            "🎮 بازی: بازی و دریافت جایزه\n"
            "🚨 گزارش: گزارش مخاطب\n"
            "🚫 بلاک: مسدود کردن مخاطب"
        )
        return

    if text == "📝 نظر و پیشنهاد":
        review_page(uid)
        return

    if text == "🛠 پنل مدیریت":
        if is_admin(uid):
            admin_panel(uid)
        return

    if text == "🛡 پنل ناظر":
        if is_moderator(uid):
            bot.send_message(
                uid,
                "🛡 <b>پنل ناظر</b>",
                reply_markup=moderator_menu()
            )
        return

    # --------------------------
    # حالت‌های در انتظار
    # --------------------------

    p = pending.get(uid)

    if p:
        ptype = p.get("type")

        # عکس
        if ptype == "profile_photo":
            bot.send_message(
                uid,
                "🖼 لطفاً یک عکس ارسال کن."
            )
            return

        # گزارش
        if ptype == "report_message":
            finish_report_message(message)
            return

        # review
        if ptype == "review":
            reviews.append({
                "uid": uid,
                "text": text,
                "time": now()
            })

            pending.pop(uid, None)

            bot.send_message(
                uid,
                "⭐ ممنون! نظر شما ثبت شد."
            )

            notify(
                ADMIN_ID,
                "⭐ <b>نظر جدید</b>\n\n"
                f"کاربر: {uid}\n"
                f"{text}"
            )

            return

        # suggestion
        if ptype == "suggestion":
            suggestions.append({
                "uid": uid,
                "text": text,
                "time": now()
            })

            pending.pop(uid, None)

            bot.send_message(
                uid,
                "💡 پیشنهاد شما ثبت شد."
            )

            notify(
                ADMIN_ID,
                "💡 <b>پیشنهاد جدید</b>\n\n"
                f"کاربر: {uid}\n"
                f"{text}"
            )

            return

        # حدس عدد
        if ptype == "guess":
            try:
                guess = int(text)

                if guess < 1 or guess > 5:
                    raise ValueError

                number = p["number"]

                pending.pop(uid, None)

                users[uid]["game_plays"] += 1

                if guess == number:
                    reward = 100

                    users[uid]["coins"] += reward
                    users[uid]["game_wins"] += 1

                    add_xp(uid, 20)

                    bot.send_message(
                        uid,
                        "🎉 درست حدس زدی!\n\n"
                        f"🪙 +{reward} سکه"
                    )
                else:
                    bot.send_message(
                        uid,
                        f"❌ اشتباه!\n"
                        f"عدد درست: {number}"
                    )

            except Exception:
                bot.send_message(
                    uid,
                    "فقط یک عدد بین ۱ تا ۵ بفرست."
                )

            return

        # جستجوی ادمین
        if ptype == "admin_search":
            if not is_admin(uid):
                pending.pop(uid, None)
                return

            target = find_user(text)

            pending.pop(uid, None)

            if not target:
                bot.send_message(
                    uid,
                    "❌ کاربر پیدا نشد."
                )
                return

            show_admin_user(uid, target)
            return

        # مدیریت سکه
        if ptype == "admin_coins":
            if not is_admin(uid):
                pending.pop(uid, None)
                return

            parts = text.split()

            if len(parts) != 2:
                bot.send_message(
                    uid,
                    "فرمت اشتباه است."
                )
                return

            target = find_user(parts[0])

            if not target:
                bot.send_message(
                    uid,
                    "کاربر پیدا نشد."
                )
                return

            try:
                amount = int(parts[1])
            except:
                bot.send_message(
                    uid,
                    "مقدار باید عدد باشد."
                )
                return

            apply_coin_change(target, amount)

            pending.pop(uid, None)

            bot.send_message(
                uid,
                "✅ انجام شد."
            )
            return

        # مدیریت اعتبار
        if ptype == "admin_balance":
            if not is_admin(uid):
                pending.pop(uid, None)
                return

            parts = text.split()

            if len(parts) != 2:
                return

            target = find_user(parts[0])

            if not target:
                bot.send_message(
                    uid,
                    "کاربر پیدا نشد."
                )
                return

            try:
                amount = int(parts[1])
            except:
                return

            apply_balance_change(target, amount)

            pending.pop(uid, None)

            bot.send_message(
                uid,
                "✅ انجام شد."
            )
            return

        # مدیریت XP
        if ptype == "admin_xp":
            if not is_admin(uid):
                pending.pop(uid, None)
                return

            parts = text.split()

            if len(parts) != 2:
                return

            target = find_user(parts[0])

            if not target:
                return

            try:
                amount = int(parts[1])
            except:
                return

            add_xp(target, amount)

            notify(
                target,
                f"⭐ <b>XP شما افزایش یافت</b>\n\n"
                f"+{amount} XP"
            )

            admin_log(
                "افزایش XP",
                target,
                str(amount)
            )

            pending.pop(uid, None)

            bot.send_message(
                uid,
                "✅ XP اضافه شد."
            )
            return

        # مدیریت رنک
        if ptype == "admin_rank":
            if not is_admin(uid):
                pending.pop(uid, None)
                return

            parts = text.split()

            if len(parts) != 2:
                bot.send_message(
                    uid,
                    "مثال: 0001 gold"
                )
                return

            target = find_user(parts[0])
            rank = parts[1].lower()

            if not target or rank not in RANKS:
                bot.send_message(
                    uid,
                    "اطلاعات اشتباه است."
                )
                return

            give_rank_admin(target, rank)

            pending.pop(uid, None)

            bot.send_message(
                uid,
                "🏆 رنک داده شد."
            )
            return

        # بن
        if ptype == "admin_ban":
            if not is_admin(uid):
                pending.pop(uid, None)
                return

            target = find_user(text)

            if not target:
                bot.send_message(
                    uid,
                    "کاربر پیدا نشد."
                )
                return

            users[target]["banned"] = True

            notify(
                target,
                "🚫 حساب شما توسط مدیریت مسدود شد."
            )

            admin_log(
                "بن دائمی",
                target
            )

            pending.pop(uid, None)

            bot.send_message(
                uid,
                "🚫 کاربر بن شد."
            )
            return

        # رفع بن
        if ptype == "admin_unban":
            if not is_admin(uid):
                pending.pop(uid, None)
                return

            target = find_user(text)

            if not target:
                bot.send_message(
                    uid,
                    "کاربر پیدا نشد."
                )
                return

            users[target]["banned"] = False

            notify(
                target,
                "🔓 حساب شما از مسدودی خارج شد."
            )

            admin_log(
                "رفع بن",
                target
            )

            pending.pop(uid, None)

            bot.send_message(
                uid,
                "🔓 انجام شد."
            )
            return

        # بن موقت
        if ptype == "admin_tempban":
            if not is_admin(uid):
                pending.pop(uid, None)
                return

            parts = text.split(maxsplit=2)

            if len(parts) < 2:
                return

            target = find_user(parts[0])

            try:
                minutes = int(parts[1])
            except:
                return

            reason = parts[2] if len(parts) >= 3 else "بدون دلیل"

            if not target:
                return

            temp_bans[target] = {
                "until": now() + timedelta(minutes=minutes),
                "reason": reason
            }

            notify(
                target,
                "⏱ <b>مسدودی موقت</b>\n\n"
                f"مدت: {minutes} دقیقه\n"
                f"دلیل: {reason}"
            )

            admin_log(
                "بن موقت",
                target,
                f"{minutes} دقیقه - {reason}"
            )

            pending.pop(uid, None)

            bot.send_message(
                uid,
                "⏱ بن موقت انجام شد."
            )
            return

        # پیام همگانی
        if ptype == "broadcast":
            if not is_admin(uid):
                pending.pop(uid, None)
                return

            count = broadcast(text)

            pending.pop(uid, None)

            bot.send_message(
                uid,
                f"📢 پیام برای {count} نفر ارسال شد."
            )
            return

        # تغییر سریع سکه
        if ptype == "quick_coin":
            if not is_admin(uid):
                return

            try:
                amount = int(text)
            except:
                return

            amount *= p["sign"]

            apply_coin_change(
                p["target"],
                amount
            )

            pending.pop(uid, None)

            bot.send_message(
                uid,
                "✅ انجام شد."
            )
            return

        # تغییر سریع اعتبار
        if ptype == "quick_balance":
            if not is_admin(uid):
                return

            try:
                amount = int(text)
            except:
                return

            amount *= p["sign"]

            apply_balance_change(
                p["target"],
                amount
            )

            pending.pop(uid, None)

            bot.send_message(
                uid,
                "✅ انجام شد."
            )
            return

        # XP سریع
        if ptype == "quick_xp":
            if not is_admin(uid):
                return

            try:
                amount = int(text)
            except:
                return

            add_xp(
                p["target"],
                amount
            )

            notify(
                p["target"],
                f"⭐ +{amount} XP"
            )

            admin_log(
                "افزایش سریع XP",
                p["target"],
                str(amount)
            )

            pending.pop(uid, None)

            bot.send_message(
                uid,
                "✅ انجام شد."
            )
            return

        # رنک سریع
        if ptype == "quick_rank":
            if not is_admin(uid):
                return

            rank = text.lower()

            if rank not in RANKS:
                bot.send_message(
                    uid,
                    "رنک اشتباه است."
                )
                return

            give_rank_admin(
                p["target"],
                rank
            )

            pending.pop(uid, None)

            bot.send_message(
                uid,
                "🏆 رنک داده شد."
            )
            return

        # ناظر بن
        if ptype == "mod_ban":
            if not is_moderator(uid):
                return

            parts = text.split(maxsplit=1)

            if len(parts) < 2:
                bot.send_message(
                    uid,
                    "مثال: 0001 60"
                )
                return

            target = find_user(parts[0])

            try:
                minutes = int(parts[1])
            except:
                return

            if not target:
                return

            temp_bans[target] = {
                "until": now() + timedelta(minutes=minutes),
                "reason": "اقدام ناظر"
            }

            notify(
                target,
                f"🛡 شما {minutes} دقیقه توسط ناظر مسدود شدید."
            )

            admin_log(
                "بن توسط ناظر",
                target,
                f"{minutes} دقیقه - ناظر {uid}"
            )

            pending.pop(uid, None)

            bot.send_message(
                uid,
                "🛡 انجام شد."
            )
            return

        # ناظر هشدار
        if ptype == "mod_warn":
            if not is_moderator(uid):
                return

            parts = text.split(maxsplit=1)

            if len(parts) < 2:
                return

            target = find_user(parts[0])
            reason = parts[1]

            if not target:
                return

            users[target]["warnings"] += 1

            warnings.append({
                "target": target,
                "admin": uid,
                "reason": reason,
                "time": now()
            })

            notify(
                target,
                f"⚠️ <b>هشدار</b>\n\n"
                f"دلیل: {reason}\n"
                f"تعداد هشدار: {users[target]['warnings']}"
            )

            pending.pop(uid, None)

            bot.send_message(
                uid,
                "⚠️ هشدار ثبت شد."
            )
            return

    # --------------------------
    # پیام در چت
    # --------------------------

    if uid in chats:
        partner = chats[uid]["partner"]

        # بررسی بلاک
        if uid in blocks and partner in blocks[uid]:
            bot.send_message(
                uid,
                "🚫 این کاربر مسدود شده."
            )
            return

        sender = users[uid]

        if sender["anonymous"]:
            prefix = "🕵️ مخاطب"
        else:
            prefix = display_name(uid)

        rank = visible_rank(uid)

        output = (
            f"<b>{prefix}</b> "
            f"({rank}) گفت:\n"
            f"{text}"
        )

        try:
            bot.send_message(
                partner,
                output
            )

            sender["messages"] += 1

            messages_log.append({
                "from": uid,
                "to": partner,
                "type": "text",
                "text": text,
                "time": now()
            })

            add_xp(uid, 1)

        except Exception:
            bot.send_message(
                uid,
                "❌ ارسال پیام انجام نشد."
            )

        return

    # --------------------------
    # متن ناشناخته
    # --------------------------

    bot.send_message(
        uid,
        "از منوی بات استفاده کن 👇",
        reply_markup=main_menu(uid)
    )


# ============================================================
# دریافت شماره تلفن
# ============================================================

@bot.message_handler(content_types=["contact"])
def contact_handler(message):
    uid = message.from_user.id

    if uid not in users:
        ensure_user(message)

    if message.contact.user_id == uid:
        users[uid]["phone"] = message.contact.phone_number

        bot.send_message(
            uid,
            "📱 شماره تلفن شما ذخیره شد."
        )


# ============================================================
# کارگر قرعه‌کشی و چالش
# ============================================================

def background_worker():
    while True:
        try:
            current = now()

            # قرعه‌کشی
            for gid, g in list(giveaways.items()):

                if g["status"] != "active":
                    continue

                if current >= g["end"]:
                    g["status"] = "finished"

                    entries = list(g["entries"])

                    if g.get("online_only"):
                        entries = [
                            x for x in entries
                            if x in user_last_activity
                            and
                            current - user_last_activity[x]
                            <= timedelta(minutes=ONLINE_MINUTES)
                        ]

                    if not entries:
                        notify(
                            ADMIN_ID,
                            f"🎁 قرعه‌کشی #{gid} تمام شد ولی برنده‌ای پیدا نشد."
                        )
                        continue

                    random.shuffle(entries)

                    winners = entries[:g["winners"]]

                    for winner in winners:

                        # اگر جایزه عددی باشد به عنوان سکه
                        nums = re.findall(
                            r"\d+",
                            str(g["prize"])
                        )

                        if nums and "سکه" in str(g["prize"]):
                            amount = int(nums[0])

                            users[winner]["coins"] += amount

                            notify(
                                winner,
                                f"🎉 <b>برنده قرعه‌کشی شدی!</b>\n\n"
                                f"🎁 {g['title']}\n"
                                f"🪙 +{amount} سکه"
                            )

                        else:
                            notify(
                                winner,
                                f"🎉 <b>برنده قرعه‌کشی شدی!</b>\n\n"
                                f"🎁 {g['title']}\n"
                                f"جایزه: {g['prize']}"
                            )

                        users[winner]["wins"] += 1

                    notify(
                        ADMIN_ID,
                        f"🎉 قرعه‌کشی #{gid} تمام شد.\n"
                        f"برنده‌ها: {winners}"
                    )

            # چالش
            for cid, c in list(challenges.items()):

                if c["status"] != "active":
                    continue

                if current >= c["end"]:
                    c["status"] = "finished"

                    ranking = []

                    for uid, u in users.items():

                        value = 0

                        if c["type"] == "messages":
                            value = u["messages"] - c["baseline"].get(uid, 0)

                        elif c["type"] == "chats":
                            value = u["chats"] - c["baseline"].get(uid, 0)

                        elif c["type"] == "xp":
                            value = u["xp"] - c["baseline"].get(uid, 0)

                        elif c["type"] == "coins":
                            value = u["coins"] - c["baseline"].get(uid, 0)

                        elif c["type"] == "referrals":
                            value = u["referrals"] - c["baseline"].get(uid, 0)

                        ranking.append(
                            (uid, value)
                        )

                    ranking.sort(
                        key=lambda x: x[1],
                        reverse=True
                    )

                    winners = [
                        x[0]
                        for x in ranking[:c["winners"]]
                        if x[1] > 0
                    ]

                    for winner in winners:
                        users[winner]["coins"] += c["prize"]

                        notify(
                            winner,
                            f"🏆 <b>چالش تمام شد!</b>\n\n"
                            f"{c['title']}\n"
                            f"🪙 +{c['prize']} سکه"
                        )

                    notify(
                        ADMIN_ID,
                        f"🏆 چالش #{cid} تمام شد.\n"
                        f"برنده‌ها: {winners}"
                    )

        except Exception:
            pass

        time.sleep(30)


# ============================================================
# پاکسازی رنک‌های منقضی
# ============================================================

def rank_cleaner():
    while True:
        try:
            current = now()

            for u in users.values():
                active = []

                for r in u["ranks"]:
                    if r["expires"] is None:
                        active.append(r)
                    elif current < r["expires"]:
                        active.append(r)

                u["ranks"] = active

        except Exception:
            pass

        time.sleep(300)


# ============================================================
# بارگذاری اولیه دیتابیس
# ============================================================

# اکنون اطلاعات قبلی کاربران از Supabase وارد حافظه بات می‌شود.
db_load_users()
db_load_ranks_and_roles()


# ============================================================
# اجرای پس‌زمینه
# ============================================================

threading.Thread(
    target=background_worker,
    daemon=True
).start()

def db_sync_worker():
    while True:
        try:
            for uid in list(users.keys()):
                db_sync_user(uid)
        except Exception as e:
            print(f"[DB] periodic sync failed: {e}")
        time.sleep(15)


threading.Thread(
    target=db_sync_worker,
    daemon=True
).start()

threading.Thread(
    target=rank_cleaner,
    daemon=True
).start()


# ============================================================
# اجرای بات
# ============================================================

print("================================")
print("       CHATE ANONYMOUS")
print("================================")
print("Bot is running...")

bot.infinity_polling(
    skip_pending=True,
    timeout=60,
    long_polling_timeout=60
)
