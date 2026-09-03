import os
import json
import logging
import requests
import re
import datetime
import random
import string
from typing import Dict, Optional, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ==================== কনফিগারেশন ====================
BOT_TOKEN = "8879701783:AAHTfTgDWT3HWnlc1xCRgYeHu_MGolCMx5E"
ADMIN_IDS = [1849126202]

FORCE_CHANNELS = [
    {"id": "-1003256463633", "url": "https://t.me/+kRLScHkVvpllYWQ1"},
]

BOT_NAME = "NHBD PRANK HUB"
BOT_USERNAME = "@Testujnch_bot"
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

# ==================== ডেটাবেস ====================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "total_users": 0, "comments": [], "ratings": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": {}, "total_users": 0, "comments": [], "ratings": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_channels():
    if not os.path.exists(CHANNELS_FILE):
        return FORCE_CHANNELS.copy()
    try:
        with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return FORCE_CHANNELS.copy()

def save_channels(channels):
    with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
        json.dump(channels, f, indent=4, ensure_ascii=False)

def load_promo_codes():
    if not os.path.exists(PROMO_FILE):
        return {}
    try:
        with open(PROMO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_promo_codes(promo_data):
    with open(PROMO_FILE, "w", encoding="utf-8") as f:
        json.dump(promo_data, f, indent=4, ensure_ascii=False)

def get_user(user_id):
    data = load_data()
    return data["users"].get(str(user_id))

def create_user(user_id, referrer_id=None):
    data = load_data()
    user_data = {
        "credits": INITIAL_CREDITS,
        "referrals": [],
        "referrer": referrer_id,
        "total_referrals": 0,
        "joined_date": str(datetime.datetime.now()),
        "used_promos": []
    }
    data["users"][str(user_id)] = user_data
    data["total_users"] += 1
    
    referrer_notified = False
    # রেফারারকে ক্রেডিট দেয় - ফিক্সড
    if referrer_id and str(referrer_id) in data["users"]:
        data["users"][str(referrer_id)]["credits"] += REFERRAL_REWARD
        data["users"][str(referrer_id)]["referrals"].append(user_id)
        data["users"][str(referrer_id)]["total_referrals"] += 1
        referrer_notified = True
        # রেফারারের ডেটা আপডেট করার পর সেভ করুন
        save_data(data)
    
    save_data(data)
    return user_data, referrer_id if referrer_id else None, referrer_notified

def update_user(user_id, key, value):
    data = load_data()
    if str(user_id) in data["users"]:
        data["users"][str(user_id)][key] = value
        save_data(data)

def add_credits(user_id, amount):
    data = load_data()
    uid = str(user_id)
    if uid in data["users"]:
        data["users"][uid]["credits"] += amount
        save_data(data)
        return True
    return False

# ==================== প্রোমো কোড ফাংশন ====================
def generate_promo_code(length=8):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def create_promo_code(code, credits, max_uses, created_by):
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

def use_promo_code(user_id, code):
    promo_data = load_promo_codes()
    
    if code not in promo_data:
        return False, "❌ ভুল প্রোমো কোড!"
    
    promo = promo_data[code]
    
    if promo["used_count"] >= promo["max_uses"]:
        return False, "❌ এই প্রোমো কোডটি আর ব্যবহার করা যায় না!"
    
    if str(user_id) in promo["users"]:
        return False, "❌ আপনি ইতিমধ্যে এই প্রোমো কোড ব্যবহার করেছেন!"
    
    if add_credits(user_id, promo["credits"]):
        promo["used_count"] += 1
        promo["users"].append(str(user_id))
        save_promo_codes(promo_data)
        
        user_data = get_user(user_id)
        if user_data:
            user_data["used_promos"].append(code)
            update_user(user_id, "used_promos", user_data["used_promos"])
        
        return True, f"✅ {promo['credits']} ক্রেডিট পেয়েছেন!"
    
    return False, "❌ কিছু সমস্যা হয়েছে!"

def delete_promo_code(code):
    promo_data = load_promo_codes()
    if code in promo_data:
        del promo_data[code]
        save_promo_codes(promo_data)
        return True
    return False

# ==================== চ্যানেল চেক ====================
async def is_user_member_all_channels(user_id):
    channels = load_channels()
    not_joined = []
    for channel in channels:
        try:
            chat_id = channel["id"]
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
            not_joined.append(channel)
    return len(not_joined) == 0, not_joined

# ==================== প্রফেশনাল UI বাটন ====================
def get_permanent_keyboard(user_id=None):
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
    
    keyboard.append([InlineKeyboardButton("👨‍💻 ডেভেলপার", url="https://t.me/nhbd_dev")])
    
    for channel in channels:
        keyboard.append([InlineKeyboardButton("📢 জয়েন চ্যানেল", url=channel["url"])])
    
    keyboard.append([InlineKeyboardButton(f"ℹ️ {BOT_NAME} {BOT_VERSION}", callback_data="about")])
    
    return InlineKeyboardMarkup(keyboard)

def get_prank_keyboard():
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

def get_admin_keyboard():
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

def get_channel_manage_keyboard():
    channels = load_channels()
    keyboard = []
    for i, channel in enumerate(channels):
        keyboard.append([
            InlineKeyboardButton(f"❌ {channel['id']}", callback_data=f"remove_channel_{i}")
        ])
    keyboard.append([InlineKeyboardButton("➕ নতুন চ্যানেল যোগ", callback_data="admin_add_channel")])
    keyboard.append([InlineKeyboardButton("🔙 অ্যাডমিন প্যানেলে", callback_data="admin_panel")])
    return InlineKeyboardMarkup(keyboard)

def get_promo_list_keyboard():
    promo_data = load_promo_codes()
    keyboard = []
    
    if promo_data:
        for code, info in list(promo_data.items())[:10]:
            status = "✅" if info["used_count"] < info["max_uses"] else "❌"
            keyboard.append([
                InlineKeyboardButton(
                    f"{status} {code} ({info['used_count']}/{info['max_uses']})", 
                    callback_data=f"promo_detail_{code}"
                )
            ])
    
    keyboard.append([InlineKeyboardButton("🗑️ প্রোমো ডিলিট", callback_data="admin_delete_promo")])
    keyboard.append([InlineKeyboardButton("🔙 অ্যাডমিন প্যানেলে", callback_data="admin_panel")])
    return InlineKeyboardMarkup(keyboard)

def get_about_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔙 হোম", callback_data="home")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== গ্লোবাল ====================
bot = None

# ==================== /admin কমান্ড ====================
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# ==================== হ্যান্ডলার ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot
    bot = context.bot
    user = update.effective_user
    user_id = user.id

    is_member, not_joined = await is_user_member_all_channels(user_id)
    if not is_member:
        join_buttons = []
        for channel in not_joined:
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
        # রেফারারকে নোটিফিকেশন - ফিক্সড
        if referrer:
            try:
                # রেফারারের আপডেটেড ডেটা
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
👥 মোট রেফার: {referrer_data['total_referrals']} জন
💳 বর্তমান ব্যালেন্স: {referrer_data['credits']} ক্রেডিট
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

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

        # ========== প্রোমো কোড তৈরি ==========
        if data == "admin_create_promo":
            context.user_data['admin_action'] = 'create_promo'
            await query.edit_message_text(
                f"""
🎁 **প্রোমো কোড তৈরি করুন**

━━━━━━━━━━━━━━━━━━━
📌 নিচের তথ্য দিন (স্পেস দিয়ে আলাদা):

**ফরম্যাট:** `প্রোমো কোড ক্রেডিট_সংখ্যা ম্যাক্স_ইউজ`

**উদাহরণ:** `PRANK2024 5 10`

🔹 কোড: PRANK2024
🔹 ক্রেডিট: ৫টি
🔹 ম্যাক্স ইউজ: ১০ জন

❌ বাতিল: /cancel
━━━━━━━━━━━━━━━━━━━
""",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="admin_panel")]]),
                parse_mode="Markdown"
            )
            return

        # ========== প্রোমো কোড তালিকা ==========
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
                status = "✅" if info["used_count"] < info["max_uses"] else "❌"
                text += f"""
{status} **{code}**
   💰 {info['credits']} ক্রেডিট
   👥 {info['used_count']}/{info['max_uses']} ইউজ
   📅 {info['created_at'][:10]}
━━━━━━━━━━━━━━━━━━━
"""
            await query.edit_message_text(text, reply_markup=get_promo_list_keyboard(), parse_mode="Markdown")
            return

        # ========== প্রোমো ডিটেইল ==========
        elif data.startswith("promo_detail_"):
            code = data.replace("promo_detail_", "")
            promo_data = load_promo_codes()
            if code in promo_data:
                info = promo_data[code]
                text = f"""
🎁 **প্রোমো কোড ডিটেইল**
━━━━━━━━━━━━━━━━━━━
📌 কোড: `{code}`
💰 ক্রেডিট: {info['credits']}
👥 ইউজ: {info['used_count']}/{info['max_uses']}
📅 তৈরি: {info['created_at']}
👤 তৈরি করেছেন: `{info['created_by']}`

**ব্যবহারকারী তালিকা:**
"""
                if info['users']:
                    for i, uid in enumerate(info['users'][:10], 1):
                        text += f"{i}. `{uid}`\n"
                    if len(info['users']) > 10:
                        text += f"... আরো {len(info['users']) - 10} জন"
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

        # ========== প্রোমো ডিলিট ==========
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

        # ========== অন্যান্য অ্যাডমিন অপশন ==========
        elif data == "admin_users":
            users = load_data()["users"]
            if not users:
                await query.edit_message_text("❌ **কোনো ইউজার নেই।**", reply_markup=get_admin_keyboard())
                return
            text = f"📊 **মোট ইউজার:** {len(users)}\n━━━━━━━━━━━━━━━━━━━\n\n"
            for i, (uid, udata) in enumerate(list(users.items())[:10], 1):
                text += f"{i}. 🆔 `{uid}`\n   💰 {udata['credits']} | 👥 {udata['total_referrals']}\n"
            if len(users) > 10:
                text += f"\n... আরো {len(users) - 10} জন"
            await query.edit_message_text(text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")
            return

        elif data == "admin_stats":
            data = load_data()
            users = data["users"]
            promo_data = load_promo_codes()
            total_users = len(users)
            total_credits = sum(u['credits'] for u in users.values())
            total_referrals = sum(u['total_referrals'] for u in users.values())
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
                text += f"{i}. 👤 `{cmt['user_id']}`:\n   💬 {cmt['comment'][:50]}\n"
            await query.edit_message_text(text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")
            return

        elif data == "admin_ratings":
            data = load_data()
            ratings = data.get("ratings", [])
            if not ratings:
                await query.edit_message_text("⭐ **এখনো কোনো রেটিং নেই।**", reply_markup=get_admin_keyboard())
                return
            avg = sum(int(r['rating']) for r in ratings) / len(ratings)
            text = f"""
⭐ **রেটিং স্ট্যাটাস**
━━━━━━━━━━━━━━━━━━━
📊 গড় রেটিং: {avg:.1f}/5
📊 মোট রেটিং: {len(ratings)}
━━━━━━━━━━━━━━━━━━━

**শেষ ৫টি রেটিং:**
"""
            for i, r in enumerate(ratings[-5:], 1):
                text += f"{i}. 👤 `{r['user_id']}`: {r['rating']}⭐\n"
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
            index = int(data.replace("remove_channel_", ""))
            channels = load_channels()
            if 0 <= index < len(channels):
                removed = channels.pop(index)
                save_channels(channels)
                await query.edit_message_text(
                    f"✅ **চ্যানেল রিমুভ করা হয়েছে!**\n\n"
                    f"🆔 আইডি: `{removed['id']}`",
                    reply_markup=get_channel_manage_keyboard(),
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text("❌ **চ্যানেল পাওয়া যায়নি!**", reply_markup=get_channel_manage_keyboard())
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
• 8810 - গার্লফ্রেন্ড
• 8805 - দুর্গন্ধ
• 8808 - ওয়াই-ফাই
• 8809 - কেন কল?
• 8803 - পিজ্জা
• 8804 - ট্যাক্সি
• 8806 - হৈচৈ
• 8807 - কুকুর

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
📝 টাইটেল: {PRANK_IDS.get(prank_id)}

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
💰 ক্রেডিট: {user_data['credits']}
👥 রেফার: {user_data['total_referrals']} জন
📊 টোটাল ইউজার: {load_data()['total_users']} জন
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
👥 মোট রেফার: {user_data['total_referrals']} জন
"""
        if user_data['referrals']:
            text += f"\n📋 **রেফার তালিকা:**\n"
            for idx, ref_id in enumerate(user_data['referrals'][:10], 1):
                text += f"{idx}. `{ref_id}`\n"
            if len(user_data['referrals']) > 10:
                text += f"... আরো {len(user_data['referrals']) - 10} জন"
        
        text += "\n━━━━━━━━━━━━━━━━━━━"
        await query.edit_message_text(text, reply_markup=get_permanent_keyboard(user_id), parse_mode="Markdown")
        return

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            await update.message.reply_text(
                f"""
🎉 **প্রোমো কোড সফল!**

━━━━━━━━━━━━━━━━━━━
{message}
💳 **নতুন ব্যালেন্স:** {get_user(user_id)['credits']} ক্রেডিট
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
💰 নতুন ব্যালেন্স: {get_user(user_id)['credits']}
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

        if user_data['credits'] <= 0:
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
            f"📝 {PRANK_IDS.get(prank_id)}\n\n"
            f"দয়া করে অপেক্ষা করুন...",
            parse_mode="Markdown"
        )
        
        try:
            api_url = f"{PRANK_API_URL}?number={clean_number}&prank={prank_id}"
            response = requests.get(api_url, timeout=30)
            result = response.text
            user_data['credits'] -= 1
            update_user(user_id, "credits", user_data['credits'])
            
            await msg.edit_text(
                f"✅ **প্রাঙ্ক কল সম্পন্ন!**\n\n"
                f"📱 {clean_number}\n"
                f"🆔 {prank_id}\n"
                f"📊 {result[:200]}\n\n"
                f"💰 বাকি ক্রেডিট: {user_data['credits']}",
                reply_markup=get_permanent_keyboard(user_id),
                parse_mode="Markdown"
            )
        except Exception as e:
            await msg.edit_text(
                f"❌ **ত্রুটি!**\n\n{str(e)}",
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
                if str(uid) in data["users"]:
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
            users = load_data()["users"]
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

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Error: {context.error}")

# ==================== মেইন ====================
def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
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

if __name__ == "__main__":
    import asyncio
    main()