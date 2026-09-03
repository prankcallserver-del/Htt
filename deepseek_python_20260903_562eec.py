import os
import json
import logging
import requests
import re
from typing import Dict, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# ==================== কনফিগারেশন ====================
BOT_TOKEN = "8879701783:AAHTfTgDWT3HWnlc1xCRgYeHu_MGolCMx5E"
ADMIN_IDS = [1849126202]  # আপনার টেলিগ্রাম আইডি দিন
 
# ===== চ্যানেল কনফিগারেশন =====
FORCE_CHANNEL = "-1003256463633"  # চ্যানেল আইডি বা ইউজারনেম
FORCE_CHANNEL_URL = "https://t.me/+ENYrQ5N9WNE3NWQ9"

BOT_NAME = "NHBD PRANK HUB"
BOT_USERNAME = "@Testujnch_bot"

INITIAL_CREDITS = 2
REFERRAL_REWARD = 2

# প্রাঙ্ক কল API
PRANK_API_URL = "https://api-lilac-seven-58.vercel.app/api.php"

# প্রাঙ্ক আইডি লিস্ট
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

# ==================== কনভারসেশন স্টেট ====================
WAITING_NUMBER = 1
WAITING_PRANK_ID = 2

# ==================== ডেটাবেস ====================
DATA_FILE = "data.json"

def load_data() -> Dict:
    if not os.path.exists(DATA_FILE):
        return {"users": {}, "total_users": 0}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": {}, "total_users": 0}

def save_data(data: Dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_user(user_id: int) -> Optional[Dict]:
    data = load_data()
    return data["users"].get(str(user_id))

def create_user(user_id: int, referrer_id: Optional[int] = None) -> Dict:
    data = load_data()
    user_data = {
        "credits": INITIAL_CREDITS,
        "referrals": [],
        "referrer": referrer_id,
        "joined_channel": False,
        "total_referrals": 0
    }
    data["users"][str(user_id)] = user_data
    data["total_users"] += 1
    
    # রেফারারকে ক্রেডিট ও নোটিফিকেশন দেয়
    if referrer_id and str(referrer_id) in data["users"]:
        data["users"][str(referrer_id)]["credits"] += REFERRAL_REWARD
        data["users"][str(referrer_id)]["referrals"].append(user_id)
        data["users"][str(referrer_id)]["total_referrals"] += 1
        save_data(data)
        
        # রেফারারকে নোটিফিকেশন পাঠানোর জন্য ডেটা সেভ করি
        return user_data, referrer_id
    
    save_data(data)
    return user_data, None

def update_user(user_id: int, key: str, value) -> None:
    data = load_data()
    if str(user_id) in data["users"]:
        data["users"][str(user_id)][key] = value
        save_data(data)

def add_credits(user_id: int, amount: int) -> bool:
    data = load_data()
    uid = str(user_id)
    if uid in data["users"]:
        data["users"][uid]["credits"] += amount
        save_data(data)
        return True
    return False

# ==================== চ্যানেল চেক ====================
async def is_user_member(user_id: int) -> bool:
    try:
        chat_id = FORCE_CHANNEL
        if FORCE_CHANNEL.startswith("@"):
            chat_id = FORCE_CHANNEL
        else:
            try:
                chat_id = int(FORCE_CHANNEL)
            except ValueError:
                chat_id = FORCE_CHANNEL
        
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logging.error(f"চ্যানেল চেক এরর: {e}")
        return False

# ==================== পার্মানেন্ট বাটন ====================
def get_permanent_keyboard():
    """পার্মানেন্ট বাটন (সব জায়গায় নিচে থাকবে)"""
    keyboard = [
        [InlineKeyboardButton("🏠 হোম", callback_data="home")],
        [InlineKeyboardButton("👤 প্রোফাইল", callback_data="profile")],
        [InlineKeyboardButton("📢 রেফার লিংক", callback_data="refer")],
        [InlineKeyboardButton("📞 প্রাঙ্ক কল", callback_data="prank_menu")],
        [InlineKeyboardButton("👨‍💻 ডেভেলপার", url="https://t.me/your_username")],
        [InlineKeyboardButton("📢 জয়েন ফোর্স চ্যানেল", url=FORCE_CHANNEL_URL)]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_prank_keyboard():
    """প্রাঙ্ক আইডি বাটন"""
    keyboard = []
    row = []
    for i, (prank_id, title) in enumerate(PRANK_IDS.items(), 1):
        button_text = f"{prank_id}"
        row.append(InlineKeyboardButton(button_text, callback_data=f"prank_{prank_id}"))
        
        if i % 4 == 0:  # প্রতি ৪টি বাটন পর লাইন ব্রেক
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    # ব্যাক বাটন
    keyboard.append([InlineKeyboardButton("🔙 ব্যাক", callback_data="home")])
    
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 ইউজার তালিকা", callback_data="admin_users")],
        [InlineKeyboardButton("💰 ক্রেডিট দেয়", callback_data="admin_add_credit")],
        [InlineKeyboardButton("✏️ রেফার পয়েন্ট এডিট", callback_data="admin_edit_refer")],
        [InlineKeyboardButton("📢 ব্রডকাস্ট", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔙 ব্যাক", callback_data="home")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== গ্লোবাল ====================
bot = None

# ==================== হ্যান্ডলার ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot
    bot = context.bot
    
    user = update.effective_user
    user_id = user.id
    
    if not await is_user_member(user_id):
        await update.message.reply_text(
            f"⚠️ **{BOT_NAME}** ব্যবহার করতে চ্যানেলে জয়েন করুন!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 জয়েন ফোর্স চ্যানেল", url=FORCE_CHANNEL_URL)],
                [InlineKeyboardButton("✅ চেক করুন", callback_data="check_join")]
            ]),
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
        user_data, referrer = create_user(user_id, referrer_id)
        
        welcome_text = f"🎉 **স্বাগতম {user.first_name}!**\n\n"
        welcome_text += f"🤖 **{BOT_NAME}**-এ আপনাকে স্বাগতম!\n"
        welcome_text += f"💰 আপনি {INITIAL_CREDITS}টি ফ্রি ক্রেডিট পেয়েছেন!\n"
        
        if referrer:
            welcome_text += f"✅ আপনি {REFERRAL_REWARD}টি বোনাস ক্রেডিট পেয়েছেন রেফারের জন্য!\n"
            
            # রেফারারকে নোটিফিকেশন পাঠাই
            try:
                await bot.send_message(
                    chat_id=referrer,
                    text=f"🎉 **নতুন রেফার!**\n\n"
                         f"আপনার রেফার লিংক থেকে {user.first_name} বটে জয়েন করেছেন!\n"
                         f"🆔 ইউজার আইডি: `{user_id}`\n"
                         f"💰 আপনি {REFERRAL_REWARD}টি ক্রেডিট পেয়েছেন!\n"
                         f"👥 আপনার মোট রেফার: {user_data['total_referrals']} জন",
                    parse_mode="Markdown",
                    reply_markup=get_permanent_keyboard()
                )
            except Exception as e:
                logging.error(f"রেফার নোটিফিকেশন পাঠাতে ব্যর্থ: {e}")
        
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
    
    if data != "check_join" and not await is_user_member(user_id):
        await query.edit_message_text(
            "⚠️ **আপনি চ্যানেলে জয়েন করেননি!**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 জয়েন ফোর্স চ্যানেল", url=FORCE_CHANNEL_URL)],
                [InlineKeyboardButton("✅ চেক করুন", callback_data="check_join")]
            ]),
            parse_mode="Markdown"
        )
        return
    
    if data == "check_join":
        if await is_user_member(user_id):
            await query.edit_message_text(
                "✅ **আপনি চ্যানেলে জয়েন করেছেন!**",
                reply_markup=get_permanent_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "❌ **আপনি এখনো চ্যানেলে জয়েন করেননি!**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📢 জয়েন ফোর্স চ্যানেল", url=FORCE_CHANNEL_URL)],
                    [InlineKeyboardButton("✅ চেক করুন", callback_data="check_join")]
                ]),
                parse_mode="Markdown"
            )
        return
    
    elif data == "home":
        await query.edit_message_text(
            "🏠 **হোম**\n\nবট ব্যবহারের জন্য নিচের অপশন থেকে নির্বাচন করুন:",
            reply_markup=get_permanent_keyboard(),
            parse_mode="Markdown"
        )
    
    elif data == "prank_menu":
        await query.edit_message_text(
            "📞 **প্রাঙ্ক কল**\n\n"
            "নিচ থেকে আপনার পছন্দের প্রাঙ্ক আইডি নির্বাচন করুন:\n\n"
            "📝 প্রতিটি প্রাঙ্কের টাইটেল:\n"
            "• 8810 - গার্লফ্রেন্ড\n"
            "• 8805 - দুর্গন্ধ\n"
            "• 8808 - ওয়াই-ফাই চুরি\n"
            "• 8809 - কেন কল?\n"
            "• 8803 - পিজ্জা\n"
            "• 8804 - ট্যাক্সি\n"
            "• 8806 - হৈচৈ\n"
            "• 8807 - কুকুর\n\n"
            "💰 প্রতি কলেই ১টি ক্রেডিট খরচ হবে।\n\n"
            "প্রথমে আপনার পছন্দের প্রাঙ্ক আইডি নির্বাচন করুন, তারপর নাম্বার দিন।",
            reply_markup=get_prank_keyboard(),
            parse_mode="Markdown"
        )
    
    elif data.startswith("prank_"):
        prank_id = data.replace("prank_", "")
        context.user_data['selected_prank'] = prank_id
        
        # নাম্বার ইনপুট চাওয়া
        await query.edit_message_text(
            f"📱 **নাম্বার দিন**\n\n"
            f"আপনি প্রাঙ্ক আইডি `{prank_id}` নির্বাচন করেছেন।\n\n"
            f"এখন যে নাম্বারে প্রাঙ্ক কল করতে চান সেটি লিখুন:\n\n"
            f"উদাহরণ: `01712345678` অথবা `+8801712345678`\n\n"
            f"❌ বাতিল করতে /cancel টাইপ করুন।",
            parse_mode="Markdown"
        )
        context.user_data['waiting_number'] = True
        return
    
    elif data == "profile":
        user_data = get_user(user_id)
        if not user_data:
            user_data = create_user(user_id)[0]
        
        text = f"👤 **আপনার প্রোফাইল**\n\n"
        text += f"🆔 আইডি: `{user_id}`\n"
        text += f"💰 ক্রেডিট: {user_data['credits']}\n"
        text += f"👥 রেফার: {user_data['total_referrals']} জন\n"
        text += f"📊 টোটাল ইউজার: {load_data()['total_users']} জন"
        
        await query.edit_message_text(
            text,
            reply_markup=get_permanent_keyboard(),
            parse_mode="Markdown"
        )
    
    elif data == "refer":
        user_data = get_user(user_id)
        if not user_data:
            user_data = create_user(user_id)[0]
        
        text = f"📢 **রেফার লিংক**\n\n"
        text += f"আপনার বন্ধুদের আমন্ত্রণ জানান এবং প্রতি রেফারে {REFERRAL_REWARD}টি ক্রেডিট পান!\n\n"
        text += f"🔗 লিংক: `https://t.me/{BOT_USERNAME.replace('@', '')}?start={user_id}`\n\n"
        text += f"👥 আপনি {user_data['total_referrals']} জনকে রেফার করেছেন।\n\n"
        text += f"📋 রেফার তালিকা:\n"
        
        if user_data['referrals']:
            for idx, ref_id in enumerate(user_data['referrals'][:10], 1):
                text += f"{idx}. 🆔 `{ref_id}`\n"
            if len(user_data['referrals']) > 10:
                text += f"... এবং আরো {len(user_data['referrals']) - 10} জন"
        else:
            text += "❌ এখনো কোনো রেফার নেই।"
        
        await query.edit_message_text(
            text,
            reply_markup=get_permanent_keyboard(),
            parse_mode="Markdown"
        )
    
    # ==================== অ্যাডমিন প্যানেল ====================
    elif data.startswith("admin"):
        if user_id not in ADMIN_IDS:
            await query.edit_message_text("⛔ **আপনি অ্যাডমিন নন!**", reply_markup=get_permanent_keyboard(), parse_mode="Markdown")
            return
        
        if data == "admin_panel" or data == "admin_back":
            await query.edit_message_text(
                "👑 **অ্যাডমিন প্যানEL**\n\nনিচের অপশন থেকে নির্বাচন করুন:",
                reply_markup=get_admin_keyboard(),
                parse_mode="Markdown"
            )
        
        elif data == "admin_users":
            users = load_data()["users"]
            if not users:
                await query.edit_message_text("❌ এখনো কোনো ইউজার নেই।", reply_markup=get_admin_keyboard())
                return
            
            text = f"📊 **মোট ইউজার:** {len(users)}\n\n"
            for i, (uid, udata) in enumerate(list(users.items())[:10], 1):
                text += f"{i}. 🆔 `{uid}` | 💰 {udata['credits']} | 👥 {udata['total_referrals']}\n"
            
            if len(users) > 10:
                text += f"\n... এবং আরো {len(users) - 10} জন"
            
            await query.edit_message_text(text, reply_markup=get_admin_keyboard(), parse_mode="Markdown")
        
        elif data == "admin_add_credit":
            context.user_data['admin_action'] = 'add_credit'
            await query.edit_message_text(
                "💰 **ক্রেডিট দেয়**\n\nইউজার আইডি ও ক্রেডিট সংখ্যা লিখুন:\nউদাহরণ: `123456789 5`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="admin_panel")]]),
                parse_mode="Markdown"
            )
        
        elif data == "admin_edit_refer":
            context.user_data['admin_action'] = 'edit_refer'
            await query.edit_message_text(
                "✏️ **রেফার পয়েন্ট এডিট**\n\nইউজার আইডি ও নতুন পয়েন্ট লিখুন:\nউদাহরণ: `123456789 10`",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="admin_panel")]]),
                parse_mode="Markdown"
            )
        
        elif data == "admin_broadcast":
            context.user_data['admin_action'] = 'broadcast'
            await query.edit_message_text(
                "📢 **ব্রডকাস্ট**\n\nসব ইউজারকে পাঠানোর মেসেজ লিখুন:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 ব্যাক", callback_data="admin_panel")]]),
                parse_mode="Markdown"
            )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """মেসেজ হ্যান্ডলার"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # কাস্টম নাম্বার ইনপুট
    if context.user_data.get('waiting_number'):
        if text.lower() == '/cancel':
            context.user_data['waiting_number'] = False
            context.user_data['selected_prank'] = None
            await update.message.reply_text(
                "❌ **বাতিল করা হয়েছে!**",
                reply_markup=get_permanent_keyboard(),
                parse_mode="Markdown"
            )
            return
        
        # নাম্বার ভ্যালিডেশন
        clean_number = re.sub(r'[\s\-\(\)]', '', text)
        if not re.match(r'^\+?[0-9]{10,15}$', clean_number):
            await update.message.reply_text(
                "❌ **ভুল নাম্বার ফরম্যাট!**\n\n"
                "সঠিক ফরম্যাটে নাম্বার দিন:\n"
                "উদাহরণ: `01712345678` অথবা `+8801712345678`\n\n"
                "আবার চেষ্টা করুন অথবা /cancel দিন।",
                parse_mode="Markdown"
            )
            return
        
        # প্রাঙ্ক কল করুন
        prank_id = context.user_data.get('selected_prank')
        if not prank_id:
            await update.message.reply_text(
                "❌ **প্রথমে প্রাঙ্ক আইডি নির্বাচন করুন!**",
                reply_markup=get_permanent_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['waiting_number'] = False
            return
        
        prank_title = PRANK_IDS.get(prank_id, "অজানা প্রাঙ্ক")
        
        user_data = get_user(user_id)
        if not user_data:
            user_data = create_user(user_id)[0]
        
        if user_data['credits'] <= 0:
            await update.message.reply_text(
                "❌ **পর্যাপ্ত ক্রেডিট নেই!**\n\n"
                "আপনার কাছে কোনো ক্রেডিট নেই। রেফার করে ক্রেডিট সংগ্রহ করুন।",
                reply_markup=get_permanent_keyboard(),
                parse_mode="Markdown"
            )
            context.user_data['waiting_number'] = False
            context.user_data['selected_prank'] = None
            return
        
        # প্রক্রিয়াকরণ শুরু
        msg = await update.message.reply_text(
            f"⏳ **প্রাঙ্ক কল হচ্ছে...**\n\n"
            f"📱 নাম্বার: `{clean_number}`\n"
            f"🆔 প্রাঙ্ক আইডি: `{prank_id}`\n"
            f"📝 টাইটেল: {prank_title}\n\n"
            f"দয়া করে অপেক্ষা করুন...",
            parse_mode="Markdown"
        )
        
        try:
            # API কল
            api_url = f"{PRANK_API_URL}?number={clean_number}&prank={prank_id}"
            response = requests.get(api_url, timeout=30)
            result = response.text
            
            # ক্রেডিট কাট
            user_data['credits'] -= 1
            update_user(user_id, "credits", user_data['credits'])
            
            # সফল হলে দেখাবে
            await msg.edit_text(
                f"✅ **প্রাঙ্ক কল সম্পন্ন!**\n\n"
                f"📱 নাম্বার: `{clean_number}`\n"
                f"🆔 প্রাঙ্ক আইডি: `{prank_id}`\n"
                f"📝 টাইটেল: {prank_title}\n"
                f"📊 রেসপন্স: `{result[:200]}`\n\n"
                f"💰 বাকি ক্রেডিট: {user_data['credits']}",
                reply_markup=get_permanent_keyboard(),
                parse_mode="Markdown"
            )
        except requests.exceptions.Timeout:
            await msg.edit_text(
                f"⏰ **টাইমআউট!**\n\n"
                f"API থেকে সাড়া পাওয়া যায়নি। দয়া করে আবার চেষ্টা করুন।",
                reply_markup=get_permanent_keyboard(),
                parse_mode="Markdown"
            )
        except Exception as e:
            await msg.edit_text(
                f"❌ **API ত্রুটি!**\n\n{str(e)}",
                reply_markup=get_permanent_keyboard(),
                parse_mode="Markdown"
            )
        
        context.user_data['waiting_number'] = False
        context.user_data['selected_prank'] = None
        return
    
    # অ্যাডমিন ইনপুট
    if user_id in ADMIN_IDS:
        await handle_admin_input(update, context)

async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    
    action = context.user_data.get('admin_action')
    if not action:
        return
    
    text = update.message.text.strip()
    
    if action == 'add_credit':
        try:
            parts = text.split()
            if len(parts) != 2:
                await update.message.reply_text("❌ ভুল ফরম্যাট! ব্যবহার করুন: `user_id amount`", parse_mode="Markdown")
                return
            
            uid = int(parts[0])
            amount = int(parts[1])
            
            if add_credits(uid, amount):
                await update.message.reply_text(
                    f"✅ ইউজার `{uid}`-কে {amount} ক্রেডিট দেওয়া হয়েছে!",
                    reply_markup=get_admin_keyboard(),
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("❌ ইউজার পাওয়া যায়নি!", reply_markup=get_admin_keyboard())
        except ValueError:
            await update.message.reply_text("❌ ভুল ফরম্যাট! ব্যবহার করুন: `user_id amount`", parse_mode="Markdown")
        context.user_data['admin_action'] = None
    
    elif action == 'edit_refer':
        try:
            parts = text.split()
            if len(parts) != 2:
                await update.message.reply_text("❌ ভুল ফরম্যাট! ব্যবহার করুন: `user_id points`", parse_mode="Markdown")
                return
            
            uid = int(parts[0])
            points = int(parts[1])
            
            data = load_data()
            if str(uid) in data["users"]:
                data["users"][str(uid)]["total_referrals"] = points
                save_data(data)
                await update.message.reply_text(
                    f"✅ ইউজার `{uid}`-এর রেফার পয়েন্ট {points} করা হয়েছে!",
                    reply_markup=get_admin_keyboard(),
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("❌ ইউজার পাওয়া যায়নি!", reply_markup=get_admin_keyboard())
        except ValueError:
            await update.message.reply_text("❌ ভুল ফরম্যাট! ব্যবহার করুন: `user_id points`", parse_mode="Markdown")
        context.user_data['admin_action'] = None
    
    elif action == 'broadcast':
        users = load_data()["users"]
        success = 0
        failed = 0
        
        await update.message.reply_text("📤 ব্রডকাস্ট শুরু হচ্ছে...")
        
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
                failed += 1
        
        await update.message.reply_text(
            f"✅ {success} জন ইউজারকে বার্তা পাঠানো হয়েছে!\n"
            f"❌ {failed} জন ব্যর্থ হয়েছে।",
            reply_markup=get_admin_keyboard()
        )
        context.user_data['admin_action'] = None

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Update {update} caused error {context.error}")

# ==================== মেইন ====================
def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    global bot
    bot = application.bot
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", handle_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_error_handler(error_handler)
    
    print(f"🤖 {BOT_NAME} বট চালু হয়েছে!")
    print(f"📢 ফোর্স চ্যানেল: {FORCE_CHANNEL}")
    print(f"👑 অ্যাডমিন: {ADMIN_IDS}")
    print(f"📊 প্রাঙ্ক আইডি: {len(PRANK_IDS)}টি")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    import asyncio
    main()
