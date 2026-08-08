import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

# ----------------------------------------------------
# CONFIGURATION & INITIALIZATION
# ----------------------------------------------------
BOT_TOKEN = "8504721778:AAHwocLRx0VMNxeaSU5ToiDPNtqPR60XbrY"  # আপনার টেলিগ্রাম বট টোকেন দিন
ADMIN_ID = 7833766898              # আপনার টেলিগ্রাম নিউমেরিক ID দিন

# Bot Branding
BOT_NAME = "Bk777 Earn"
LOGO_URL = "https://i.ibb.co/L8G3X30/logo.jpg"  # img.bb থেকে আপনার লোগোর ডাইরেক্ট লিঙ্ক দিন

# Conversation States for Admin Panel
SET_CHANNEL, SET_REF_BONUS, SET_MIN_WITHDRAW, SET_DAILY_BONUS, SET_REF_BOX, BROADCAST, BAN_USER, UNBAN_USER = range(8)

# Global Data Store (For Production, use SQLite/PostgreSQL Database)
db = {
    "users": {},         # {user_id: {balance, ref_by, referrals, claimed_boxes, lang, captcha_passed}}
    "banned": [],        # [user_id, ...]
    "channels": [],      # ["@channel1", "@channel2"]
    "ref_bonus": 2.0,    # Default Referral Bonus
    "daily_bonus": 1.0,  # Default Daily Bonus
    "min_withdraw": 50,  # Default Minimum Withdraw Amount
    "ref_boxes": {       # Referral Milestone Boxes
        10: 5,
        20: 30,
        30: 60
    },
    "withdraw_requests": []
}

# ----------------------------------------------------
# LANGUAGE STRINGS (বাংলা ও English)
# ----------------------------------------------------
STRINGS = {
    "BN": {
        "verifying": "⏳ দয়া করে অপেক্ষা করুন, ভেরিফিকেশন করা হচ্ছে...",
        "captcha_msg": "🤖 মানব পরীক্ষা: অনুগ্রহ করে নিচের ক্যাপচা বাটনটিতে ক্লিক করে ভেরিফাই করুন।",
        "captcha_btn": "✅ আমি রোবট নই (Verify)",
        "select_lang": "🌐 দয়া করে আপনার ভাষা নির্বাচন করুন 👇",
        "force_join": "⚠️ বট ব্যবহার করতে হলে আপনাকে অবশ্যই আমাদের অফিশিয়াল চ্যানেলে জয়েন করতে হবে!",
        "btn_join": "📢 Join Now",
        "btn_verify": "🔄 Verify Now",
        "welcome": f"🎉 **{BOT_NAME}** এ আপনাকে স্বাগতম!\n\nনিচের বাটনগুলো ব্যবহার করে কাজ শুরু করুন:",
        "balance_text": "💰 **আপনার ব্যালেন্স বিবরণী:**\n\n💵 মূল ব্যালেন্স: ৳{balance:.2f}\n👥 মোট রেফারেল: {ref_count} জন",
        "invite_text": "🔗 **আপনার রেফারেল লিংক:**\n`https://t.me/{bot_username}?start={user_id}`\n\n👥 প্রতি সফল রেফারে পাবেন: ৳{ref_bonus:.2f}",
        "daily_success": "🎉 অভিনন্দন! আপনি আজকের ডেইলি বোনাস ৳{amount:.2f} ক্লেইম করেছেন।",
        "daily_claimed": "❌ আপনি আজ ইতিমধ্যেই বোনাস ক্লেইম করেছেন! আগামীকাল আবার চেষ্টা করুন।",
        "ref_box_title": "🎁 **রেফারেল বক্স রিওয়ার্ডস:**\n\nরেফার টার্গেট পূরণ করে বোনাস আনলক করুন:",
        "ref_box_claimed": "✅ ইতিমধ্যেই ক্লেইম করা হয়েছে",
        "ref_box_claim_btn": "🎁 Claim (৳{reward})",
        "ref_box_locked": "🔒 Locked ({current}/{target})",
        "ref_box_success": "🎉 অভিনন্দন! আপনি {target} রেফারেল বক্স থেকে ৳{reward} ক্লেইম করেছেন!",
        "ref_box_already": "❌ আপনি এই বক্স রিওয়ার্ডটি আগেই ক্লেইম করেছেন।",
        "ref_box_not_enough": "❌ আপনার পর্যাপ্ত রেফার নেই! আরও রেফার করুন।",
        "withdraw_menu": "💳 **উইথড্র প্যানেল:**\n\n📌 মিনিমাম উইথড্র: ৳{min_withdraw}\n💵 আপনার বর্তমান ব্যালেন্স: ৳{balance:.2f}",
        "withdraw_low_bal": "❌ আপনার পর্যাপ্ত ব্যালেন্স নেই! মিনিমাম উইথড্র ৳{min_withdraw}",
        "btn_balance": "💰 Balance",
        "btn_invite": "👥 Invite Friends",
        "btn_daily": "📅 Daily Bonus",
        "btn_ref_box": "🎁 Referral Box",
        "btn_withdraw": "💳 Withdraw",
        "btn_admin": "⚙️ Admin Panel"
    },
    "EN": {
        "verifying": "⏳ Please wait, verification is in progress...",
        "captcha_msg": "🤖 Human Verification: Please click the button below to verify.",
        "captcha_btn": "✅ I am not a robot (Verify)",
        "select_lang": "🌐 Please select your language 👇",
        "force_join": "⚠️ You must join our official channels to use this bot!",
        "btn_join": "📢 Join Now",
        "btn_verify": "🔄 Verify Now",
        "welcome": f"🎉 Welcome to **{BOT_NAME}**!\n\nUse the buttons below to navigate:",
        "balance_text": "💰 **Your Balance Details:**\n\n💵 Main Balance: ৳{balance:.2f}\n👥 Total Referrals: {ref_count}",
        "invite_text": "🔗 **Your Referral Link:**\n`https://t.me/{bot_username}?start={user_id}`\n\n👥 Earn per referral: ৳{ref_bonus:.2f}",
        "daily_success": "🎉 Congratulations! You have claimed your daily bonus of ৳{amount:.2f}.",
        "daily_claimed": "❌ You have already claimed today's bonus! Try again tomorrow.",
        "ref_box_title": "🎁 **Referral Box Rewards:**\n\nComplete referral targets to unlock bonuses:",
        "ref_box_claimed": "✅ Already Claimed",
        "ref_box_claim_btn": "🎁 Claim (৳{reward})",
        "ref_box_locked": "🔒 Locked ({current}/{target})",
        "ref_box_success": "🎉 Congratulations! You claimed ৳{reward} from {target} Ref Box!",
        "ref_box_already": "❌ You have already claimed this box reward.",
        "ref_box_not_enough": "❌ Not enough referrals! Invite more friends.",
        "withdraw_menu": "💳 **Withdrawal Panel:**\n\n📌 Minimum Withdraw: ৳{min_withdraw}\n💵 Your Balance: ৳{balance:.2f}",
        "withdraw_low_bal": "❌ Insufficient balance! Minimum withdraw is ৳{min_withdraw}",
        "btn_balance": "💰 Balance",
        "btn_invite": "👥 Invite Friends",
        "btn_daily": "📅 Daily Bonus",
        "btn_ref_box": "🎁 Referral Box",
        "btn_withdraw": "💳 Withdraw",
        "btn_admin": "⚙️ Admin Panel"
    }
}

# ----------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------
def get_user(user_id):
    if user_id not in db["users"]:
        db["users"][user_id] = {
            "balance": 0.0,
            "ref_by": None,
            "referrals": 0,
            "claimed_boxes": [],
            "daily_claimed": False,
            "lang": "BN",
            "captcha_passed": False
        }
    return db["users"][user_id]

async def check_force_join(user_id, context):
    if not db["channels"]:
        return True
    for ch in db["channels"]:
        try:
            member = await context.bot.get_chat_member(chat_id=ch, user_id=user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception:
            return False
    return True

def get_main_keyboard(user_id):
    u = get_user(user_id)
    lang = u["lang"]
    s = STRINGS[lang]
    
    keyboard = [
        [InlineKeyboardButton(s["btn_balance"], callback_data="btn_balance"), InlineKeyboardButton(s["btn_invite"], callback_data="btn_invite")],
        [InlineKeyboardButton(s["btn_daily"], callback_data="btn_daily"), InlineKeyboardButton(s["btn_ref_box"], callback_data="btn_ref_box")],
        [InlineKeyboardButton(s["btn_withdraw"], callback_data="btn_withdraw")]
    ]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton(s["btn_admin"], callback_data="btn_admin")])
        
    return InlineKeyboardMarkup(keyboard)

# ----------------------------------------------------
# START & CAPTCHA FLOW
# ----------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in db["banned"]:
        return

    u = get_user(user_id)
    
    # Save Referral Data if new
    if context.args and not u["ref_by"] and u["referrals"] == 0:
        try:
            ref_id = int(context.args[0])
            if ref_id != user_id and ref_id in db["users"]:
                u["ref_by"] = ref_id
        except ValueError:
            pass

    # Send Logo with Verification Pending Text
    await context.bot.send_photo(
        chat_id=user_id,
        photo=LOGO_URL,
        caption=STRINGS["BN"]["verifying"]
    )
    await asyncio.sleep(1.5)  # Simulated Delay

    # Send Captcha Button
    captcha_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(STRINGS["BN"]["captcha_btn"], callback_data="pass_captcha")]
    ])
    await update.message.reply_text(STRINGS["BN"]["captcha_msg"], reply_markup=captcha_kb)

async def captcha_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    u = get_user(user_id)
    u["captcha_passed"] = True
    
    # Language Selection Buttons (Side by Side)
    lang_kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇧🇩 বাংলা", callback_data="set_lang_BN"),
            InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_EN")
        ]
    ])
    await query.message.edit_text(STRINGS["BN"]["select_lang"], reply_markup=lang_kb)

async def set_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    lang_code = query.data.split("_")[2]
    u = get_user(user_id)
    u["lang"] = lang_code
    
    # Add Referral Credit after Language Selection (To avoid fake bot clicks)
    if u["ref_by"]:
        ref_user = get_user(u["ref_by"])
        ref_user["balance"] += db["ref_bonus"]
        ref_user["referrals"] += 1
        try:
            await context.bot.send_message(
                chat_id=u["ref_by"],
                text=f"🎉 New Referral Joined! You earned ৳{db['ref_bonus']:.2f}"
            )
        except Exception:
            pass
        u["ref_by"] = None  # Processed once

    # Force Join Check
    if not await check_force_join(user_id, context):
        buttons = []
        for ch in db["channels"]:
            ch_url = f"https://t.me/{ch.replace('@', '')}"
            buttons.append(InlineKeyboardButton(STRINGS[lang_code]["btn_join"], url=ch_url))
        
        # Grid of 2 buttons per row
        grid = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
        grid.append([InlineKeyboardButton(STRINGS[lang_code]["btn_verify"], callback_data="check_join")])
        
        await query.message.reply_text(
            STRINGS[lang_code]["force_join"],
            reply_markup=InlineKeyboardMarkup(grid)
        )
        return

    await query.message.reply_text(
        STRINGS[lang_code]["welcome"],
        reply_markup=get_main_keyboard(user_id),
        parse_mode="Markdown"
    )

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    u = get_user(user_id)
    lang = u["lang"]

    if await check_force_join(user_id, context):
        await query.message.delete()
        await query.message.reply_text(
            STRINGS[lang]["welcome"],
            reply_markup=get_main_keyboard(user_id),
            parse_mode="Markdown"
        )
    else:
        await query.answer("❌ You haven't joined all channels yet!", show_alert=True)

# ----------------------------------------------------
# MAIN USER BUTTON CALLBACKS
# ----------------------------------------------------
async def user_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if user_id in db["banned"]:
        return

    u = get_user(user_id)
    lang = u["lang"]
    s = STRINGS[lang]
    action = query.data

    if action == "btn_balance":
        text = s["balance_text"].format(balance=u["balance"], ref_count=u["referrals"])
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))

    elif action == "btn_invite":
        bot_obj = await context.bot.get_me()
        text = s["invite_text"].format(bot_username=bot_obj.username, user_id=user_id, ref_bonus=db["ref_bonus"])
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=get_main_keyboard(user_id))

    elif action == "btn_daily":
        if not u["daily_claimed"]:
            u["daily_claimed"] = True
            u["balance"] += db["daily_bonus"]
            text = s["daily_success"].format(amount=db["daily_bonus"])
        else:
            text = s["daily_claimed"]
        await query.message.reply_text(text, reply_markup=get_main_keyboard(user_id))

    elif action == "btn_ref_box":
        kb = []
        for target, reward in sorted(db["ref_boxes"].items()):
            if target in u["claimed_boxes"]:
                btn_text = f"{target} Ref ➔ {s['ref_box_claimed']}"
                cb_data = "refbox_already"
            elif u["referrals"] >= target:
                btn_text = f"{target} Ref ➔ " + s["ref_box_claim_btn"].format(reward=reward)
                cb_data = f"claimbox_{target}"
            else:
                btn_text = f"{target} Ref ➔ " + s["ref_box_locked"].format(current=u["referrals"], target=target)
                cb_data = "refbox_notyet"
            
            kb.append([InlineKeyboardButton(btn_text, callback_data=cb_data)])
        
        await query.message.reply_text(s["ref_box_title"], reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif action.startswith("claimbox_"):
        target = int(action.split("_")[1])
        reward = db["ref_boxes"].get(target, 0)
        
        if target in u["claimed_boxes"]:
            await query.answer(s["ref_box_already"], show_alert=True)
        elif u["referrals"] >= target:
            u["claimed_boxes"].append(target)
            u["balance"] += reward
            await query.answer(s["ref_box_success"].format(target=target, reward=reward), show_alert=True)
            # Refresh box menu
            await query.message.delete()
        else:
            await query.answer(s["ref_box_not_enough"], show_alert=True)

    elif action == "refbox_already":
        await query.answer(s["ref_box_already"], show_alert=True)
    elif action == "refbox_notyet":
        await query.answer(s["ref_box_not_enough"], show_alert=True)

    elif action == "btn_withdraw":
        if u["balance"] < db["min_withdraw"]:
            text = s["withdraw_low_bal"].format(min_withdraw=db["min_withdraw"])
            await query.message.reply_text(text, reply_markup=get_main_keyboard(user_id))
        else:
            # Automatic withdrawal request logic
            text = s["withdraw_menu"].format(min_withdraw=db["min_withdraw"], balance=u["balance"])
            req_text = f"⚙️ Withdraw Request Logged! Admin will process it soon.\nYour Current Balance: ৳{u['balance']:.2f}"
            db["withdraw_requests"].append({"user_id": user_id, "amount": u["balance"]})
            await query.message.reply_text(f"{text}\n\n✅ {req_text}", reply_markup=get_main_keyboard(user_id))

# ----------------------------------------------------
# ADMIN PANEL LOGIC
# ----------------------------------------------------
def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 Set Channel", callback_data="admin_set_chan"), InlineKeyboardButton("🗑 Remove Channel", callback_data="admin_rem_chan")],
        [InlineKeyboardButton("💵 Set Ref Bonus", callback_data="admin_set_ref"), InlineKeyboardButton("💰 Set Bonus", callback_data="admin_set_daily")],
        [InlineKeyboardButton("💳 Set Min Withdraw", callback_data="admin_set_min_w"), InlineKeyboardButton("🎁 Set Ref Box", callback_data="admin_set_refbox")],
        [InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban"), InlineKeyboardButton("✅ Unban User", callback_data="admin_unban")],
        [InlineKeyboardButton("📥 Withdraw Request", callback_data="admin_withdraws"), InlineKeyboardButton("📡 Broadcast", callback_data="admin_broadcast")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def admin_panel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return
    await query.message.reply_text("⚙️ **Welcome to Admin Panel:**", reply_markup=get_admin_keyboard(), parse_mode="Markdown")

async def admin_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return

    data = query.data
    if data == "admin_set_chan":
        await query.message.reply_text(" Send Telegram Channel Username (e.g. `@MyChannel`):")
        return SET_CHANNEL
    elif data == "admin_rem_chan":
        db["channels"] = []
        await query.message.reply_text("✅ All Force-Join Channels Removed!")
    elif data == "admin_set_ref":
        await query.message.reply_text(" Send New Referral Bonus Amount (e.g. `2.5`):")
        return SET_REF_BONUS
    elif data == "admin_set_daily":
        await query.message.reply_text(" Send New Daily Bonus Amount (e.g. `1.0`):")
        return SET_DAILY_BONUS
    elif data == "admin_set_min_w":
        await query.message.reply_text(" Send New Minimum Withdraw Amount (e.g. `50`):")
        return SET_MIN_WITHDRAW
    elif data == "admin_set_refbox":
        await query.message.reply_text(" Send Ref Box in format: `Target,Reward` (e.g., `40,80`):")
        return SET_REF_BOX
    elif data == "admin_ban":
        await query.message.reply_text(" Send User ID to Ban:")
        return BAN_USER
    elif data == "admin_unban":
        await query.message.reply_text(" Send User ID to Unban:")
        return UNBAN_USER
    elif data == "admin_broadcast":
        await query.message.reply_text(" Send/Forward the message, photo, or file you want to Broadcast to all users:")
        return BROADCAST
    elif data == "admin_withdraws":
        if not db["withdraw_requests"]:
            await query.message.reply_text("🙌 No Pending Withdrawal Requests!")
        else:
            msg = "📥 **Pending Withdrawals:**\n\n"
            for req in db["withdraw_requests"]:
                msg += f"👤 User: `{req['user_id']}` | Amount: ৳{req['amount']:.2f}\n"
            await query.message.reply_text(msg, parse_mode="Markdown")

# Admin Input Receivers
async def save_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ch = update.message.text.strip()
    db["channels"].append(ch)
    await update.message.reply_text(f"✅ Channel {ch} added successfully!", reply_markup=get_admin_keyboard())
    return ConversationHandler.END

async def save_ref_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text.strip())
        db["ref_bonus"] = val
        await update.message.reply_text(f"✅ Referral bonus set to ৳{val:.2f}", reply_markup=get_admin_keyboard())
    except ValueError:
        await update.message.reply_text("❌ Invalid input! Numbers only.")
    return ConversationHandler.END

async def save_daily_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text.strip())
        db["daily_bonus"] = val
        await update.message.reply_text(f"✅ Daily bonus set to ৳{val:.2f}", reply_markup=get_admin_keyboard())
    except ValueError:
        await update.message.reply_text("❌ Invalid input!")
    return ConversationHandler.END

async def save_min_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text.strip())
        db["min_withdraw"] = val
        await update.message.reply_text(f"✅ Min Withdraw set to ৳{val:.2f}", reply_markup=get_admin_keyboard())
    except ValueError:
        await update.message.reply_text("❌ Invalid input!")
    return ConversationHandler.END

async def save_ref_box(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        raw = update.message.text.strip().split(",")
        target = int(raw[0])
        reward = float(raw[1])
        db["ref_boxes"][target] = reward
        await update.message.reply_text(f"✅ Referral Box added: {target} Ref ➔ ৳{reward}", reply_markup=get_admin_keyboard())
    except Exception:
        await update.message.reply_text("❌ Invalid format! Send as `10,5` (Target,Reward)")
    return ConversationHandler.END

async def process_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = int(update.message.text.strip())
        db["banned"].append(uid)
        await update.message.reply_text(f"🚫 User {uid} Banned successfully!", reply_markup=get_admin_keyboard())
    except ValueError:
        await update.message.reply_text("❌ Invalid User ID!")
    return ConversationHandler.END

async def process_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = int(update.message.text.strip())
        if uid in db["banned"]:
            db["banned"].remove(uid)
            await update.message.reply_text(f"✅ User {uid} Unbanned!", reply_markup=get_admin_keyboard())
        else:
            await update.message.reply_text("⚠️ User not in ban list!")
    except ValueError:
        await update.message.reply_text("❌ Invalid User ID!")
    return ConversationHandler.END

async def process_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    count = 0
    await update.message.reply_text("⏳ Broadcasting message to all users...")
    
    for uid in list(db["users"].keys()):
        try:
            await msg.copy(chat_id=uid)
            count += 1
            await asyncio.sleep(0.05)  # Telegram API Limit handling
        except Exception:
            pass
            
    await update.message.reply_text(f"🎉 Broadcast finished! Sent to {count} users.", reply_markup=get_admin_keyboard())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation Cancelled.", reply_markup=get_admin_keyboard())
    return ConversationHandler.END

# ----------------------------------------------------
# MAIN APPLICATION SETUP
# ----------------------------------------------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Admin Conversation Handler
    admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_action_handler, pattern="^admin_")],
        states={
            SET_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_channel)],
            SET_REF_BONUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_ref_bonus)],
            SET_DAILY_BONUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_daily_bonus)],
            SET_MIN_WITHDRAW: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_min_withdraw)],
            SET_REF_BOX: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_ref_box)],
            BAN_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_ban)],
            UNBAN_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_unban)],
            BROADCAST: [MessageHandler(filters.ALL & ~filters.COMMAND, process_broadcast)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # Command Handlers
    app.add_handler(CommandHandler("start", start))
    
    # Callback Handlers
    app.add_handler(CallbackQueryHandler(captcha_callback, pattern="^pass_captcha$"))
    app.add_handler(CallbackQueryHandler(set_language_callback, pattern="^set_lang_"))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))
    app.add_handler(CallbackQueryHandler(admin_panel_start, pattern="^btn_admin$"))
    app.add_handler(admin_conv)
    app.add_handler(CallbackQueryHandler(user_menu_handler))

    # Run Bot
    print(f"🤖 {BOT_NAME} Bot Started Successfully...")
    app.run_polling()

if __name__ == "__main__":
    main()
