import os
import json
import logging
import requests
import re
import datetime
import random
import string
import traceback
from typing import Dict, Optional, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ==================== কনফিগারেশন ====================
BOT_TOKEN = "8707267313:AAF2Gp6slMwY3vsJLinWsZyK-TNGDFfTdpU"
ADMIN_IDS = [1849126202]

FORCE_CHANNELS = [
    {"id": "-1003256463633", "url": "https://t.me/+kRLScHkVvpllYWQ1"},
]

BOT_NAME = "NHBD PRANK HUB"
BOT_USERNAME = "@nhbd_call_bot"
BOT_VERSION = "v2.2"

INITIAL_CREDITS = 2
REFERRAL_REWARD = 2
PRANK_API_URL = "https://api-lilac-seven-58.vercel.app/api.php"

PRANK_IDS = {
    "8810": "আপনি আমার গার্লফ্রেন্ডকে কল করেন কেন?",
    "8805": "গাজার মতো দুর্গন্ধ!",
    "8808": "আপনি আমার ওয়াই-ফাই চুরি করছেন!",
    "8809": "আপনি কেন আমাকে কল করেন?",
    "8803": "পিজ্জা ডেলিভারি",
    "8804": "আপনার ট্যাক্সি আপনার জন্য অপেক্ষা করছে",
    "8806": "আপনার কামরার হৈচৈ আওয়াজ",
    "8807": "আপনার কুকুরটি খুবই ক্লান্তিকর!"
}

DATA_FILE = "data.json"
CHANNELS_FILE = "channels.json"
PROMO_FILE = "promo_codes.json"

# ==================== সেফ ডেটাবেস ফাংশন ====================
def safe_load_json(file_path, default_data):
    """JSON ফাইল সেফলি লোড করে - ক্রাশ প্রতিরোধ করে"""
    if not os.path.exists(file_path):
        return default_data
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError, ValueError) as e:
        logging.warning(f"JSON লোড করতে ব্যর্থ: {file_path} - {e}")
        # ব্যাকআপ তৈরি
        if os.path.exists(file_path):
            backup_path = f"{file_path}.backup"
            try:
                os.rename(file_path, backup_path)
                logging.info(f"করাপ্ট ফাইল ব্যাকআপ করা হয়েছে: {backup_path}")
            except:
                pass
        return default_data

def safe_save_json(file_path, data):
    """JSON ফাইল সেফলি সেভ করে"""
    try:
        # টেম্প ফাইলে সেভ
        temp_file = f"{file_path}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        # সফল হলে রিলেস
        if os.path.exists(temp_file):
            os.replace(temp_file, file_path)
        return True
    except Exception as e:
        logging.error(f"JSON সেভ করতে ব্যর্থ: {file_path} - {e}")
        return False

# ==================== ডেটাবেস ফাংশন ====================
def load_data():
    return safe_load_json(DATA_FILE, {"users": {}, "total_users": 0, "comments": [], "ratings": []})

def save_data(data):
    return safe_save_json(DATA_FILE, data)

def load_channels():
    return safe_load_json(CHANNELS_FILE, FORCE_CHANNELS.copy())

def save_channels(channels):
    return safe_save_json(CHANNELS_FILE, channels)

def load_promo_codes():
    return safe_load_json(PROMO_FILE, {})

def save_promo_codes(promo_data):
    return safe_save_json(PROMO_FILE, promo_data)

def get_user(user_id):
    try:
        data = load_data()
        return data.get("users", {}).get(str(user_id))
    except Exception as e:
        logging.error(f"get_user error: {e}")
        return None

def create_user(user_id, referrer_id=None):
    try:
        data = load_data()
        user_data = {
            "credits": INITIAL_CREDITS,
            "referrals": [],
            "referrer": referrer_id,
            "total_referrals": 0,
            "joined_date": str(datetime.datetime.now()),
            "used_promos": []
        }
        
        if "users" not in data:
            data["users"] = {}
        if "total_users" not in data:
            data["total_users"] = 0
        
        data["users"][str(user_id)] = user_data
        data["total_users"] += 1
        
        referrer_notified = False
        if referrer_id and str(referrer_id) in data["users"]:
            data["users"][str(referrer_id)]["credits"] = data["users"][str(referrer_id)].get("credits", 0) + REFERRAL_REWARD
            data["users"][str(referrer_id)]["referrals"] = data["users"][str(referrer_id)].get("referrals", [])
            data["users"][str(referrer_id)]["referrals"].append(user_id)
            data["users"][str(referrer_id)]["total_referrals"] = data["users"][str(referrer_id)].get("total_referrals", 0) + 1
            referrer_notified = True
        
        save_data(data)
        return user_data, referrer_id if referrer_id else None, referrer_notified
    except Exception as e:
        logging.error(f"create_user error: {e}")
        return {"credits": INITIAL_CREDITS, "referrals": [], "referrer": None, "total_referrals": 0, "joined_date": str(datetime.datetime.now()), "used_promos": []}, None, False

def update_user(user_id, key, value):
    try:
        data = load_data()
        if str(user_id) in data.get("users", {}):
            data["users"][str(user_id)][key] = value
            save_data(data)
            return True
        return False
    except Exception as e:
        logging.error(f"update_user error: {e}")
        return False

def add_credits(user_id, amount):
    try:
        data = load_data()
        uid = str(user_id)
        if uid in data.get("users", {}):
            data["users"][uid]["credits"] = data["users"][uid].get("credits", 0) + amount
            save_data(data)
            return True
        return False
    except Exception as e:
        logging.error(f"add_credits error: {e}")
        return False

# ==================== প্রোমো কোড ফাংশন ====================
def generate_promo_code(length=8):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def create_promo_code(code, credits, max_uses, created_by):
    try:
        promo_data = load_promo_codes()
        
        if code in promo_data:
            return False, "কোড ইতিমধ্যে আছে!"
        
        promo_data[code] = {
            "credits": credits,
            "max_uses": max_uses,
            "used_count": 0,
            "created_by": created_by,
            "created_at": str(datetime.datetime.now()),
            "users": []
        }
        
        save_promo_codes(promo_data)
        return True, "প্রোমো কোড তৈরি করা হয়েছে!"
    except Exception as e:
        logging.error(f"create_promo_code error: {e}")
        return False, f"ত্রুটি: {str(e)}"

def use_promo_code(user_id, code):
    try:
        promo_data = load_promo_codes()
        
        if code not in promo_data:
            return False, "❌ ভুল প্রোমো কোড!"
        
        promo = promo_data[code]
        
        if promo.get("used_count", 0) >= promo.get("max_uses", 0):
            return False, "❌ এই প্রোমো কোডটি আর ব্যবহার করা যায় না!"
        
        if str(user_id) in promo.get("users", []):
            return False, "❌ আপনি ইতিমধ্যে এই প্রোমো কোড ব্যবহার করেছেন!"
        
        if add_credits(user_id, promo.get("credits", 0)):
            promo["used_count"] = promo.get("used_count", 0) + 1
            if "users" not in promo:
                promo["users"] = []
            promo["users"].append(str(user_id))
            save_promo_codes(promo_data)
            
            user_data = get_user(user_id)
            if user_data:
                used_promos = user_data.get("used_promos", [])
                used_promos.append(code)
                update_user(user_id, "used_promos", used_promos)
            
            return True, f"✅ {promo['credits']} ক্রেডিট পেয়েছেন!"
        
        return False, "❌ কিছু সমস্যা হয়েছে!"
    except Exception as e:
        logging.error(f"use_promo_code error: {e}")
        return False, f"❌ ত্রুটি: {str(e)}"

def delete_promo_code(code):
    try:
        promo_data = load_promo_codes()
        if code in promo_data:
            del promo_data[code]
            save_promo_codes(promo_data)
            return True
        return False
    except Exception as e:
        logging.error(f"delete_promo_code error: {e}")
        return False

# ==================== চ্যানেল চেক ====================
async def is_user_member_all_channels(user_id):
    try:
        channels = load_channels()
        if not channels:
            return True, []
        
        not_joined = []
        for channel in channels:
            try:
                chat_id = channel.get("id", "")
                if not chat_id:
                    continue
                    
                if str(chat_id).startswith("@"):
                    chat_id = chat_id
                else:
                    try:
                        chat_id = int(chat_id)
                    except ValueError:
                        chat_id = chat_id
                
                member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
                if member.status not in ["member", "administrator", "creator"]:
                    not_joined.append(channel)
            except Exception as e:
                logging.warning(f"Channel check error {channel}: {e}")
                not_joined.append(channel)
        return len(not_joined) == 0, not_joined
    except Exception as e:
        logging.error(f"is_user_member_all_channels error: {e}")
        return True, []

# ==================== প্রফেশনাল UI বাটন ====================
def get_permanent_keyboard(user_id=None):
    try:
        channels = load_channels()
        
        keyboard = [
            [InlineKeyboardButton("🏠 হোম", callback_data="home")],
            [InlineKeyboardButton("👤 প্রোফাইল", callback_data="profile")],
            [InlineKeyboardButton("📢 রেফার লিংক", callback_data="refer")],
            [InlineKeyboardButton("🎁 ইউজ প্রোমো কোড", callback_data="use_promo")],
            [InlineKeyboardButton("📞 প্রাঙ্ক কল", callback_data="prank_menu")],
        ]
        
        if user_id and user_id in ADMIN_IDS:
            keyboard.append([InlineKeyboardButton("👑 অ্যাডমিন প্যানেল", callback_data="admin_panel")])
        
        keyboard.append([InlineKeyboardButton("👨‍💻 ডেভেলপার", url="https://t.me/noobxvau")])
        
        for channel in channels:
            if channel and channel.get("url"):
                keyboard.append([InlineKeyboardButton("📢 জয়েন চ্যানেল", url=channel["url"])])
        
        keyboard.append([InlineKeyboardButton(f"ℹ️ {BOT_NAME} {BOT_VERSION}", callback_data="about")])
        
        return InlineKeyboardMarkup(keyboard)
    except Exception as e:
        logging.error(f"get_permanent_keyboard error: {e}")
        return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 হোম", callback_data="home")]])

def get_prank_keyboard():
    try:
        keyboard = []
        row = []
        for i, (prank_id, title) in enumerate(PRANK_IDS.items(), 1):
            row.append(InlineKeyboardButton(f"🎭 {prank_id}", callback_data=f"prank_{prank_id}"))
            if i % 4 == 0:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 ব্যাক টু হোম", callback_data="home")])
        return InlineKeyboardMarkup(keyboard)
    except Exception as e:
        logging.error(f"get_prank_keyboard error: {e}")
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 হোম", callback_data="home")]])

def get_admin_keyboard():
    try:
        keyboard = [
            [InlineKeyboardButton("📊 ইউজার তালিকা", callback_data="admin_users")],
            [InlineKeyboardButton("💰 ক্রেডিট দেয়", callback_data="admin_add_credit")],
            [InlineKeyboardButton("✏️ রেফার পয়েন্ট এডিট", callback_data="admin_edit_refer")],
            [InlineKeyboardButton("🎁 প্রোমো কোড তৈরি", callback_data="admin_create_promo")],
            [InlineKeyboardButton("📋 প্রোমো কোড তালিকা", callback_data="admin_promo_list")],
            [InlineKeyboardButton("📢 ব্রডকাস্ট", callback_data="admin_broadcast")],
            [InlineKeyboardButton("📋 কমেন্ট দেখুন", callback_data="admin_comments")],
            [InlineKeyboardButton("⭐ রেটিং দেখুন", callback_data="admin_ratings")],
            [InlineKeyboardButton("📢 চ্যানেল ম্যানেজ", callback_data="admin_channels")],
            [InlineKeyboardButton("📊 সার্ভার স্ট্যাটাস", callback_data="admin_stats")],
            [InlineKeyboardButton("🔙 হোম", callback_data="home")]
        ]
        return InlineKeyboardMarkup(keyboard)
    except Exception as e:
        logging.error(f"get_admin_keyboard error: {e}")
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 হোম", callback_data="home")]])

def get_channel_manage_keyboard():
    try:
        channels = load_channels()
        keyboard = []
        for i, channel in enumerate(channels):
            if channel and channel.get("id"):
                keyboard.append([
                    InlineKeyboardButton(f"❌ {channel['id']}", callback_data=f"remove_channel_{i}")
                ])
        keyboard.append([InlineKeyboardButton("➕ নতুন চ্যানেল যোগ", callback_data="admin_add_channel")])
        keyboard.append([InlineKeyboardButton("🔙 অ্যাডমিন প্যানেলে", callback_data="admin_panel")])
        return InlineKeyboardMarkup(keyboard)
    except Exception as e:
        logging.error(f"get_channel_manage_keyboard error: {e}")
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 অ্যাডমিন প্যানেলে", callback_data="admin_panel")]])

def get_promo_list_keyboard():
    try:
        promo_data = load_promo_codes()
        keyboard = []
        
        if promo_data:
            for code, info in list(promo_data.items())[:10]:
                used = info.get("used_count", 0)
                max_uses = info.get("max_uses", 0)
                status = "✅" if used < max_uses else "❌"
                keyboard.append([
                    InlineKeyboardButton(
                        f"{status} {code} ({used}/{max_uses})", 
                        callback_data=f"promo_detail_{code}"
                    )
                ])
        
        keyboard.append([InlineKeyboardButton("🗑️ প্রোমো ডিলিট", callback_data="admin_delete_promo")])
        keyboard.append([InlineKeyboardButton("🔙 অ্যাডমিন প্যানেলে", callback_data="admin_panel")])
        return InlineKeyboardMarkup(keyboard)
    except Exception as e:
        logging.error(f"get_promo_list_keyboard error: {e}")
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 অ্যাডমিন প্যানেলে", callback_data="admin_panel")]])

def get_about_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 হোম", callback_data="home")]])

# ==================== গ্লোবাল ====================
bot = None

# ==================== /admin কমান্ড ====================
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        
        if user_id not in ADMIN_IDS:
            await update.message.reply_text(
                "⛔ **আপনি অ্যাডমিন নন!**",
                reply_markup=get_permanent_keyboard(user_id),
                parse_mode="Markdown"
            )
            return
        
        await update.message.reply_text(
            "👑 **অ্যাডমিন প্যানেল**\n\n"
            "📌 স্বাগতম অ্যাডমিন! নিচের অপশন থেকে নির্বাচন করুন:",
            reply_markup=get_admin_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"admin_command error: {e}")
        await update.message.reply_text(f"❌ ত্রুটি: {str(e)[:100]}")

# ==================== হ্যান্ডলার ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        global bot
        bot = context.bot
        user = update.effective_user
        user_id = user.id

        is_member, not_joined = await is_user_member_all_channels(user_id)
        if not is_member:
            join_buttons = []
            for channel in not_joined:
                if channel and channel.get("url"):
                    join_buttons.append([InlineKeyboardButton("📢 জয়েন চ্যানেল", url=channel["url"])])
            join_buttons.append([InlineKeyboardButton("✅ চেক করুন", callback_data="check_join")])
            await update.message.reply_text(
                f"⚠️ **{BOT_NAME}** ব্যবহার করতে সব চ্যানেলে জয়েন করুন!",
                reply_markup=InlineKeyboardMarkup(join_buttons),
                parse_mode="Markdown"
            )
            return

        referrer_id = None
        if context.args:
            try:
                referrer_id = int(context.args[0])
            except:
                pass

        user_data = get_user(user_id)
        if not user_data:
            user_data, referrer, notified = create_user(user_id, referrer_id)
            
            welcome_text = f"""
🎉 **স্বাগতম {user.first_name}!**

━━━━━━━━━━━━━━━━━━━
🤖 **{BOT_NAME}**
📌 ভার্সন: {BOT_VERSION}
━━━━━━━━━━━━━━━━━━━

💰 আপনি **{INITIAL_CREDITS}** টি ফ্রি ক্রেডিট পেয়েছেন!

{ f'✅ আপনি **{REFERRAL_REWARD}** টি বোনাস ক্রেডিট পেয়েছেন রেফারের জন্য!' if referrer else '' }

📌 **কীভাবে ব্যবহার করবেন:**
• প্রাঙ্ক কল করতে 📞 প্রাঙ্ক কল বাটনে ক্লিক করুন
• বন্ধুদের আমন্ত্রণ জানাতে 📢 রেফার লিংক ব্যবহার করুন
• প্রোমো কোড ব্যবহার করতে 🎁 ইউজ প্রোমো কোড বাটনে ক্লিক করুন
• আপনার ব্যালেন্স চেক করতে 👤 প্রোফাইলে যান

━━━━━━━━━━━━━━━━━━━
🔹 **বট ব্যবহারের জন্য নিচের মেনু থেকে নির্বাচন করুন:**
"""
            if referrer:
                try:
                    referrer_data = get_user(referrer)
                    if referrer_data:
                        await bot.send_message(
                            chat_id=referrer,
                            text=f"""
🎉 **নতুন রেফার!**

━━━━━━━━━━━━━━━━━━━
👤 ইউজার: {user.first_name}
🆔 আইডি: `{user_id}`
💰 আপনি {REFERRAL_REWARD}টি ক্রেডিট পেয়েছেন!
👥 মোট রেফার: {referrer_data.get('total_referrals', 0)} জন
💳 বর্তমান ব্যালেন্স: {referrer_data.get('credits', 0)} ক্রেডিট
━━━━━━━━━━━━━━━━━━━
""",
                            parse_mode="Markdown",
                            reply_markup=get_permanent_keyboard(referrer)
                        )
                except Exception as e:
                    logging.error(f"রেফার নোটিফিকেশন এরর: {e}")
        else:
            welcome_text = f"""
👋 **স্বাগতম kembali {user.first_name}!**

━━━━━━━━━━━━━━━━━━━
🤖 **{BOT_NAME}** {BOT_VERSION}
━━━━━━━━━━━━━━━━━━━

📌 বট ব্যবহারের জন্য নিচের মেনু থেকে নির্বাচন করুন:
"""

        await update.message.reply_text(
            welcome_text,
            reply_markup=get_permanent_keyboard(user_id),
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"start error: {e}")
        await update.message.reply_text(f"❌ ত্রুটি: {str(e)[:100]}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        global bot
        bot = context.bot
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        data = query.data

        # চ্যানেল চেক
        if data != "check_join" and not data.startswith("admin") and data != "about":
            is_member, not_joined = await is_user_member_all_channels(user_id)
            if not is_member:
                join_buttons = []
                for channel in not_joined:
                    if channel and channel.get("url"):
                        join_buttons.append([InlineKeyboardButton("📢 জয়েন চ্যানেল", url=channel["url"])])
                join_buttons.append([InlineKeyboardButton("✅ চেক করুন", callback_data="check_join")])
                await query.edit_message_text(
                    "⚠️ **সব চ্যানেলে জয়েন করুন!**",
                    reply_markup=InlineKeyboardMarkup(join_buttons),
                    parse_mode="Markdown"
                )
                return

        if data == "check_join":
            is_member, not_joined = await is_user_member_all_channels(user_id)
            if is_member:
                await query.edit_message_text(
                    "✅ **সব চ্যানেলে জয়েন করেছেন!**",
                    reply_markup=get_permanent_keyboard(user_id),
                    parse_mode="Markdown"
                )
            else:
                join_buttons = []
                for channel in not_joined:
                    if channel and channel.get("url"):
                        join_buttons.append([InlineKeyboardButton("📢 জয়েন চ্যানেল", url=channel["url"])])
                join_buttons.append([InlineKeyboardButton("✅ চেক করুন", callback_data="check_join")])
                await query.edit_message_text(
                    "❌ **কিছু চ্যানেলে জয়েন করেননি!**",
                    reply_markup=InlineKeyboardMarkup(join_buttons),
                    parse_mode="Markdown"
                )
            return

        # ==================== About ====================
        if data == "about":
            await query.edit_message_text(
                f"""
ℹ️ **{BOT_NAME}**

━━━━━━━━━━━━━━━━━━━
📌 **বট তথ্য:**
• নাম: {BOT_NAME}
• ভার্সন: {BOT_VERSION}
• ডেভেলপার: @nhbd_dev
• ভাষা: বাংলা

📌 **ফিচারসমূহ:**
• 🎭 ৮টি প্রাঙ্ক কল
• 💰 ক্রেডিট সিস্টেম
• 📢 রেফার সিস্টেম
• 🎁 প্রোমো কোড সিস্টেম
• 👑 অ্যাডমিন প্যানেল
• 📊 ইউজার ট্র্যাকিং

📌 **সাপোর্ট:**
• প্রশ্ন/সমস্যা: @nhbd_dev
• চ্যানেল: @nhbd_official
━━━━━━━━━━━━━━━━━━━
""",
                reply_markup=get_about_keyboard(),
                parse_mode="Markdown"
            )
            return

        # ==================== ইউজার প্রোমো কোড ====================
        if data == "use_promo":
            await query.edit_message_text(
                f"""
🎁 **প্রোমো কোড ব্যবহার করুন**

━━━━━━━━━━━━━━━━━━━
📌 আপনার প্রোমো কোড লিখুন:

উদাহরণ: `PRANK2024`

❌ বাতিল করতে: /cancel
━━━━━━━━━━━━━━━━━━━
""",
                parse_mode="Markdown"
            )
            context.user_data['waiting_promo'] = True
            return

        # ==================== অ্যাডমিন চেক ====================
        if data == "admin_panel":
            if user_id not in ADMIN_IDS:
                await query.edit_message_text(
                    "⛔ **আপনি অ্যাডমিন নন!**",
                    reply_markup=get_permanent_keyboard(user_id),
                    parse_mode="Markdown"
                )
                return
            await query.edit_message_text(
                "👑 **অ্যাডমিন প্যানেল**\n\n"
                "📌 স্বাগতম অ্যাডমিন! নিচের অপশন থেকে নির্বাচন করুন:",
                reply_markup=get_admin_keyboard(),
                parse_mode="Markdown"
            )
            return

        # ==================== অ্যাডমিন অপশন ====================
        if data.startswith("admin"):
            if user_id not in ADMIN_IDS:
                await query.edit_message_text(
                    "⛔ **আপনি অ্যাডমিন নন!**",
                    reply_markup=get_permanent_keyboard(user_id),
                    parse_mode="Markdown"
                )
                return

            if data == "admin_create_promo":
                context.user_data['admin_action'] = 'create_promo'
                await query.edit_message_text(
                    f"""
🎁 **প্রোমো কোড তৈরি করুন**

━━━━━━━━━━━━━━━━━━━
📌 নিচের তথ্য দিন (স্পেস দিয়ে আলাদা):

**ফরম্যাট:** `প্রোমো কোড ক্রেডিট_সংখ্যা ম্যাক্স_ইউজ`

**উদাহরণ:** `PRANK2024 5 10`

❌ বাতিল: /cancel
━━━━━━━━━━━━━━━━━━━
""",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="admin_panel")]]),
                    parse_mode="Markdown"
                )
                return

            elif data == "admin_promo_list":
                promo_data = load_promo_codes()
                if not promo_data:
                    await query.edit_message_text(
                        "📭 **কোনো প্রোমো কোড নেই!**",
                        reply_markup=get_admin_keyboard(),
                        parse_mode="Markdown"
                    )
                    return
                
                text = f"""
🎁 **প্রোমো কোড তালিকা**
━━━━━━━━━━━━━━━━━━━
"""
                for code, info in promo_data.items():
                    used = info.get("used_count", 0)
                    max_uses = info.get("max_uses", 0)
                    status = "✅" if used < max_uses else "❌"
                    text += f"""
{status} **{code}**
   💰 {info.get('credits', 0)} ক্রেডিট
   👥 {used}/{max_uses} ইউজ
   📅 {info.get('created_at', 'N/A')[:10]}
━━━━━━━━━━━━━━━━━━━
"""
                await query.edit_message_text(text, reply_markup=get_promo_list_keyboard(), parse_mode="Markdown")
                return

            elif data.startswith("promo_detail_"):
                code = data.replace("promo_detail_", "")
                promo_data = load_promo_codes()
                if code in promo_data:
                    info = promo_data[code]
                    text = f"""
🎁 **প্রোমো কোড ডিটেইল**
━━━━━━━━━━━━━━━━━━━
📌 কোড: `{code}`
💰 ক্রেডিট: {info.get('credits', 0)}
👥 ইউজ: {info.get('used_count', 0)}/{info.get('max_uses', 0)}
📅 তৈরি: {info.get('created_at', 'N/A')}
👤 তৈরি করেছেন: `{info.get('created_by', 'N/A')}`

**ব্যবহারকারী তালিকা:**
"""
                    users_list = info.get('users', [])
                    if users_list:
                        for i, uid in enumerate(users_list[:10], 1):
                            text += f"{i}. `{uid}`\n"
                        if len(users_list) > 10:
                            text += f"... আরো {len(users_list) - 10} জন"
                    else:
                        text += "❌ এখনো কেউ ব্যবহার করেনি"
                    
                    await query.edit_message_text(
                        text,
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 তালিকায়", callback_data="admin_promo_list")],
                            [InlineKeyboardButton("🗑️ ডিলিট", callback_data=f"delete_promo_{code}")],
                            [InlineKeyboardButton("🔙 অ্যাডমিন প্যানেলে", callback_data="admin_panel")]
                        ]),
                        parse_mode="Markdown"
                    )
                return

            elif data.startswith("delete_promo_"):
                code = data.replace("delete_promo_", "")
                if delete_promo_code(code):
                    await query.edit_message_text(
                        f"✅ **প্রোমো কোড `{code}` ডিলিট করা হয়েছে!**",
                        reply_markup=get_admin_keyboard(),
                        parse_mode="Markdown"
                    )
                else:
                    await query.edit_message_text(
                        f"❌ **প্রোমো কোড `{code}` পাওয়া যায়নি!**",
                        reply_markup=get_admin_keyboard(),
                        parse_mode="Markdown"
                    )
                return

            elif data == "admin_delete_promo":
                context.user_data['admin_action'] = 'delete_promo'
                await query.edit_message_text(
                    f"""
🗑️ **প্রোমো কোড ডিলিট করুন**

━━━━━━━━━━━━━━━━━━━
📌 যে প্রোমো কোড ডিলিট করতে চান সেটি লিখুন:

উদাহরণ: `PRANK2024`

❌ বাতিল: /cancel
━━━━━━━━━━━━━━━━━━━
""",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 তালিকায়", callback_data="admin_promo_list")]]),
                    parse_mode="Markdown"
                )
                return

            elif data == "admin_users":
                data = load_data()
                users = data.get("users", {})
                if not users:
                    await query.edit_message_text("❌ **কোনো ইউজার নেই।**", reply_markup=get_admin_keyboard())
                    return
                text = f"📊 **মোট ইউজার:** {len(users)}\n━━━━━━━━━━━━━━━━━━━\n\n"
                for i, (uid, udata) in enumerate(list(users.items())[:10], 1):
                    text += f"{i}. 🆔 `{uid}`\n   💰 {udata.get('credits', 0)} | 👥 {udata.get('total_referrals', 0)}\n"
                if len(users) > 10:
                    text += f"\n... আরো {len(users) - 10} জন"
                await query.edit_message_text(text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")
                return

            elif data == "admin_stats":
                data = load_data()
                users = data.get("users", {})
                promo_data = load_promo_codes()
                total_users = len(users)
                total_credits = sum(u.get('credits', 0) for u in users.values())
                total_referrals = sum(u.get('total_referrals', 0) for u in users.values())
                total_promos = len(promo_data)
                
                text = f"""
📊 **সার্ভার স্ট্যাটাস**
━━━━━━━━━━━━━━━━━━━
👥 মোট ইউজার: {total_users}
💰 মোট ক্রেডিট: {total_credits}
👥 মোট রেফার: {total_referrals}
🎁 মোট প্রোমো: {total_promos}
📌 ভার্সন: {BOT_VERSION}
📅 আপডেট: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━
"""
                await query.edit_message_text(text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")
                return

            elif data == "admin_add_credit":
                context.user_data['admin_action'] = 'add_credit'
                await query.edit_message_text(
                    "💰 **ক্রেডিট দেয়**\n\n"
                    "ইউজার আইডি ও ক্রেডিট লিখুন:\n"
                    "উদাহরণ: `1849126202 10`",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="admin_panel")]]),
                    parse_mode="Markdown"
                )
                return

            elif data == "admin_edit_refer":
                context.user_data['admin_action'] = 'edit_refer'
                await query.edit_message_text(
                    "✏️ **রেফার পয়েন্ট এডিট**\n\n"
                    "ইউজার আইডি ও পয়েন্ট লিখুন:\n"
                    "উদাহরণ: `1849126202 10`",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="admin_panel")]]),
                    parse_mode="Markdown"
                )
                return

            elif data == "admin_broadcast":
                context.user_data['admin_action'] = 'broadcast'
                await query.edit_message_text(
                    "📢 **ব্রডকাস্ট**\n\n"
                    "সব ইউজারকে পাঠানোর মেসেজ লিখুন:",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="admin_panel")]]),
                    parse_mode="Markdown"
                )
                return

            elif data == "admin_comments":
                data = load_data()
                comments = data.get("comments", [])
                if not comments:
                    await query.edit_message_text("📭 **এখনো কোনো কমেন্ট নেই।**", reply_markup=get_admin_keyboard())
                    return
                text = f"📋 **মোট কমেন্ট:** {len(comments)}\n━━━━━━━━━━━━━━━━━━━\n\n"
                for i, cmt in enumerate(comments[-10:], 1):
                    text += f"{i}. 👤 `{cmt.get('user_id', 'N/A')}`:\n   💬 {cmt.get('comment', '')[:50]}\n"
                await query.edit_message_text(text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")
                return

            elif data == "admin_ratings":
                data = load_data()
                ratings = data.get("ratings", [])
                if not ratings:
                    await query.edit_message_text("⭐ **এখনো কোনো রেটিং নেই।**", reply_markup=get_admin_keyboard())
                    return
                avg = sum(int(r.get('rating', 0)) for r in ratings) / len(ratings) if ratings else 0
                text = f"""
⭐ **রেটিং স্ট্যাটাস**
━━━━━━━━━━━━━━━━━━━
📊 গড় রেটিং: {avg:.1f}/5
📊 মোট রেটিং: {len(ratings)}
━━━━━━━━━━━━━━━━━━━

**শেষ ৫টি রেটিং:**
"""
                for i, r in enumerate(ratings[-5:], 1):
                    text += f"{i}. 👤 `{r.get('user_id', 'N/A')}`: {r.get('rating', 0)}⭐\n"
                await query.edit_message_text(text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")
                return

            elif data == "admin_channels":
                await query.edit_message_text(
                    "📢 **চ্যানেল ম্যানেজ**\n\n"
                    "নিচের অপশন থেকে নির্বাচন করুন:",
                    reply_markup=get_channel_manage_keyboard(),
                    parse_mode="Markdown"
                )
                return

            elif data.startswith("remove_channel_"):
                try:
                    index = int(data.replace("remove_channel_", ""))
                    channels = load_channels()
                    if 0 <= index < len(channels):
                        removed = channels.pop(index)
                        save_channels(channels)
                        await query.edit_message_text(
                            f"✅ **চ্যানেল রিমুভ করা হয়েছে!**\n\n"
                            f"🆔 আইডি: `{removed.get('id', 'N/A')}`",
                            reply_markup=get_channel_manage_keyboard(),
                            parse_mode="Markdown"
                        )
                    else:
                        await query.edit_message_text("❌ **চ্যানেল পাওয়া যায়নি!**", reply_markup=get_channel_manage_keyboard())
                except Exception as e:
                    await query.edit_message_text(f"❌ ত্রুটি: {str(e)[:100]}", reply_markup=get_channel_manage_keyboard())
                return

            elif data == "admin_add_channel":
                context.user_data['admin_action'] = 'add_channel'
                await query.edit_message_text(
                    "➕ **নতুন চ্যানেল যোগ করুন**\n\n"
                    "চ্যানেল আইডি লিখুন:\n"
                    "• পাবলিক: @username\n"
                    "• প্রাইভেট: -100xxxxxxxxxx\n\n"
                    "উদাহরণ: `-1003256463633`",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="admin_channels")]]),
                    parse_mode="Markdown"
                )
                context.user_data['waiting_channel_id'] = True
                return

        # ==================== সাধারণ ইউজার মেনু ====================
        if data == "home":
            await query.edit_message_text(
                f"""
🏠 **হোম**

━━━━━━━━━━━━━━━━━━━
🤖 **{BOT_NAME}** {BOT_VERSION}
━━━━━━━━━━━━━━━━━━━

📌 বট ব্যবহারের জন্য নিচের অপশন থেকে নির্বাচন করুন:
""",
                reply_markup=get_permanent_keyboard(user_id),
                parse_mode="Markdown"
            )
            return

        elif data == "prank_menu":
            await query.edit_message_text(
                f"""
📞 **প্রাঙ্ক কল মেনু**

━━━━━━━━━━━━━━━━━━━
🎭 **উপলব্ধ প্রাঙ্ক আইডি:**
• 8810 - আপনি আমার গার্লফ্রেন্ডকে কল করেন কেন?
• 8805 - গাজার মতো দুর্গন্ধ!
• 8808 - আপনি আমার ওয়াই-ফাই চুরি করছেন!
• 8809 - আপনি কেন আমাকে কল করেন?
• 8803 - পিজ্জা ডেলিভারি
• 8804 - আপনার ট্যাক্সি আপনার জন্য অপেক্ষা করছে
• 8806 - আপনার কামরার হৈচৈ আওয়াজ
• 8807 - আপনার কুকুরটি খুবই ক্লান্তিকর!

💰 **ক্রেডিট খরচ:** ১ প্রতি কলে

📌 **নির্দেশনা:**
প্রাঙ্ক আইডি নির্বাচন করুন, তারপর নাম্বার দিন।
━━━━━━━━━━━━━━━━━━━
""",
                reply_markup=get_prank_keyboard(),
                parse_mode="Markdown"
            )
            return

        elif data.startswith("prank_"):
            prank_id = data.replace("prank_", "")
            context.user_data['selected_prank'] = prank_id
            await query.edit_message_text(
                f"""
📱 **নাম্বার দিন**

━━━━━━━━━━━━━━━━━━━
🆔 প্রাঙ্ক আইডি: `{prank_id}`
📝 টাইটেল: {PRANK_IDS.get(prank_id, 'N/A')}

📌 **নির্দেশনা:**
নাম্বার লিখুন (উদাহরণ: `01712345678`)

❌ বাতিল করতে: /cancel
━━━━━━━━━━━━━━━━━━━
""",
                parse_mode="Markdown"
            )
            context.user_data['waiting_number'] = True
            return

        elif data == "profile":
            user_data = get_user(user_id)
            if not user_data:
                user_data, _, _ = create_user(user_id)
            
            text = f"""
👤 **আপনার প্রোফাইল**

━━━━━━━━━━━━━━━━━━━
🆔 আইডি: `{user_id}`
💰 ক্রেডিট: {user_data.get('credits', 0)}
👥 রেফার: {user_data.get('total_referrals', 0)} জন
📊 টোটাল ইউজার: {load_data().get('total_users', 0)} জন
📅 জয়েন: {user_data.get('joined_date', 'N/A')}
🎁 ইউজড প্রোমো: {len(user_data.get('used_promos', []))} টি
━━━━━━━━━━━━━━━━━━━
"""
            await query.edit_message_text(text, reply_markup=get_permanent_keyboard(user_id), parse_mode="Markdown")
            return

        elif data == "refer":
            user_data = get_user(user_id)
            if not user_data:
                user_data, _, _ = create_user(user_id)
            
            text = f"""
📢 **রেফার লিংক**

━━━━━━━━━━━━━━━━━━━
💰 প্রতি রেফারে {REFERRAL_REWARD} ক্রেডিট!

🔗 **আপনার লিংক:**
`https://t.me/{BOT_USERNAME.replace('@', '')}?start={user_id}`

📊 **পরিসংখ্যান:**
👥 মোট রেফার: {user_data.get('total_referrals', 0)} জন
"""
            referrals = user_data.get('referrals', [])
            if referrals:
                text += f"\n📋 **রেফার তালিকা:**\n"
                for idx, ref_id in enumerate(referrals[:10], 1):
                    text += f"{idx}. `{ref_id}`\n"
                if len(referrals) > 10:
                    text += f"... আরো {len(referrals) - 10} জন"
            
            text += "\n━━━━━━━━━━━━━━━━━━━"
            await query.edit_message_text(text, reply_markup=get_permanent_keyboard(user_id), parse_mode="Markdown")
            return

    except Exception as e:
        logging.error(f"button_handler error: {e}")
        try:
            await query.edit_message_text(f"❌ ত্রুটি: {str(e)[:100]}")
        except:
            pass

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        text = update.message.text.strip()

        # ==================== প্রোমো কোড ইনপুট ====================
        if context.user_data.get('waiting_promo'):
            if text.lower() == '/cancel':
                context.user_data['waiting_promo'] = False
                await update.message.reply_text(
                    "❌ **বাতিল করা হয়েছে!**",
                    reply_markup=get_permanent_keyboard(user_id),
                    parse_mode="Markdown"
                )
                return

            success, message = use_promo_code(user_id, text.upper())
            
            if success:
                user_data = get_user(user_id)
                await update.message.reply_text(
                    f"""
🎉 **প্রোমো কোড সফল!**

━━━━━━━━━━━━━━━━━━━
{message}
💳 **নতুন ব্যালেন্স:** {user_data.get('credits', 0) if user_data else 0} ক্রেডিট
━━━━━━━━━━━━━━━━━━━
""",
                    reply_markup=get_permanent_keyboard(user_id),
                    parse_mode="Markdown"
                )
                
                for admin_id in ADMIN_IDS:
                    try:
                        await bot.send_message(
                            chat_id=admin_id,
                            text=f"""
🎁 **প্রোমো কোড ব্যবহার!**

━━━━━━━━━━━━━━━━━━━
👤 ইউজার: `{user_id}`
🎁 কোড: `{text.upper()}`
💰 নতুন ব্যালেন্স: {user_data.get('credits', 0) if user_data else 0}
━━━━━━━━━━━━━━━━━━━
""",
                            parse_mode="Markdown"
                        )
                    except:
                        pass
            else:
                await update.message.reply_text(
                    f"""
❌ **প্রোমো কোড ব্যর্থ!**

━━━━━━━━━━━━━━━━━━━
{message}
━━━━━━━━━━━━━━━━━━━
""",
                    reply_markup=get_permanent_keyboard(user_id),
                    parse_mode="Markdown"
                )
            
            context.user_data['waiting_promo'] = False
            return

        # ==================== চ্যানেল আইডি ইনপুট ====================
        if context.user_data.get('waiting_channel_id'):
            channel_id = text
            context.user_data['temp_channel_id'] = channel_id
            context.user_data['waiting_channel_id'] = False
            context.user_data['waiting_channel_url'] = True
            await update.message.reply_text(
                "✅ **চ্যানেল আইডি সেভ করা হয়েছে!**\n\n"
                "এখন চ্যানেলের URL দিন:\n"
                "উদাহরণ: `https://t.me/+kRLScHkVvpllYWQ1`",
                parse_mode="Markdown"
            )
            return

        if context.user_data.get('waiting_channel_url'):
            channel_url = text
            channel_id = context.user_data.get('temp_channel_id')
            channels = load_channels()
            channels.append({"id": channel_id, "url": channel_url})
            save_channels(channels)
            context.user_data['temp_channel_id'] = None
            context.user_data['waiting_channel_url'] = False
            context.user_data['admin_action'] = None
            await update.message.reply_text(
                f"✅ **চ্যানেল যোগ করা হয়েছে!**\n\n"
                f"🆔 আইডি: `{channel_id}`\n"
                f"🔗 URL: {channel_url}",
                reply_markup=get_admin_keyboard(),
                parse_mode="Markdown"
            )
            return

        # ==================== নাম্বার ইনপুট ====================
        if context.user_data.get('waiting_number'):
            if text.lower() == '/cancel':
                context.user_data['waiting_number'] = False
                context.user_data['selected_prank'] = None
                await update.message.reply_text(
                    "❌ **বাতিল করা হয়েছে!**",
                    reply_markup=get_permanent_keyboard(user_id),
                    parse_mode="Markdown"
                )
                return

            clean_number = re.sub(r'[\s\-\(\)]', '', text)
            if not re.match(r'^\+?[0-9]{10,15}$', clean_number):
                await update.message.reply_text(
                    "❌ **ভুল নাম্বার ফরম্যাট!**\n\n"
                    "সঠিক ফরম্যাট: `01712345678`",
                    parse_mode="Markdown"
                )
                return

            prank_id = context.user_data.get('selected_prank')
            if not prank_id:
                await update.message.reply_text(
                    "❌ **প্রথমে প্রাঙ্ক আইডি নির্বাচন করুন!**",
                    reply_markup=get_permanent_keyboard(user_id),
                    parse_mode="Markdown"
                )
                context.user_data['waiting_number'] = False
                return

            user_data = get_user(user_id)
            if not user_data:
                user_data, _, _ = create_user(user_id)

            if user_data.get('credits', 0) <= 0:
                await update.message.reply_text(
                    "❌ **পর্যাপ্ত ক্রেডিট নেই!**\n\n"
                    "রেফার করে বা প্রোমো কোড ব্যবহার করে ক্রেডিট সংগ্রহ করুন।",
                    reply_markup=get_permanent_keyboard(user_id),
                    parse_mode="Markdown"
                )
                context.user_data['waiting_number'] = False
                context.user_data['selected_prank'] = None
                return

            msg = await update.message.reply_text(
                f"⏳ **প্রাঙ্ক কল হচ্ছে...**\n\n"
                f"📱 {clean_number}\n"
                f"🆔 {prank_id}\n"
                f"📝 {PRANK_IDS.get(prank_id, 'N/A')}\n\n"
                f"দয়া করে অপেক্ষা করুন...",
                parse_mode="Markdown"
            )
            
            try:
                api_url = f"{PRANK_API_URL}?number={clean_number}&prank={prank_id}"
                response = requests.get(api_url, timeout=30)
                result = response.text[:200] if response.text else "No response"
                
                user_data['credits'] = user_data.get('credits', 0) - 1
                update_user(user_id, "credits", user_data['credits'])
                
                await msg.edit_text(
                    f"✅ **প্রাঙ্ক কল সম্পন্ন!**\n\n"
                    f"📱 {clean_number}\n"
                    f"🆔 {prank_id}\n"
                    f"📊 {result}\n\n"
                    f"💰 বাকি ক্রেডিট: {user_data.get('credits', 0)}",
                    reply_markup=get_permanent_keyboard(user_id),
                    parse_mode="Markdown"
                )
            except requests.exceptions.Timeout:
                await msg.edit_text(
                    f"⏰ **টাইমআউট!**\n\nAPI থেকে সাড়া পাওয়া যায়নি।",
                    reply_markup=get_permanent_keyboard(user_id),
                    parse_mode="Markdown"
                )
            except Exception as e:
                await msg.edit_text(
                    f"❌ **ত্রুটি!**\n\n{str(e)[:100]}",
                    reply_markup=get_permanent_keyboard(user_id),
                    parse_mode="Markdown"
                )

            context.user_data['waiting_number'] = False
            context.user_data['selected_prank'] = None
            return

        # ==================== অ্যাডমিন ইনপুট ====================
        if user_id in ADMIN_IDS:
            action = context.user_data.get('admin_action')
            if not action:
                return

            if action == 'create_promo':
                try:
                    parts = text.split()
                    if len(parts) != 3:
                        await update.message.reply_text(
                            "❌ **ভুল ফরম্যাট!**\n\n"
                            "ফরম্যাট: `প্রোমো কোড ক্রেডিট_সংখ্যা ম্যাক্স_ইউজ`\n"
                            "উদাহরণ: `PRANK2024 5 10`",
                            parse_mode="Markdown"
                        )
                        return
                    
                    code = parts[0].upper()
                    credits = int(parts[1])
                    max_uses = int(parts[2])
                    
                    if credits <= 0 or max_uses <= 0:
                        await update.message.reply_text(
                            "❌ **ক্রেডিট এবং ম্যাক্স ইউজ ০ এর বেশি হতে হবে!**",
                            parse_mode="Markdown"
                        )
                        return
                    
                    success, message = create_promo_code(code, credits, max_uses, user_id)
                    
                    if success:
                        await update.message.reply_text(
                            f"""
✅ **প্রোমো কোড তৈরি করা হয়েছে!**

━━━━━━━━━━━━━━━━━━━
🎁 কোড: `{code}`
💰 ক্রেডিট: {credits}
👥 ম্যাক্স ইউজ: {max_uses}
📅 তৈরি: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━
""",
                            reply_markup=get_admin_keyboard(),
                            parse_mode="Markdown"
                        )
                    else:
                        await update.message.reply_text(
                            f"❌ {message}",
                            reply_markup=get_admin_keyboard(),
                            parse_mode="Markdown"
                        )
                except ValueError:
                    await update.message.reply_text(
                        "❌ **ভুল ফরম্যাট!**\n\n"
                        "ক্রেডিট এবং ম্যাক্স ইউজ সংখ্যা হতে হবে।",
                        reply_markup=get_admin_keyboard(),
                        parse_mode="Markdown"
                    )
                context.user_data['admin_action'] = None
                return

            if action == 'delete_promo':
                code = text.upper()
                if delete_promo_code(code):
                    await update.message.reply_text(
                        f"✅ **প্রোমো কোড `{code}` ডিলিট করা হয়েছে!**",
                        reply_markup=get_admin_keyboard(),
                        parse_mode="Markdown"
                    )
                else:
                    await update.message.reply_text(
                        f"❌ **প্রোমো কোড `{code}` পাওয়া যায়নি!**",
                        reply_markup=get_admin_keyboard(),
                        parse_mode="Markdown"
                    )
                context.user_data['admin_action'] = None
                return

            if action == 'add_credit':
                try:
                    parts = text.split()
                    if len(parts) != 2:
                        await update.message.reply_text("❌ ফরম্যাট: `user_id amount`", parse_mode="Markdown")
                        return
                    uid = int(parts[0])
                    amount = int(parts[1])
                    if add_credits(uid, amount):
                        await update.message.reply_text(
                            f"✅ `{uid}`-কে {amount} ক্রেডিট দেওয়া হয়েছে!",
                            reply_markup=get_admin_keyboard(),
                            parse_mode="Markdown"
                        )
                    else:
                        await update.message.reply_text(
                            "❌ ইউজার পাওয়া যায়নি!",
                            reply_markup=get_admin_keyboard()
                        )
                except:
                    await update.message.reply_text("❌ ভুল ফরম্যাট!", parse_mode="Markdown")
                context.user_data['admin_action'] = None

            elif action == 'edit_refer':
                try:
                    parts = text.split()
                    if len(parts) != 2:
                        await update.message.reply_text("❌ ফরম্যাট: `user_id points`", parse_mode="Markdown")
                        return
                    uid = int(parts[0])
                    points = int(parts[1])
                    data = load_data()
                    if str(uid) in data.get("users", {}):
                        data["users"][str(uid)]["total_referrals"] = points
                        save_data(data)
                        await update.message.reply_text(
                            f"✅ `{uid}`-এর রেফার পয়েন্ট {points} করা হয়েছে!",
                            reply_markup=get_admin_keyboard(),
                            parse_mode="Markdown"
                        )
                    else:
                        await update.message.reply_text(
                            "❌ ইউজার পাওয়া যায়নি!",
                            reply_markup=get_admin_keyboard()
                        )
                except:
                    await update.message.reply_text("❌ ভুল ফরম্যাট!", parse_mode="Markdown")
                context.user_data['admin_action'] = None

            elif action == 'broadcast':
                users = load_data().get("users", {})
                success = 0
                await update.message.reply_text("📤 **ব্রডকাস্ট শুরু হচ্ছে...**")
                for uid in users:
                    try:
                        await context.bot.send_message(
                            chat_id=int(uid),
                            text=f"📢 **অ্যাডমিন বার্তা**\n\n{text}",
                            parse_mode="Markdown",
                            reply_markup=get_permanent_keyboard(int(uid))
                        )
                        success += 1
                    except:
                        pass
                await update.message.reply_text(
                    f"✅ **{success} জন ইউজার পেয়েছে!**",
                    reply_markup=get_admin_keyboard()
                )
                context.user_data['admin_action'] = None

    except Exception as e:
        logging.error(f"handle_message error: {e}")
        try:
            await update.message.reply_text(f"❌ ত্রুটি: {str(e)[:100]}")
        except:
            pass

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Error: {context.error}")
    logging.error(traceback.format_exc())
    try:
        if update and update.effective_user:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=f"❌ সার্ভার ত্রুটি! দয়া করে আবার চেষ্টা করুন।"
            )
    except:
        pass

# ==================== মেইন ====================
def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        global bot
        bot = application.bot
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("admin", admin_command))
        application.add_handler(CommandHandler("cancel", handle_message))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_error_handler(error_handler)
        
        print(f"""
╔════════════════════════════════════╗
║        🤖 {BOT_NAME} চালু!         ║
╠════════════════════════════════════╣
║ 📢 চ্যানেল: {len(load_channels())}টি              ║
║ 👑 অ্যাডমিন: {ADMIN_IDS[0]}        ║
║ 🔗 বট: {BOT_USERNAME}              ║
║ 📌 ভার্সন: {BOT_VERSION}              ║
║ 🎁 প্রোমো: ✅ সক্রিয়              ║
║ 📢 রেফার: ✅ সক্রিয়               ║
╚════════════════════════════════════╝
""")
        
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logging.error(f"Main error: {e}")
        print(f"❌ বট চালু করতে ব্যর্থ: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 বট বন্ধ করা হয়েছে।")
    except Exception as e:
        print(f"❌ ফাটাল ত্রুটি: {e}")
