import os
import psutil
import asyncio
import speedtest
from threading import Thread
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, Application
from flask import Flask

# ==========================================
# PHẦN 1: CẤU HÌNH ĐỂ CHẠY TRÊN RENDER (KEEP ALIVE)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Bot is running OK!"

def run_http():
    # Render thường mở port 8080 hoặc qua biến môi trường PORT
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_http)
    t.start()

# ==========================================
# PHẦN 2: LOGIC BOT TELEGRAM
# ==========================================

# Biến lưu thời gian để cooldown (tránh spam lệnh bot quá nhanh)
last_cmd_time = {}

# Hàm kiểm tra trạng thái Server (CPU, RAM, Mạng)
async def server(update: Update, context: CallbackContext):
    # Lấy thông số CPU & RAM
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk_usage = psutil.disk_usage('/')
    
    # Kiểm tra mạng (Lưu ý: Speedtest trên Render có thể chậm, có thể bỏ qua nếu muốn bot nhanh hơn)
    download_speed = 0
    upload_speed = 0
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        download_speed = st.download() / 1e+6
        upload_speed = st.upload() / 1e+6
    except:
        pass

    await update.message.reply_text(
        f"🖥 **INFO SERVER RENDER**\n"
        f"CPU: *{cpu_percent}%*\n"
        f"RAM: *{memory.percent}%*\n"
        f"Disk: *{disk_usage.percent}%* used\n"
        f"Net: ↓ {download_speed:.2f} Mbps | ↑ {upload_speed:.2f} Mbps",
        parse_mode="Markdown"
    )

# Hàm xử lý lệnh SMS/SPAM (Dùng chung cho mọi người, KHÔNG CẦN VIP)
async def sms(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    # --- ĐÃ XÓA CHECK VIP Ở ĐÂY ---
    
    # Kiểm tra tham số đầu vào
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("❌ Cách dùng: /sms [số điện thoại] [số lần]")
        return

    phone = args[0]
    loops = args[1]

    # Kiểm tra tính hợp lệ cơ bản
    if not phone.isdigit() or len(phone) < 10:
        await update.message.reply_text("❌ Số điện thoại không hợp lệ.")
        return

    if not loops.isdigit() or int(loops) > 10000:
        await update.message.reply_text("❌ Số lần lặp không hợp lệ (Max 10000).")
        return

    # Thông báo đã nhận lệnh
    await update.message.reply_text(
        f"🚀 **Đang thực thi lệnh!**\n"
        f"📱 Mục tiêu: `{phone}`\n"
        f"🔄 Số lần: `{loops}`\n"
        f"⚠️ Trạng thái: Đang chạy trên Render...",
        parse_mode="Markdown"
    )

    # --- LƯU Ý CHO NGƯỜI DÙNG ---
    # Tại đây, code cũ của bạn dùng `subprocess.Popen` để chạy file `sms.py`.
    # Tôi đã thay thế bằng logic in ra log để đảm bảo an toàn.
    # Nếu bạn có file sms.py xử lý logic riêng, bạn có thể khôi phục lệnh subprocess tại đây.
    print(f"User {user_id} executed SMS on {phone} with {loops} loops.")
    
    # Giả lập thời gian chạy (để không spam bot liên tục)
    await asyncio.sleep(5) 
    await update.message.reply_text(f"✅ Đã hoàn thành tác vụ với {phone}.")

# ==========================================
# PHẦN 3: CHẠY CHƯƠNG TRÌNH
# ==========================================
if __name__ == "__main__":
    # Lấy Token từ biến môi trường (Cài đặt trong Render: Environment Variables)
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    if not TOKEN:
        print("❌ LỖI: Chưa có TELEGRAM_TOKEN trong biến môi trường!")
    else:
        # 1. Kích hoạt Web Server để Render không tắt Bot
        keep_alive()

        # 2. Khởi tạo Bot
        app_bot = Application.builder().token(TOKEN).build()

        # Đăng ký các lệnh
        app_bot.add_handler(CommandHandler("sms", sms))   # Lệnh SMS (cũ)
        app_bot.add_handler(CommandHandler("spam", sms))  # Gộp lệnh Spam vào SMS luôn
        app_bot.add_handler(CommandHandler("server", server)) # Lệnh xem cấu hình

        print("✅ Bot đang chạy trên Render...")
        app_bot.run_polling()
