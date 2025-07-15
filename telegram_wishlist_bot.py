import os
import json
from typing import Dict, List
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class WishlistBot:
    def __init__(self):
        self.data_file = "wishlists.json"
        self.wishlists = self.load_data()
    
    def load_data(self) -> Dict:
        """بارگذاری داده‌ها از فایل"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_data(self):
        """ذخیره داده‌ها در فایل"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.wishlists, f, ensure_ascii=False, indent=2)
    
    def get_user_lists(self, user_id: str) -> Dict:
        """دریافت لیست‌های کاربر"""
        if user_id not in self.wishlists:
            self.wishlists[user_id] = {}
        return self.wishlists[user_id]
    
    def add_to_list(self, user_id: str, list_name: str, item: str):
        """اضافه کردن آیتم به لیست"""
        user_lists = self.get_user_lists(user_id)
        if list_name not in user_lists:
            user_lists[list_name] = []
        
        if item not in user_lists[list_name]:
            user_lists[list_name].append(item)
            self.save_data()
            return True
        return False
    
    def get_list(self, user_id: str, list_name: str) -> List[str]:
        """دریافت آیتم‌های یک لیست"""
        user_lists = self.get_user_lists(user_id)
        return user_lists.get(list_name, [])
    
    def remove_from_list(self, user_id: str, list_name: str, item: str):
        """حذف آیتم از لیست"""
        user_lists = self.get_user_lists(user_id)
        if list_name in user_lists and item in user_lists[list_name]:
            user_lists[list_name].remove(item)
            self.save_data()
            return True
        return False
    
    def get_all_lists(self, user_id: str) -> Dict:
        """دریافت تمام لیست‌های کاربر"""
        return self.get_user_lists(user_id)

# ایجاد instance از ربات
bot = WishlistBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پیام خوشآمدگویی"""
    welcome_message = """
🎯 سلام! من ربات ویش لیست شما هستم!

📝 دستورات:
• برای مشاهده لیست: `نام_لیست`
• برای اضافه کردن: `نام_لیست آیتم_جدید`
• برای حذف: `/remove نام_لیست آیتم`
• برای مشاهده همه لیست‌ها: `/lists`

📋 مثال‌ها:
• `films` - نمایش لیست فیلم‌ها
• `films Inception` - اضافه کردن فیلم Inception
• `کارها خرید نان` - اضافه کردن به لیست کارها
• `/remove films Inception` - حذف فیلم

✨ شما می‌تونید هر تعداد لیست بسازید و بهشون آیتم اضافه کنید!
    """
    await update.message.reply_text(welcome_message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام‌های کاربر"""
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()
    
    # تقسیم پیام به کلمات
    parts = text.split()
    if not parts:
        return
    
    list_name = parts[0]
    
    if len(parts) == 1:
        # نمایش لیست
        items = bot.get_list(user_id, list_name)
        if items:
            response = f"📋 لیست {list_name}:\n\n"
            for i, item in enumerate(items, 1):
                response += f"{i}. {item}\n"
        else:
            response = f"📭 لیست '{list_name}' خالی است یا وجود ندارد."
    else:
        # اضافه کردن آیتم
        item = " ".join(parts[1:])
        if bot.add_to_list(user_id, list_name, item):
            response = f"✅ '{item}' به لیست '{list_name}' اضافه شد!"
        else:
            response = f"⚠️ '{item}' قبلاً در لیست '{list_name}' موجود است."
    
    await update.message.reply_text(response)

async def remove_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف آیتم از لیست"""
    user_id = str(update.effective_user.id)
    
    if len(context.args) < 2:
        await update.message.reply_text("❌ فرمت: /remove نام_لیست آیتم")
        return
    
    list_name = context.args[0]
    item = " ".join(context.args[1:])
    
    if bot.remove_from_list(user_id, list_name, item):
        response = f"🗑️ '{item}' از لیست '{list_name}' حذف شد!"
    else:
        response = f"❌ '{item}' در لیست '{list_name}' یافت نشد."
    
    await update.message.reply_text(response)

async def show_all_lists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش تمام لیست‌ها"""
    user_id = str(update.effective_user.id)
    all_lists = bot.get_all_lists(user_id)
    
    if not all_lists:
        response = "📭 شما هیچ لیستی ندارید."
    else:
        response = "📋 لیست‌های شما:\n\n"
        for list_name, items in all_lists.items():
            item_count = len(items)
            response += f"• {list_name} ({item_count} آیتم)\n"
    
    await update.message.reply_text(response)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """راهنما"""
    help_text = """
🆘 راهنمای استفاده:

📝 دستورات اصلی:
• `نام_لیست` - نمایش لیست
• `نام_لیست آیتم` - اضافه کردن آیتم
• `/remove نام_لیست آیتم` - حذف آیتم
• `/lists` - نمایش همه لیست‌ها

📋 مثال‌های کاربردی:
• `films` - نمایش لیست فیلم‌ها
• `films The Matrix` - اضافه کردن فیلم
• `کتاب‌ها هری پاتر` - اضافه کردن کتاب
• `خرید نان و شیر` - اضافه کردن به لیست خرید
• `/remove films The Matrix` - حذف فیلم

💡 نکات:
• نام لیست‌ها می‌توانند فارسی یا انگلیسی باشند
• هر آیتم فقط یک بار در هر لیست ذخیره می‌شود
• تعداد لیست‌ها نامحدود است
    """
    await update.message.reply_text(help_text)

def main():
    """اجرای ربات"""
    # توکن ربات را اینجا قرار دهید
    BOT_TOKEN = "7659958351:AAH4KhKNWyYtBJmK1kCfZ2414i4S5juDV2c"
    
    # ایجاد اپلیکیشن
    application = Application.builder().token(BOT_TOKEN).build()
    
    # اضافه کردن هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("remove", remove_item))
    application.add_handler(CommandHandler("lists", show_all_lists))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # اجرای ربات
    print("ربات در حال اجرا...")
    application.run_polling()

if __name__ == '__main__':
    main()
