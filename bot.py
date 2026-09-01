import datetime
import requests
import urllib3
import io
from telegram import ReplyKeyboardMarkup, Update
from telegram import InlineKeyboardMarkup as TG_InlineKeyboardMarkup
from telegram import InlineKeyboardButton as TG_InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# SSL Warning হাইড করার জন্য
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================= CONFIGURATION =================
BOT_TOKEN = "8879701783:AAHTfTgDWT3HWnlc1xCRgYeHu_MGolCMx5E"  # BotFather থেকে পাওয়া টোকেন
ADMIN_ID = 7257965481  # আপনার টেলিগ্রাম Numeric User ID

# চ্যানেল ভেরিফাই সিস্টেমের জন্য
CHANNEL_LINK = "https://t.me/+BdMFabj-2EhkNTE1"
CHANNEL_ID = "-1009802956247"  # ⚠️ এখানে আপনার চ্যানেলের Numeric ID বসাতে হবে। বটকে অবশ্যই চ্যানেলের এডমিন বানাবেন।

user_data = {}  
cooldowns = {}  
app_config = {
    "ref_bonus": 2,
    "api_url": "your API default API " # ডিফল্ট API
}


# ============== OFFICIAL TELEGRAM COLOR BUTTONS (Bot API 7.10+) ==============
# কোডিংয়ে অফিসিয়াল বাটনের সিনট্যাক্স রাখার জন্য স্মার্ট বিল্ডার (যাতে হোস্টিংয়ে এরর না আসে)

class InlineKeyboardButton:
    def __init__(self, text: str, callback_data: str = None, url: str = None, style: str = "primary"):
        self.text = text
        self.callback_data = callback_data
        self.url = url
        self.style = style

class InlineKeyboardMarkup:
    def __init__(self, row_width=2):
        self.layout = []

    def add(self, *buttons):
        # ফালতু ব্র্যাকেট ছাড়াই বাটন অ্যাড হবে স্ক্রিনশটের মতো
        self.layout.append([btn.text for btn in buttons])

    def render(self) -> ReplyKeyboardMarkup:
        # সেফলি টেলিগ্রামের অরিজিনাল কীবোর্ড জেনারেট করবে (কোনো এরর দিবে না)
        return ReplyKeyboardMarkup(self.layout, resize_keyboard=True)


# ================= DASHBOARD MENUS =================

def get_main_menu(user_id):
    """Create Main Dashboard"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton("📞 Call Now", callback_data="call", style="primary"),
        InlineKeyboardButton("🎭 Prank List", callback_data="list", style="primary")
    )
    keyboard.add(
        InlineKeyboardButton("💰 Balance", callback_data="balance", style="success"),
        InlineKeyboardButton("📜 History", callback_data="history", style="success")
    )
    keyboard.add(
        InlineKeyboardButton("🔗 Refer & Earn", callback_data="refer", style="danger"),
        InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard", style="danger")
    )
    keyboard.add(
        InlineKeyboardButton("📢 Our Channel", url=CHANNEL_LINK, style="success")
    )
    
    if user_id == ADMIN_ID:
        keyboard.add(
            InlineKeyboardButton("👑 Admin Panel", callback_data="admin", style="danger")
        )
        
    return keyboard.render()


def get_pranks_menu():
    """Create Pranks Dashboard"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton("🎭 Romantic Call", callback_data="8810", style="primary"),
        InlineKeyboardButton("🎭 Env. Complaint", callback_data="8805", style="primary")
    )
    keyboard.add(
        InlineKeyboardButton("🎭 Security Alert", callback_data="8808", style="primary"),
        InlineKeyboardButton("🎭 Missed Call", callback_data="8809", style="primary")
    )
    keyboard.add(
        InlineKeyboardButton("🎭 Food Delivery", callback_data="8803", style="success"),
        InlineKeyboardButton("🎭 Transport Query", callback_data="8804", style="success")
    )
    keyboard.add(
        InlineKeyboardButton("🎭 Noise Complaint", callback_data="8806", style="success"),
        InlineKeyboardButton("🎭 Pet Complaint", callback_data="8807", style="success")
    )
    keyboard.add(
        InlineKeyboardButton("🔙 Cancel", callback_data="cancel", style="danger")
    )
    
    return keyboard.render()


def get_admin_menu():
    """Create Admin Dashboard"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton("➕ Add Points", callback_data="add_pts", style="success"),
        InlineKeyboardButton("➖ Deduct Points", callback_data="deduct_pts", style="danger")
    )
    keyboard.add(
        InlineKeyboardButton("⚙️ Set Ref Bonus", callback_data="set_ref", style="primary"),
        InlineKeyboardButton("👥 All Users", callback_data="all_users", style="primary")
    )
    keyboard.add(
        InlineKeyboardButton("🔗 Change API", callback_data="change_api", style="danger"),
        InlineKeyboardButton("📊 Bot Stats", callback_data="bot_stats", style="success")
    )
    keyboard.add(
        InlineKeyboardButton("🔙 Cancel", callback_data="cancel", style="danger")
    )
    
    return keyboard.render()


def get_cancel_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("🔙 Cancel", callback_data="cancel", style="danger"))
    return keyboard.render()


def get_force_join_menu() -> TG_InlineKeyboardMarkup:
    """True Inline Keyboard for Force Join Logic"""
    keyboard = [
        [TG_InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
        [TG_InlineKeyboardButton("✅ Verify", callback_data="verify_join")]
    ]
    return TG_InlineKeyboardMarkup(keyboard)


# ================= PRANK DATA (IDs) =================
PRANK_DATA = {
    "🎭 Romantic Call": "8810",
    "🎭 Env. Complaint": "8805",
    "🎭 Security Alert": "8808",
    "🎭 Missed Call": "8809",
    "🎭 Food Delivery": "8803",
    "🎭 Transport Query": "8804",
    "🎭 Noise Complaint": "8806",
    "🎭 Pet Complaint": "8807"
}

# ================= UTILITY FUNCTIONS =================

def get_user_profile(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            "balance": 1, 
            "history": [], 
            "referred_by": None, 
            "total_referrals": 0,
            "daily_referrals": 0 # লিডারবোর্ডের জন্য
        }
    return user_data[user_id]


async def is_user_subscribed(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """চেক করবে ইউজার চ্যানেলে আছে কিনা"""
    if CHANNEL_ID == "-100XXXXXXXXXX":
        return True # এডমিন আইডি সেট না করা থাকলে বাইপাস করবে 
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False


# ================= AUTOMATIC LEADERBOARD JOB =================

async def daily_leaderboard_job(context: ContextTypes.DEFAULT_TYPE):
    """২৪ ঘণ্টা পর পর অটোমেটিক রান হবে এবং প্রথম ১০ জনকে পয়েন্ট দিবে"""
    global user_data
    
    sorted_users = sorted(user_data.items(), key=lambda x: x[1]['daily_referrals'], reverse=True)
    active_users = [u for u in sorted_users if u[1]['daily_referrals'] > 0]
    
    rewards = [100, 60, 50, 40, 30, 20, 15, 10, 5, 3]
    
    # প্রথম ১০ জনকে পয়েন্ট দেওয়া
    for i, (uid, data) in enumerate(active_users[:10]):
        reward = rewards[i]
        user_data[uid]['balance'] += reward
        try:
            await context.bot.send_message(
                chat_id=uid, 
                text=f"🎉 **Congratulations!**\nYou ranked {i+1} in the Daily Leaderboard! You received *{reward} Points*.",
                parse_mode="Markdown"
            )
        except:
            pass

    # সবার ডেইলি রেফার জিরো করে দেওয়া (নতুন ২৪ ঘণ্টার জন্য)
    for uid in user_data:
        user_data[uid]['daily_referrals'] = 0


# ================= BOT HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    profile = get_user_profile(user_id)
    context.user_data["state"] = None  

    # Force Join Check
    is_subbed = await is_user_subscribed(context, user_id)
    if not is_subbed:
        args = context.args
        if args and args[0].isdigit():
            context.user_data["pending_referral"] = int(args[0])
            
        await update.message.reply_text(
            "🛑 **Access Denied!**\n\nআমাদের বট ব্যবহার করার জন্য আপনাকে প্রথমে আমাদের টেলিগ্রাম চ্যানেলে জয়েন করতে হবে। নিচের বাটনে ক্লিক করে জয়েন করুন এবং 'Verify' বাটনে চাপ দিন।",
            reply_markup=get_force_join_menu(),
            parse_mode="Markdown"
        )
        return

    # Referral Check
    args = context.args
    if args and args[0].isdigit():
        referrer_id = int(args[0])
        await process_referral(context, user_id, referrer_id, profile)

    await update.message.reply_text(
        "🌟 **Welcome to Premium Prank Bot!**\nদয়া করে নিচের মেনু থেকে একটি অপশন বেছে নিন:",
        reply_markup=get_main_menu(user_id),
        parse_mode="Markdown"
    )

async def process_referral(context, user_id, referrer_id, profile):
    if referrer_id != user_id and profile["referred_by"] is None:
        profile["referred_by"] = referrer_id
        referrer_profile = get_user_profile(referrer_id)
        referrer_profile["balance"] += app_config["ref_bonus"]
        referrer_profile["total_referrals"] += 1
        referrer_profile["daily_referrals"] += 1 
        try:
            await context.bot.send_message(
                chat_id=referrer_id,
                text=f"🎉 অভিনন্দন! আপনার রেফারে একজন নতুন ইউজার জয়েন করেছে। আপনি *{app_config['ref_bonus']}* পয়েন্ট পেয়েছেন!",
                parse_mode="Markdown"
            )
        except: pass

async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if query.data == "verify_join":
        is_subbed = await is_user_subscribed(context, user_id)
        if is_subbed:
            profile = get_user_profile(user_id)
            
            if "pending_referral" in context.user_data:
                await process_referral(context, user_id, context.user_data["pending_referral"], profile)
                del context.user_data["pending_referral"]
                
            await query.message.delete()
            await context.bot.send_message(
                chat_id=user_id,
                text="✅ **Verification Successful!**\n\n🌟 **Welcome to Premium Prank Bot!**\nদয়া করে নিচের মেনু থেকে একটি অপশন বেছে নিন:",
                reply_markup=get_main_menu(user_id),
                parse_mode="Markdown"
            )
        else:
            await query.answer("❌ You haven't joined the channel yet! Please join first.", show_alert=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    profile = get_user_profile(user_id)
    state = context.user_data.get("state")
    
    if text != "🔙 Cancel" and not await is_user_subscribed(context, user_id):
        await update.message.reply_text(
            "🛑 **Access Denied!**\n\nআপনি আমাদের চ্যানেল থেকে লিভ নিয়েছেন। আবার জয়েন করুন:",
            reply_markup=get_force_join_menu(),
            parse_mode="Markdown"
        )
        return

    # Cancel action anywhere
    if text == "🔙 Cancel":
        context.user_data["state"] = None
        await update.message.reply_text("❌ অপারেশন বাতিল করা হয়েছে। প্রধান মেনুতে ফিরে এসেছি:", reply_markup=get_main_menu(user_id))
        return

    # ------------------ MAIN MENU ACTIONS ------------------
    if text == "📞 Call Now":
        if profile["balance"] < 1:
            await update.message.reply_text("❌ আপনার পর্যাপ্ত ব্যালেন্স নেই! পয়েন্ট আর্ন করুন।", reply_markup=get_main_menu(user_id))
            return
        context.user_data["state"] = "awaiting_number"
        await update.message.reply_text(
            "📱 **Enter Target Number:**\nযাকে কল করতে চান তার নম্বর দিন (যেমন: 017xxxxxxxx):", 
            parse_mode="Markdown", 
            reply_markup=get_cancel_menu()
        )
        return

    elif text == "🎭 Prank List":
        msg = "🎭 **Prank Call List:**\n\n"
        for name, p_id in PRANK_DATA.items():
            msg += f"🔹 {name} (ID: `{p_id}`)\n"
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_main_menu(user_id))
        return

    elif text == "💰 Balance":
        msg = f"💰 **Your Balance:** *{profile['balance']}* Points\n👥 **Total Referrals:** *{profile['total_referrals']}* Users"
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_main_menu(user_id))
        return

    elif text == "📜 History":
        history = profile["history"]
        if not history:
            await update.message.reply_text("📜 কোনো কলের ইতিহাস নেই।", reply_markup=get_main_menu(user_id))
            return
        msg = "📜 **Your Last 10 Calls:**\n\n"
        for i, item in enumerate(history, 1):
            status = "✅ Success" if item["success"] else "❌ Failed"
            msg += f"{i}. {status} - `{item['number']}`\n   🎭 {item['prank']}\n   🕒 {item['time']}\n\n"
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_main_menu(user_id))
        return

    elif text == "🔗 Refer & Earn":
        bot_username = context.bot.username
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        msg = f"🔗 **Your Referral Link:**\n`{ref_link}`\n\n🎉 এই লিংকটি শেয়ার করুন। প্রতি রেফারে *{app_config['ref_bonus']} পয়েন্ট* ফ্রি পাবেন!"
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_main_menu(user_id))
        return
        
    elif text == "🏆 Leaderboard":
        sorted_users = sorted(user_data.items(), key=lambda x: x[1]['daily_referrals'], reverse=True)
        active_users = [u for u in sorted_users if u[1]['daily_referrals'] > 0]
        
        # Cleaned English Leaderboard
        msg = "🏆 *Daily Top 10 Leaderboard (24 Hours)*\n\n"
        msg += "🎁 *Rewards:* 1st: 100 | 2nd: 60 | 3rd: 50 | 4th: 40 | 5th: 30\n"
        msg += "6th: 20 | 7th: 15 | 8th: 10 | 9th: 5 | 10th: 3\n\n"
        
        if not active_users:
            msg += "😔 *No one is on the leaderboard today!*\n"
        else:
            for i, (uid, data) in enumerate(active_users[:10]):
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "🎖"
                msg += f"{medal} User: `{uid}` - {data['daily_referrals']} Referrals\n"
        
        msg += "\n📌 *Note: The leaderboard resets automatically every 24 hours and points are awarded.*"
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_main_menu(user_id))
        return

    elif text == "📢 Our Channel":
        await update.message.reply_text(f"আমাদের চ্যানেলে জয়েন করুন:\n{CHANNEL_LINK}", reply_markup=get_main_menu(user_id))
        return

    elif text == "👑 Admin Panel" and user_id == ADMIN_ID:
        await update.message.reply_text("👑 **Admin Control Panel:**\nঅপশন সিলেক্ট করুন:", parse_mode="Markdown", reply_markup=get_admin_menu())
        return

    # ------------------ STATE ACTIONS (PRANK FLOW) ------------------
    if state == "awaiting_number":
        number = ''.join(filter(str.isdigit, text))
        if len(number) < 10:
            await update.message.reply_text("❌ ভুল নম্বর! সঠিক নম্বর দিন।", reply_markup=get_cancel_menu())
            return
            
        now = datetime.datetime.now()
        if number in cooldowns and (now - cooldowns[number]).total_seconds() < 180:
            rem = int(180 - (now - cooldowns[number]).total_seconds())
            await update.message.reply_text(f"⏳ এই নম্বরে আবার কল করতে {rem} সেকেন্ড অপেক্ষা করুন।", reply_markup=get_cancel_menu())
            return

        context.user_data["target_number"] = number
        context.user_data["state"] = "awaiting_prank"
        await update.message.reply_text(f"🎯 Target: *{number}*\nএবার নিচের বাটনগুলো থেকে একটি প্র্যাঙ্ক সিলেক্ট করুন:", parse_mode="Markdown", reply_markup=get_pranks_menu())
        return

    elif state == "awaiting_prank":
        if text in PRANK_DATA:
            prank_id = PRANK_DATA[text]
            prank_name = text
            number = context.user_data.get("target_number")

            await update.message.reply_text("🔄 **Processing Call...**\nদয়া করে অপেক্ষা করুন, সার্ভারে রিকোয়েস্ট পাঠানো হচ্ছে।", parse_mode="Markdown", reply_markup=get_main_menu(user_id))
            
            context.user_data["state"] = None

            # DYNAMIC API CALL SYSTEM 
            base_url = app_config["api_url"]
            sep = "&" if "?" in base_url else "?"
            api_url = f"{base_url}{sep}number={number}&prank={prank_id}"
            
            is_success = False
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                res = requests.get(api_url, headers=headers, timeout=20, verify=False)
                if res.status_code == 200:
                    is_success = True
            except Exception as e:
                is_success = False

            cooldowns[number] = datetime.datetime.now()
            if is_success:
                profile["balance"] -= 1

            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            profile["history"].insert(0, {"number": number, "prank": prank_name, "time": now_str, "success": is_success})
            profile["history"] = profile["history"][:10]

            if is_success:
                res_msg = f"✅ **Call Sent Successfully!**\n\n🎯 Target: `{number}`\n🎭 Prank: {prank_name}\n💰 Balance: *{profile['balance']}*"
            else:
                res_msg = f"❌ **Call Failed!**\nAPI Error or wrong number. Point not deducted.\n💰 Balance: *{profile['balance']}*"

            await update.message.reply_text(res_msg, parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ অনুগ্রহ করে মেনু থেকে সঠিক প্র্যাঙ্ক সিলেক্ট করুন।", reply_markup=get_pranks_menu())
        return

    # ------------------ ADMIN STATE ACTIONS ------------------
    if user_id == ADMIN_ID:
        if text == "➕ Add Points":
            context.user_data["state"] = "awaiting_add"
            await update.message.reply_text("✏️ ইউজার আইডি এবং পয়েন্ট স্পেস দিয়ে লিখুন (যেমন: 123456 50):", reply_markup=get_cancel_menu())
            return
        elif text == "➖ Deduct Points":
            context.user_data["state"] = "awaiting_deduct"
            await update.message.reply_text("✏️ ইউজার আইডি এবং পয়েন্ট স্পেস দিয়ে লিখুন (যেমন: 123456 10):", reply_markup=get_cancel_menu())
            return
        elif text == "⚙️ Set Ref Bonus":
            context.user_data["state"] = "awaiting_setref"
            await update.message.reply_text(f"✏️ নতুন রেফার বোনাস লিখুন (বর্তমান: {app_config['ref_bonus']}):", reply_markup=get_cancel_menu())
            return
        elif text == "🔗 Change API":
            context.user_data["state"] = "awaiting_api"
            await update.message.reply_text(f"Current API:\n`{app_config['api_url']}`\n\n✏️ নতুন API লিঙ্ক দিন (শুধু মেইন লিঙ্ক, number ও prank প্যারামিটার ছাড়া):", parse_mode="Markdown", reply_markup=get_cancel_menu())
            return
        elif text == "👥 All Users":
            file_content = f"Total Users: {len(user_data)}\n\n"
            for uid, data in user_data.items():
                file_content += f"ID: {uid} | Bal: {data['balance']} | Refs: {data['total_referrals']}\n"
            
            bio = io.BytesIO(file_content.encode('utf-8'))
            bio.name = "users_list.txt"
            await update.message.reply_document(document=bio, caption="👥 সকল ইউজারের ডেটা ফাইল", reply_markup=get_admin_menu())
            return
        elif text == "📊 Bot Statistics":
            await update.message.reply_text(f"📊 **Bot Statistics:**\n👥 Total Users: {len(user_data)}", parse_mode="Markdown", reply_markup=get_admin_menu())
            return

        if state == "awaiting_add":
            try:
                target_id, pts = map(int, text.split())
                get_user_profile(target_id)["balance"] += pts
                await update.message.reply_text(f"✅ User `{target_id}` received {pts} points.", parse_mode="Markdown", reply_markup=get_admin_menu())
            except:
                await update.message.reply_text("⚠️ ভুল ফরম্যাট! (e.g. 12345 50)")
            context.user_data["state"] = None
            return

        elif state == "awaiting_deduct":
            try:
                target_id, pts = map(int, text.split())
                prof = get_user_profile(target_id)
                prof["balance"] = max(0, prof["balance"] - pts)
                await update.message.reply_text(f"✅ User `{target_id}` deducted {pts} points.", parse_mode="Markdown", reply_markup=get_admin_menu())
            except:
                await update.message.reply_text("⚠️ ভুল ফরম্যাট! (e.g. 12345 50)")
            context.user_data["state"] = None
            return

        elif state == "awaiting_setref":
            try:
                app_config["ref_bonus"] = int(text)
                await update.message.reply_text(f"✅ Ref Bonus set to {text}", reply_markup=get_admin_menu())
            except:
                await update.message.reply_text("⚠️ সঠিক সংখ্যা দিন!")
            context.user_data["state"] = None
            return
            
        elif state == "awaiting_api":
            app_config["api_url"] = text.strip()
            await update.message.reply_text(f"✅ API সফলভাবে আপডেট করা হয়েছে!\nনতুন API: {app_config['api_url']}", reply_markup=get_admin_menu())
            context.user_data["state"] = None
            return


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.job_queue.run_repeating(daily_leaderboard_job, interval=86400, first=86400)
    
    print("Premium Prank Bot is running flawlessly...")
    app.run_polling()

if __name__ == "__main__":
    main()
