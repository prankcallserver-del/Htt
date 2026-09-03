import os
import json
import logging
import requests
import re
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

# ==================== ডেটাবেস ====================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "total_users": 0}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": {}, "total_users": 0}

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

def get_user(user_id):
    data = load_data()
    return data["users"].get(str(user_id))

def create_user(user_id, referrer_id=None):
    data = load_data()
    user_data = {
        "credits": INITIAL_CREDITS,
        "referrals": [],
        "referrer": referrer_id,
        "total_referrals": 0
    }
    data["users"][str(user_id)] = user_data
    data["total_users"] += 1
    
    referrer_notified = False
    if referrer_id and str(referrer_id) in data["users"]:
        data["users"][str(referrer_id)]["credits"] += REFERRAL_REWARD
        data["users"][str(referrer_id)]["referrals"].append(user_id)
        data["users"][str(referrer_id)]["total_referrals"] += 1
        referrer_notified = True
    
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

# ==================== পার্মানেন্ট বাটন (এখনও নিচে থাকবে) ====================
def get_permanent_keyboard():
    channels = load_channels()
    keyboard = [
        [InlineKeyboardButton("🏠 হোম", callback_data="home")],
        [InlineKeyboardButton("👤 প্রোফাইল", callback_data="profile")],
        [InlineKeyboardButton("📢 রেফার লিংক", callback_data="refer")],
        [InlineKeyboardButton("📞 প্রাঙ্ক কল", callback_data="prank_menu")],
        [InlineKeyboardButton("👨‍💻 ডেভেলপার", url="https://t.me/nhbd_dev")],
    ]
    for channel in channels:
        keyboard.append([InlineKeyboardButton("📢 জয়েন চ্যানেল", url=channel["url"])])
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
    keyboard.append([InlineKeyboardButton("🔙 ব্যাক", callback_data="home")])
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 ইউজার তালিকা", callback_data="admin_users")],
        [InlineKeyboardButton("💰 ক্রেডিট দেয়", callback_data="admin_add_credit")],
        [InlineKeyboardButton("✏️ রেফার পয়েন্ট এডিট", callback_data="admin_edit_refer")],
        [InlineKeyboardButton("📢 ব্রডকাস্ট", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📋 কমেন্ট দেখুন", callback_data="admin_comments")],
        [InlineKeyboardButton("📊 রেটিং দেখুন", callback_data="admin_ratings")],
        [InlineKeyboardButton("📢 চ্যানেল ম্যানেজ", callback_data="admin_channels")],
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
    keyboard.append([InlineKeyboardButton("➕ চ্যানেল যোগ", callback_data="admin_add_channel")])
    keyboard.append([InlineKeyboardButton("🔙 ব্যাক", callback_data="admin_panel")])
    return InlineKeyboardMarkup(keyboard)

# ==================== গ্লোবাল ====================
bot = None

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
        welcome_text = f"🎉 **স্বাগতম {user.first_name}!**\n\n"
        welcome_text += f"🤖 **{BOT_NAME}**-এ আপনাকে স্বাগতম!\n"
        welcome_text += f"💰 আপনি {INITIAL_CREDITS}টি ফ্রি ক্রেডিট পেয়েছেন!\n"
        if referrer:
            welcome_text += f"✅ আপনি {REFERRAL_REWARD}টি বোনাস ক্রেডিট পেয়েছেন!\n"
            try:
                await bot.send_message(
                    chat_id=referrer,
                    text=f"🎉 **নতুন রেফার!**\n\nআপনার রেফার লিংক থেকে {user.first_name} জয়েন করেছেন!\n💰 আপনি {REFERRAL_REWARD}টি ক্রেডিট পেয়েছেন!",
                    parse_mode="Markdown",
                    reply_markup=get_permanent_keyboard()
                )
            except Exception as e:
                logging.error(f"রেফার নোটিফিকেশন এরর: {e}")
        welcome_text += "\nনিচের মেনু থেকে অপশন নির্বাচন করুন:"
    else:
        welcome_text = f"👋 **স্বাগতম kembali {user.first_name}!**\n\nনিচের মেনু থেকে অপশন নির্বাচন করুন:"

    await update.message.reply_text(
        welcome_text,
        reply_markup=get_permanent_keyboard(),
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
    if data != "check_join" and not data.startswith("admin"):
        is_member, not_joined = await is_user_member_all_channels(user_id)
        if not is_member:
            join_buttons = []
            for channel in not_joined:
                join_buttons.append([InlineKeyboardButton("📢 জয়েন চ্যানেল", url=channel["url"])])
            join_buttons.append([InlineKeyboardButton("✅ চেক করুন", callback_data="check_join")])
            await query.edit_message_text(
                "⚠️ সব চ্যানেলে জয়েন করুন!",
                reply_markup=InlineKeyboardMarkup(join_buttons),
                parse_mode="Markdown"
            )
            return

    if data == "check_join":
        is_member, not_joined = await is_user_member_all_channels(user_id)
        if is_member:
            await query.edit_message_text(
                "✅ সব চ্যানেলে জয়েন করেছেন!",
                reply_markup=get_permanent_keyboard(),
                parse_mode="Markdown"
            )
        else:
            join_buttons = []
            for channel in not_joined:
                join_buttons.append([InlineKeyboardButton("📢 জয়েন চ্যানেল", url=channel["url"])])
            join_buttons.append([InlineKeyboardButton("✅ চেক করুন", callback_data="check_join")])
            await query.edit_message_text(
                "❌ কিছু চ্যানেলে জয়েন করেননি!",
                reply_markup=InlineKeyboardMarkup(join_buttons),
                parse_mode="Markdown"
            )
        return

    # ==================== যদি ইউজার অ্যাডমিন হয় ====================
    if user_id in ADMIN_IDS:
        if data == "home":
            await query.edit_message_text(
                "🏠 **হোম**\n\nবট ব্যবহারের জন্য নিচের অপশন থেকে নির্বাচন করুন:",
                reply_markup=get_permanent_keyboard(),
                parse_mode="Markdown"
            )
            return

        # অ্যাডমিন প্যানেল চালু
        if data.startswith("admin"):
            if data == "admin_panel":
                await query.edit_message_text(
                    "👑 **অ্যাডমিন প্যানেল**\n\nনিচের অপশন থেকে নির্বাচন করুন:",
                    reply_markup=get_admin_keyboard(),
                    parse_mode="Markdown"
                )
                return

            elif data == "admin_users":
                users = load_data()["users"]
                if not users:
                    await query.edit_message_text("❌ কোনো ইউজার নেই।", reply_markup=get_admin_keyboard())
                    return
                text = f"📊 **মোট ইউজার:** {len(users)}\n\n"
                for i, (uid, udata) in enumerate(list(users.items())[:10], 1):
                    text += f"{i}. `{uid}` | 💰{udata['credits']} | 👥{udata['total_referrals']}\n"
                if len(users) > 10:
                    text += f"\n... আরো {len(users) - 10} জন"
                await query.edit_message_text(text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")
                return

            elif data == "admin_add_credit":
                context.user_data['admin_action'] = 'add_credit'
                await query.edit_message_text(
                    "💰 **ক্রেডিট দেয়**\n\nইউজার আইডি ও ক্রেডিট লিখুন:\nউদাহরণ: `1849126202 10`",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="admin_panel")]]),
                    parse_mode="Markdown"
                )
                return

            elif data == "admin_edit_refer":
                context.user_data['admin_action'] = 'edit_refer'
                await query.edit_message_text(
                    "✏️ **রেফার পয়েন্ট এডিট**\n\nইউজার আইডি ও পয়েন্ট লিখুন:\nউদাহরণ: `1849126202 10`",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="admin_panel")]]),
                    parse_mode="Markdown"
                )
                return

            elif data == "admin_broadcast":
                context.user_data['admin_action'] = 'broadcast'
                await query.edit_message_text(
                    "📢 **ব্রডকাস্ট**\n\nসব ইউজারকে মেসেজ লিখুন:",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="admin_panel")]]),
                    parse_mode="Markdown"
                )
                return

            elif data == "admin_comments":
                data = load_data()
                comments = data.get("comments", [])
                if not comments:
                    await query.edit_message_text("📭 এখনো কোনো কমেন্ট নেই।", reply_markup=get_admin_keyboard())
                    return
                text = f"📋 **মোট কমেন্ট:** {len(comments)}\n\n"
                for i, cmt in enumerate(comments[-10:], 1):
                    text += f"{i}. 👤 `{cmt['user_id']}`: {cmt['comment'][:50]}\n"
                await query.edit_message_text(text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")
                return

            elif data == "admin_ratings":
                data = load_data()
                ratings = data.get("ratings", [])
                if not ratings:
                    await query.edit_message_text("⭐ এখনো কোনো রেটিং নেই।", reply_markup=get_admin_keyboard())
                    return
                avg = sum(int(r['rating']) for r in ratings) / len(ratings)
                text = f"⭐ **গড় রেটিং:** {avg:.1f}/5\n📊 **মোট রেটিং:** {len(ratings)}\n\n"
                for i, r in enumerate(ratings[-5:], 1):
                    text += f"{i}. 👤 `{r['user_id']}`: {r['rating']}⭐\n"
                await query.edit_message_text(text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")
                return

            elif data == "admin_channels":
                await query.edit_message_text(
                    "📢 **চ্যানেল ম্যানেজ**\n\nনিচের অপশন থেকে নির্বাচন করুন:",
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
                        f"✅ চ্যানেল `{removed['id']}` রিমুভ করা হয়েছে!",
                        reply_markup=get_channel_manage_keyboard(),
                        parse_mode="Markdown"
                    )
                else:
                    await query.edit_message_text("❌ চ্যানেল পাওয়া যায়নি!", reply_markup=get_channel_manage_keyboard())
                return

            elif data == "admin_add_channel":
                context.user_data['admin_action'] = 'add_channel'
                await query.edit_message_text(
                    "➕ **চ্যানেল যোগ করুন**\n\nচ্যানেল আইডি লিখুন:\nপাবলিক: @username\nপ্রাইভেট: -100xxxxxxxxxx\n\nউদাহরণ: `-1003256463633`",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="admin_channels")]]),
                    parse_mode="Markdown"
                )
                context.user_data['waiting_channel_id'] = True
                return

    # ==================== সাধারণ ইউজার মেনু ====================
    if data == "prank_menu":
        await query.edit_message_text(
            "📞 **প্রাঙ্ক কল**\n\nনিচ থেকে প্রাঙ্ক আইডি নির্বাচন করুন:\n\n"
            "🎭 8810 - গার্লফ্রেন্ড\n🎭 8805 - দুর্গন্ধ\n🎭 8808 - ওয়াই-ফাই\n"
            "🎭 8809 - কেন কল?\n🎭 8803 - পিজ্জা\n🎭 8804 - ট্যাক্সি\n"
            "🎭 8806 - হৈচৈ\n🎭 8807 - কুকুর\n\n💰 প্রতি কল = ১ ক্রেডিট\n\nআইডি নির্বাচন করুন, তারপর নাম্বার দিন:",
            reply_markup=get_prank_keyboard(),
            parse_mode="Markdown"
        )
        return

    elif data.startswith("prank_"):
        prank_id = data.replace("prank_", "")
        context.user_data['selected_prank'] = prank_id
        await query.edit_message_text(
            f"📱 **নাম্বার দিন**\n\nপ্রাঙ্ক আইডি: `{prank_id}`\nটাইটেল: {PRANK_IDS.get(prank_id)}\n\nনাম্বার লিখুন:\nউদাহরণ: `01712345678`\n\n❌ বাতিল: /cancel",
            parse_mode="Markdown"
        )
        context.user_data['waiting_number'] = True
        return

    elif data == "profile":
        user_data = get_user(user_id)
        if not user_data:
            user_data, _, _ = create_user(user_id)
        text = f"👤 **প্রোফাইল**\n\n🆔 আইডি: `{user_id}`\n💰 ক্রেডিট: {user_data['credits']}\n👥 রেফার: {user_data['total_referrals']} জন\n📊 টোটাল ইউজার: {load_data()['total_users']} জন"
        await query.edit_message_text(text, reply_markup=get_permanent_keyboard(), parse_mode="Markdown")
        return

    elif data == "refer":
        user_data = get_user(user_id)
        if not user_data:
            user_data, _, _ = create_user(user_id)
        text = f"📢 **রেফার লিংক**\n\nপ্রতি রেফারে {REFERRAL_REWARD} ক্রেডিট!\n\n🔗 `https://t.me/{BOT_USERNAME.replace('@', '')}?start={user_id}`\n\n👥 রেফার: {user_data['total_referrals']} জন\n"
        if user_data['referrals']:
            text += f"\n📋 রেফার তালিকা:\n"
            for idx, ref_id in enumerate(user_data['referrals'][:10], 1):
                text += f"{idx}. `{ref_id}`\n"
            if len(user_data['referrals']) > 10:
                text += f"... আরো {len(user_data['referrals']) - 10} জন"
        await query.edit_message_text(text, reply_markup=get_permanent_keyboard(), parse_mode="Markdown")
        return

    # ==================== যদি কেউ অন্য কিছু ক্লিক করে ====================
    await query.edit_message_text(
        "🏠 **হোম**\n\nবট ব্যবহারের জন্য নিচের অপশন থেকে নির্বাচন করুন:",
        reply_markup=get_permanent_keyboard(),
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # চ্যানেল আইডি ইনপুট
    if context.user_data.get('waiting_channel_id'):
        channel_id = text
        context.user_data['temp_channel_id'] = channel_id
        context.user_data['waiting_channel_id'] = False
        context.user_data['waiting_channel_url'] = True
        await update.message.reply_text(
            "✅ চ্যানেল আইডি সেভ করা হয়েছে!\n\nএখন চ্যানেলের URL দিন:\nউদাহরণ: `https://t.me/+kRLScHkVvpllYWQ1`",
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
            f"✅ **চ্যানেল যোগ করা হয়েছে!**\n\n🆔 আইডি: `{channel_id}`\n🔗 URL: {channel_url}",
            reply_markup=get_admin_keyboard(),
            parse_mode="Markdown"
        )
        return

    # নাম্বার ইনপুট
    if context.user_data.get('waiting_number'):
        if text.lower() == '/cancel':
            context.user_data['waiting_number'] = False
            context.user_data['selected_prank'] = None
            await update.message.reply_text("❌ বাতিল!", reply_markup=get_permanent_keyboard(), parse_mode="Markdown")
            return

        clean_number = re.sub(r'[\s\-\(\)]', '', text)
        if not re.match(r'^\+?[0-9]{10,15}$', clean_number):
            await update.message.reply_text("❌ **ভুল নাম্বার!**\n\nসঠিক ফরম্যাট: `01712345678`", parse_mode="Markdown")
            return

        prank_id = context.user_data.get('selected_prank')
        if not prank_id:
            await update.message.reply_text("❌ প্রাঙ্ক আইডি নির্বাচন করুন!", reply_markup=get_permanent_keyboard(), parse_mode="Markdown")
            context.user_data['waiting_number'] = False
            return

        user_data = get_user(user_id)
        if not user_data:
            user_data, _, _ = create_user(user_id)

        if user_data['credits'] <= 0:
            await update.message.reply_text("❌ **ক্রেডিট নেই!**\nরেফার করে সংগ্রহ করুন।", reply_markup=get_permanent_keyboard(), parse_mode="Markdown")
            context.user_data['waiting_number'] = False
            context.user_data['selected_prank'] = None
            return

        msg = await update.message.reply_text(f"⏳ কল হচ্ছে...\n📱 {clean_number}\n🆔 {prank_id}", parse_mode="Markdown")
        try:
            api_url = f"{PRANK_API_URL}?number={clean_number}&prank={prank_id}"
            response = requests.get(api_url, timeout=30)
            result = response.text
            user_data['credits'] -= 1
            update_user(user_id, "credits", user_data['credits'])
            await msg.edit_text(
                f"✅ **প্রাঙ্ক কল সম্পন্ন!**\n\n📱 {clean_number}\n🆔 {prank_id}\n📊 {result[:200]}\n\n💰 বাকি: {user_data['credits']}",
                reply_markup=get_permanent_keyboard(),
                parse_mode="Markdown"
            )
        except Exception as e:
            await msg.edit_text(f"❌ **ত্রুটি!**\n{str(e)}", reply_markup=get_permanent_keyboard(), parse_mode="Markdown")

        context.user_data['waiting_number'] = False
        context.user_data['selected_prank'] = None
        return

    # অ্যাডমিন ইনপুট
    if user_id in ADMIN_IDS:
        action = context.user_data.get('admin_action')
        if not action:
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
                    await update.message.reply_text(f"✅ `{uid}`-কে {amount} ক্রেডিট দেওয়া হয়েছে!", reply_markup=get_admin_keyboard(), parse_mode="Markdown")
                else:
                    await update.message.reply_text("❌ ইউজার পাওয়া যায়নি!", reply_markup=get_admin_keyboard())
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
                    await update.message.reply_text(f"✅ `{uid}`-এর রেফার পয়েন্ট {points} করা হয়েছে!", reply_markup=get_admin_keyboard(), parse_mode="Markdown")
                else:
                    await update.message.reply_text("❌ ইউজার পাওয়া যায়নি!", reply_markup=get_admin_keyboard())
            except:
                await update.message.reply_text("❌ ভুল ফরম্যাট!", parse_mode="Markdown")
            context.user_data['admin_action'] = None

        elif action == 'broadcast':
            users = load_data()["users"]
            success = 0
            await update.message.reply_text("📤 ব্রডকাস্ট শুরু...")
            for uid in users:
                try:
                    await context.bot.send_message(
                        chat_id=int(uid),
                        text=f"📢 **অ্যাডমিন বার্তা**\n\n{text}",
                        parse_mode="Markdown",
                        reply_markup=get_permanent_keyboard()
                    )
                    success += 1
                except:
                    pass
            await update.message.reply_text(f"✅ {success} জন পেয়েছে!", reply_markup=get_admin_keyboard())
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
    application.add_handler(CommandHandler("cancel", handle_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_error_handler(error_handler)
    
    print(f"🤖 {BOT_NAME} চালু!")
    print(f"📢 চ্যানেল: {len(load_channels())}টি")
    print(f"👑 অ্যাডমিন: {ADMIN_IDS}")
    print(f"🔗 বট ইউজারনেম: {BOT_USERNAME}")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    import asyncio
    main()
