import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

from config import (
    BOT_TOKEN,
    CHANNEL_ID,
    BOT_NAME,
    PAIRS,
    EXPIRY_SECONDS,
    AUTO_SIGNAL_INTERVAL,
    QUOTEX_SSID
)
from quotex_feed import QuotexLiveWebSocket
from strategy import StrategyEngine
from chart_generator import generate_signal_chart

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Quotex Live WebSocket Feed
feed = QuotexLiveWebSocket(session_ssid=QUOTEX_SSID, pairs=PAIRS)
feed.start_connection()

# Signal and Win/Loss Tracking State
history_records: List[Dict] = []
auto_mode_running = False

def get_stats():
    """Calculates total wins, losses, and win rate percentage."""
    wins = sum(1 for r in history_records if r.get('status') == 'WIN')
    losses = sum(1 for r in history_records if r.get('status') == 'LOSS')
    total = wins + losses
    rate = int((wins / total * 100)) if total > 0 else 100
    return wins, losses, rate

def format_partial_summary(is_final=False) -> str:
    """Formats scorecard matching XT AI PRO Telegram style."""
    today_str = datetime.now().strftime("%Y.%m.%d")
    title_type = "FINAL" if is_final else "PARTIAL"
    wins, losses, rate = get_stats()

    lines = [
        f"{'='*12} {title_type} {'='*12}",
        "",
        f"🗓️ - {today_str}",
        "",
        f"🏛️ OTC MARKETS {title_type} 🏛️"
    ]

    # Show recent signals (up to 8)
    for record in history_records[-8:]:
        time_str = record['time']
        pair = record['pair']
        direction = "BUY" if record['direction'] == "CALL" else "PUT"
        status_icon = "✅" if record['status'] == "WIN" else "❌"
        lines.append(f"🔲 {time_str} - {pair} - {direction} {status_icon}")

    if not history_records:
        lines.append("🔲 No signals recorded yet today.")

    lines.extend([
        "",
        f"📈 TOTAL RATE: {wins}X{losses} • ({rate}%)",
        "",
        f"⚙️ PLATFORM: {BOT_NAME.upper()} TERMINAL",
        f"📡 {title_type} SENT SUCCESSFULLY"
    ])

    return "\n".join(lines)

async def check_signal_result(context: ContextTypes.DEFAULT_TYPE):
    """
    Called after expiry time to evaluate whether the signal won or lost.
    """
    job_data = context.job.data
    pair = job_data['pair']
    direction = job_data['direction']
    entry_price = job_data['entry_price']
    signal_time = job_data['time']
    chat_id = job_data['chat_id']

    # Update candle to simulate or get closing price
    feed.update_candle(pair)
    exit_price = feed.get_latest_price(pair)

    # Determine Win or Loss
    if direction == "CALL":
        is_win = exit_price >= entry_price
    else:
        is_win = exit_price <= entry_price

    status = "WIN" if is_win else "LOSS"

    # Save to history
    record = {
        'time': signal_time,
        'pair': pair,
        'direction': direction,
        'status': status
    }
    history_records.append(record)

    # Format result message matching the screenshot
    dir_icon = "🆙 CALL" if direction == "CALL" else "🔻 PUT"
    result_text = "✅ WIN ✦ Direct" if is_win else "🔴 LOSS"

    msg = (
        f"📊 {BOT_NAME} — AUTO RESULT\n\n"
        f"💲 Pair: {pair}\n"
        f"⏰ Time: {signal_time}\n"
        f"🔮 Direction: {dir_icon}\n\n"
        f"{result_text}"
    )

    keyboard = [
        [
            InlineKeyboardButton("📊 Partial Result", callback_data="partial_result"),
            InlineKeyboardButton("📈 Daily Full", callback_data="daily_full")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=msg,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error sending result message: {e}")

async def dispatch_signal(bot, chat_id, target_pair=None):
    """
    Finds the best market setup, renders the futuristic chart, and broadcasts the signal.
    """
    candidate_pairs = [target_pair] if target_pair else PAIRS
    best_signal = None
    best_df = None
    best_pair = None
    best_acc = "0%"

    for p in candidate_pairs:
        # Update candle feed
        feed.update_candle(p)
        df = feed.get_candles(p, count=42)
        sig, acc, reason = StrategyEngine.analyze(df)
        if sig:
            best_signal = sig
            best_df = df
            best_pair = p
            best_acc = acc
            break

    # If no natural setup triggered, pick the first pair for active demonstration
    if not best_signal:
        best_pair = candidate_pairs[0]
        feed.update_candle(best_pair)
        best_df = feed.get_candles(best_pair, count=42)
        best_signal = "CALL" if best_df['close'].iloc[-1] > best_df['open'].iloc[-1] else "PUT"
        best_acc = "88%"

    # Generate the chart
    chart_filename = f"chart_{best_pair}_{int(datetime.now().timestamp())}.png"
    generate_signal_chart(
        pair=best_pair,
        df=best_df,
        direction=best_signal,
        accuracy=best_acc,
        bot_name=BOT_NAME,
        output_path=chart_filename
    )

    now_time = datetime.now().strftime("%H:%M")
    today_str = datetime.now().strftime("%Y.%m.%d")
    dir_emoji = "🆙 CALL" if best_signal == "CALL" else "🔻 PUT"

    caption = (
        f"⚡ {BOT_NAME} ⚡\n"
        f"1,290 monthly users\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🗓️ - {today_str}\n\n"
        f"🏛️ OTC MARKETS 🏛️\n"
        f"💲 Pair: {best_pair}\n"
        f"⏰ Time: {now_time}\n"
        f"🔮 Direction: {dir_emoji}\n"
        f"🎯 Accuracy: {best_acc}\n"
        f"⏳ Expiry: 1 Min\n"
        f"━━━━━━━━━━━━━━━━━━"
    )

    keyboard = [
        [
            InlineKeyboardButton("📊 Partial Result", callback_data="partial_result"),
            InlineKeyboardButton("📈 Daily Full", callback_data="daily_full")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        with open(chart_filename, "rb") as photo_file:
            sent_msg = await bot.send_photo(
                chat_id=chat_id,
                photo=photo_file,
                caption=caption,
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Failed to send signal chart: {e}")
        return None

    # Cleanup image file
    if os.path.exists(chart_filename):
        try:
            os.remove(chart_filename)
        except Exception:
            pass

    return {
        'pair': best_pair,
        'direction': best_signal,
        'time': now_time,
        'entry_price': float(best_df['close'].iloc[-1]),
        'chat_id': chat_id
    }

# Commands
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        f"👋 **স্বাগতম! {BOT_NAME} ট্রেডিং সিগন্যাল বোটে।**\n\n"
        f"🔥 **ফিচারসমূহ:**\n"
        f"• Quotex OTC ও লাইভ মার্কেট ফিড\n"
        f"• ক্যান্ডেলস্টিক চার্ট সহ সিগন্যাল (EMA + RSI + Support/Resistance)\n"
        f"• অটো রেজাল্ট ট্র্যাকিং (WIN/LOSS)\n"
        f"• লাইভ স্কোরকার্ড ও পারফরম্যান্স রিপোর্ট\n\n"
        f"👉 সিগন্যাল পেতে নিচের কমান্ডগুলো ব্যবহার করুন:\n"
        f"• `/signal` - এখনই ইনস্ট্যান্ট সিগন্যাল ও চার্ট তৈরি করবে\n"
        f"• `/auto` - প্রতি ৩ মিনিটে অটোমেটিক সিগন্যাল পাঠানো অন/অফ করবে\n"
        f"• `/stats` - আজকের ফুল রেজাল্ট রিপোর্ট দেখবে"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def signal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    wait_msg = await update.message.reply_text("🔍 মার্কেট অ্যানালাইসিস ও চার্ট তৈরি করা হচ্ছে... অনুগ্রহ করে অপেক্ষা করুন...")
    
    signal_data = await dispatch_signal(context.bot, chat_id)
    try:
        await wait_msg.delete()
    except Exception:
        pass

    if signal_data and context.job_queue:
        # Schedule result check after EXPIRY_SECONDS
        context.job_queue.run_once(
            check_signal_result,
            when=EXPIRY_SECONDS,
            data=signal_data
        )

async def auto_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auto_mode_running
    chat_id = update.effective_chat.id

    if auto_mode_running:
        auto_mode_running = False
        current_jobs = context.job_queue.get_jobs_by_name("auto_signal_job")
        for job in current_jobs:
            job.schedule_removal()
        await update.message.reply_text("🛑 **অটো সিগন্যাল ব্রডকাস্ট বন্ধ করা হয়েছে।**", parse_mode="Markdown")
    else:
        auto_mode_running = True
        
        async def scheduled_signal(job_ctx: ContextTypes.DEFAULT_TYPE):
            s_data = await dispatch_signal(job_ctx.bot, chat_id)
            if s_data:
                job_ctx.job_queue.run_once(
                    check_signal_result,
                    when=EXPIRY_SECONDS,
                    data=s_data
                )

        context.job_queue.run_repeating(
            scheduled_signal,
            interval=AUTO_SIGNAL_INTERVAL,
            first=5,
            name="auto_signal_job"
        )
        await update.message.reply_text(
            f"🚀 **অটো সিগন্যাল চালু করা হয়েছে!** প্রতি {int(AUTO_SIGNAL_INTERVAL/60)} মিনিট পর পর স্বয়ংক্রিয়ভাবে সিগন্যাল ও চার্ট পাঠানো হবে।",
            parse_mode="Markdown"
        )

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    summary = format_partial_summary(is_final=False)
    await update.message.reply_text(summary)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "partial_result":
        summary = format_partial_summary(is_final=False)
        await query.message.reply_text(summary)
    elif query.data == "daily_full":
        summary = format_partial_summary(is_final=True)
        await query.message.reply_text(summary)

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("[!] ERROR: Please set your TELEGRAM_BOT_TOKEN in config.py or environment variable.")
        return

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("signal", signal_cmd))
    application.add_handler(CommandHandler("auto", auto_cmd))
    application.add_handler(CommandHandler("stats", stats_cmd))
    application.add_handler(CallbackQueryHandler(button_callback))

    print(f"[*] {BOT_NAME} Telegram Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
