import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton,InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, InlineQueryHandler
import json
import os
from datetime import datetime
import uuid

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# توکن ربات تلگرام خود را اینجا قرار دهید
BOT_TOKEN = ""

# فایل ذخیره داده‌ها
DATA_FILE = "wishlist_data.json"
WHITELIST_FILE = "whitelist.json"

# آیدی ادمین اصلی (صاحب ربات)
ADMIN_ID = 123456  # آیدی تلگرام خود را اینجا قرار دهید

class WishlistBot:
    def __init__(self):
        self.data = self.load_data()
        self.whitelist = self.load_whitelist()
        
    def load_data(self):
        """بارگذاری داده‌ها از فایل - حالا مشترک برای همه کاربران"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.get_default_data()
        return self.get_default_data()
    
    def get_default_data(self):
        """داده‌های پیش‌فرض مشترک"""
        return {
            'categories': {
                '1': {'name': 'فیلم', 'icon': '🎬', 'items': []},
                '2': {'name': 'کتاب', 'icon': '📚', 'items': []}
            },
            'next_category_id': 3,
            'next_item_id': 1,
            'movie_ratings': {} 
        }
    
    def save_data(self):
        """ذخیره داده‌ها در فایل"""
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def load_whitelist(self):
        """بارگذاری وایت لیست از فایل"""
        if os.path.exists(WHITELIST_FILE):
            try:
                with open(WHITELIST_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('allowed_users', [])
            except:
                return []
        return []
    
    def save_whitelist(self):
        """ذخیره وایت لیست در فایل"""
        with open(WHITELIST_FILE, 'w', encoding='utf-8') as f:
            json.dump({'allowed_users': self.whitelist}, f, ensure_ascii=False, indent=2)
    
    def is_user_allowed(self, user_id):
        """بررسی اجازه دسترسی کاربر"""
        return user_id == ADMIN_ID or user_id in self.whitelist
    
    def add_user_to_whitelist(self, user_id):
        """اضافه کردن کاربر به وایت لیست"""
        if user_id not in self.whitelist:
            self.whitelist.append(user_id)
            self.save_whitelist()
            return True
        return False
    
    def remove_user_from_whitelist(self, user_id):
        """حذف کاربر از وایت لیست"""
        if user_id in self.whitelist:
            self.whitelist.remove(user_id)
            self.save_whitelist()
            return True
        return False
    
    def get_whitelist_info(self):
        """دریافت اطلاعات وایت لیست"""
        return {
            'users': self.whitelist,
            'count': len(self.whitelist)
        }
    
    def get_shared_data(self):
        """دریافت داده‌های مشترک"""
        return self.data
    
    def add_category(self, name, icon='⭐'):
        """اضافه کردن دسته‌بندی جدید به داده‌های مشترک"""
        cat_id = str(self.data['next_category_id'])
        self.data['categories'][cat_id] = {
            'name': name,
            'icon': icon,
            'items': []
        }
        self.data['next_category_id'] += 1
        self.save_data()
        return cat_id
    
    def add_item(self, category_id, text, user_name="نامشخص"):
        """اضافه کردن آیتم جدید به داده‌های مشترک"""
        if category_id in self.data['categories']:
            item_id = str(self.data['next_item_id'])
            item = {
                'id': item_id,
                'text': text,
                'completed': False,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'added_by': user_name
            }
            self.data['categories'][category_id]['items'].append(item)
            self.data['next_item_id'] += 1
            self.save_data()
            return True
        return False
    
    def toggle_item(self, category_id, item_id, user_name="نامشخص"):
        """تغییر وضعیت آیتم"""
        if category_id in self.data['categories']:
            for item in self.data['categories'][category_id]['items']:
                if item['id'] == item_id:
                    item['completed'] = not item['completed']
                    item['last_modified_by'] = user_name
                    item['last_modified_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')
                    self.save_data()
                    return True
        return False
    
    def delete_item(self, category_id, item_id):
        """حذف آیتم"""
        if category_id in self.data['categories']:
            items = self.data['categories'][category_id]['items']
            self.data['categories'][category_id]['items'] = [
                item for item in items if item['id'] != item_id
            ]
            self.save_data()
            return True
        return False
    
    def delete_category(self, category_id):
        """حذف دسته‌بندی"""
        if category_id in self.data['categories']:
            del self.data['categories'][category_id]
            self.save_data()
            return True
        return False
    def add_movie_rating(self, movie_name, rating, comment, user_name, user_id):
        """اضافه کردن نمره فیلم"""
        if 'movie_ratings' not in self.data:
            self.data['movie_ratings'] = {}
        
        if movie_name not in self.data['movie_ratings']:
            self.data['movie_ratings'][movie_name] = {
                'ratings': [],
                'average': 0.0,
                'total_ratings': 0
            }
        
        # اضافه کردن نمره جدید
        rating_data = {
            'rating': rating,
            'comment': comment,
            'user_name': user_name,
            'user_id': user_id,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        
        # بررسی اینکه آیا این کاربر قبلا نمره داده یا نه
        existing_index = None
        for i, r in enumerate(self.data['movie_ratings'][movie_name]['ratings']):
            if r['user_id'] == user_id:
                existing_index = i
                break
        
        if existing_index is not None:
            # اپدیت نمره قبلی
            self.data['movie_ratings'][movie_name]['ratings'][existing_index] = rating_data
        else:
            # اضافه کردن نمره جدید
            self.data['movie_ratings'][movie_name]['ratings'].append(rating_data)
        
        # محاسبه میانگین جدید
        ratings = self.data['movie_ratings'][movie_name]['ratings']
        total = sum(r['rating'] for r in ratings)
        self.data['movie_ratings'][movie_name]['average'] = total / len(ratings)
        self.data['movie_ratings'][movie_name]['total_ratings'] = len(ratings)
        
        self.save_data()
        return True

    def get_movie_ratings(self, sort_by='name'):
        """دریافت لیست فیلم‌های نمره‌دهی شده"""
        if 'movie_ratings' not in self.data:
            return {}
        
        movies = self.data['movie_ratings'].copy()
        
        if sort_by == 'rating':
            # مرتب‌سازی بر اساس میانگین نمره (نازل)
            return dict(sorted(movies.items(), key=lambda x: x[1]['average'], reverse=True))
        elif sort_by == 'date':
            # مرتب‌سازی بر اساس آخرین نمره داده شده
            return dict(sorted(movies.items(), 
                              key=lambda x: max(r['date'] for r in x[1]['ratings']), 
                              reverse=True))
        else:
            # مرتب‌سازی بر اساس نام (الفبایی)
            return dict(sorted(movies.items()))
    
    def delete_movie_rating(self, movie_name):
        """حذف فیلم از لیست نمره‌دهی"""
        if 'movie_ratings' not in self.data:
            return False
        
        if movie_name in self.data['movie_ratings']:
            del self.data['movie_ratings'][movie_name]
            self.save_data()
            return True
        return False

    def get_user_movie_rating(self, movie_name, user_id):
        """دریافت نمره کاربر خاص برای فیلم"""
        if 'movie_ratings' not in self.data:
            return None
        
        if movie_name not in self.data['movie_ratings']:
            return None
        
        for rating in self.data['movie_ratings'][movie_name]['ratings']:
            if rating['user_id'] == user_id:
                return rating
        return None



# ایجاد instance از کلاس ربات
bot = WishlistBot()

def check_access(func):
    """دکوریتر برای بررسی دسترسی"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if not bot.is_user_allowed(user_id):
            user_name = update.effective_user.first_name or "کاربر"
            await update.message.reply_text(
                f"❌ {user_name} عزیز، شما مجاز به استفاده از این ربات نیستید!\n\n"
                f"🆔 آیدی شما: `{user_id}`\n\n"
                f"لطفاً از ادمین بخواهید شما را به لیست کاربران مجاز اضافه کند.",
                parse_mode='Markdown'
            )
            return
        
        return await func(update, context)
    return wrapper

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع ربات"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "کاربر"
    
    if not bot.is_user_allowed(user_id):
        await update.message.reply_text(
            f"❌ {user_name} عزیز، شما مجاز به استفاده از این ربات نیستید!\n\n"
            f"🆔 آیدی شما: `{user_id}`\n\n"
            f"لطفاً از ادمین بخواهید شما را به لیست کاربران مجاز اضافه کند.",
            parse_mode='Markdown'
        )
        return
    
    # بررسی پارامترهای deep linking
    if context.args:
        command = context.args[0]
        
        if command == "add_movie":
            context.user_data['waiting_for_movie_name'] = True
            await update.message.reply_text("🎬 نام فیلم را وارد کنید:")
            return
            
        elif command.startswith("add_item_"):
            category_id = command.replace("add_item_", "")
            context.user_data['waiting_for_item'] = category_id
            await update.message.reply_text("📝 متن آیتم جدید را بنویسید:")
            return
            
        elif command == "add_category":
            context.user_data['waiting_for_category'] = True
            await update.message.reply_text("📝 نام دسته‌بندی جدید را بنویسید:\n\n💡 راهنما: می‌توانید یک ایموجی در ابتدای نام قرار دهید تا به عنوان آیکون دسته‌بندی استفاده شود.")
            return
    
    welcome_text = f"""
🎉 سلام {user_name}\!

به PaNIr خوش اومدی

📋 قابلیت‌ها:
• 🤝 ویش لیست مشترک بین کاربران مجاز
• ➕ اضافه کردن دسته‌بندی جدید
• 📝 مدیریت آیتم‌ها در هر دسته
• ✅ تیک زدن آیتم‌های انجام شده
• ✏️ ویرایش و حذف آیتم‌ها
• 📊 مشاهده پیشرفت

🚀 دستورات:
• /movies \- امتیاز دهی فیلم ها
• /categories \- نمایش دسته‌بندی‌ها
• /add\_category \- اضافه کردن دسته جدید
• /help \- راهنما
"""
    
    if user_id == ADMIN_ID:
        welcome_text += """

👑 دستورات ادمین:
• /whitelist \- مدیریت کاربران مجاز
• /add\_user \[user\_id\] \- اضافه کردن کاربر
• /remove\_user \[user\_id\] \- حذف کاربر
"""
    
    welcome_text += "\nبرای شروع، دستور /categories را بزنید\."
    
    await update.message.reply_text(welcome_text, parse_mode='MarkdownV2')

@check_access
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش راهنما"""
    help_text = """
📚 **راهنمای استفاده:**

🔹 **دستورات اصلی:**
• `/categories` - نمایش همه دسته‌بندی‌ها
• `/add_category` - اضافه کردن دسته‌بندی جدید
• `/help` - نمایش این راهنما
• `/movies` - نمره‌دهی فیلم‌ها

🔹 **نحوه استفاده:**
1️⃣ ابتدا دسته‌بندی‌هایتان را با `/categories` ببینید
2️⃣ روی هر دسته کلیک کنید تا آیتم‌هایش را ببینید
3️⃣ از دکمه‌ها برای اضافه کردن، ویرایش یا حذف استفاده کنید
4️⃣ برای تیک زدن آیتم‌ها، روی دکمه ✅ کلیک کنید

🤝 **ویژگی‌های مشترک:**
• تمام کاربران مجاز به یک ویش لیست دسترسی دارند
• تغییرات شما برای همه کاربران قابل مشاهده است
• نام افزوده‌کننده هر آیتم نمایش داده می‌شود

💡 **نکات:**
• می‌توانید آیکون‌های مختلف برای دسته‌بندی‌ها انتخاب کنید
• آیتم‌های انجام شده با رنگ سبز نمایش داده می‌شوند
• داده‌های مشترک به صورت امن ذخیره می‌شوند

سوال دارید؟ فقط پیام بدهید! 😊
"""
    await update.message.reply_text(help_text)

async def admin_whitelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت وایت لیست (فقط ادمین)"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ فقط ادمین می‌تواند وایت لیست را مدیریت کند!")
        return
    
    whitelist_info = bot.get_whitelist_info()
    
    text = "👑 **مدیریت کاربران مجاز:**\n\n"
    text += f"📊 تعداد کاربران مجاز: {whitelist_info['count']}\n\n"
    
    if whitelist_info['users']:
        text += "👥 **کاربران مجاز:**\n"
        for user_id in whitelist_info['users']:
            text += f"• `{user_id}`\n"
    else:
        text += "📝 هیچ کاربری در لیست نیست.\n"
    
    text += "\n🔧 **دستورات:**\n"
    text += "• `/add_user [user_id]` - اضافه کردن کاربر\n"
    text += "• `/remove_user [user_id]` - حذف کاربر\n"
    text += "• `/whitelist` - مشاهده این لیست\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def admin_add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اضافه کردن کاربر به وایت لیست"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ فقط ادمین می‌تواند کاربر اضافه کند!")
        return
    
    if not context.args:
        await update.message.reply_text("❌ لطفاً آیدی کاربر را وارد کنید!\n\nمثال: `/add_user 123456789`", parse_mode='Markdown')
        return
    
    try:
        target_user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ آیدی کاربر باید عدد باشد!")
        return
    
    if bot.add_user_to_whitelist(target_user_id):
        await update.message.reply_text(f"✅ کاربر `{target_user_id}` به لیست کاربران مجاز اضافه شد!", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"⚠️ کاربر `{target_user_id}` قبلاً در لیست موجود است!", parse_mode='Markdown')

async def admin_remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف کاربر از وایت لیست"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ فقط ادمین می‌تواند کاربر حذف کند!")
        return
    
    if not context.args:
        await update.message.reply_text("❌ لطفاً آیدی کاربر را وارد کنید!\n\nمثال: `/remove_user 123456789`", parse_mode='Markdown')
        return
    
    try:
        target_user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ آیدی کاربر باید عدد باشد!")
        return
    
    if bot.remove_user_from_whitelist(target_user_id):
        await update.message.reply_text(f"✅ کاربر `{target_user_id}` از لیست کاربران مجاز حذف شد!", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"⚠️ کاربر `{target_user_id}` در لیست موجود نیست!", parse_mode='Markdown')

@check_access
async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش دسته‌بندی‌ها"""
    shared_data = bot.get_shared_data()
    
    keyboard = []
    text = "📂 **دسته‌بندی‌های مشترک:**\n\n"
    
    if not shared_data['categories']:
        text += "❌ هیچ دسته‌بندی‌ای وجود ندارد!\n\n"
        text += "برای شروع، یک دسته‌بندی جدید اضافه کنید."
        keyboard = [[
            InlineKeyboardButton("➕ دسته جدید", url=f"https://t.me/{context.bot.username}?start=add_category")
        ]]
    else:
        for cat_id, category in shared_data['categories'].items():
            total_items = len(category['items'])
            completed_items = sum(1 for item in category['items'] if item['completed'])
            
            text += f"{category['icon']} **{category['name']}**\n"
            text += f"   📊 {completed_items}/{total_items} انجام شده\n"
            
            # نمایش ۵ آیتم آخر
            items = category['items']
            if items:
                # فیلتر کردن آیتم‌ها: اول غیرتکمیل‌شده‌ها، سپس تکمیل‌شده‌ها
                incomplete_items = [item for item in items if not item['completed']]
                completed_items_list = [item for item in items if item['completed']]
                
                # انتخاب ۵ آیتم آخر
                if incomplete_items:
                    display_items = incomplete_items[-5:]
                else:
                    display_items = completed_items_list[-5:]
                
                for item in display_items:
                    status = "✅" if item['completed'] else "⭕"
                    text += f"      {status} {item['text'][:30]}{'...' if len(item['text']) > 30 else ''}\n"
                
                if len(items) > 5:
                    text += f"      📝 و {len(items) - 5} آیتم دیگر...\n"
            else:
                text += "      📝 هیچ آیتمی وجود ندارد\n"
            
            text += "\n"
            keyboard.append([
                InlineKeyboardButton(
                    f"{category['icon']} {category['name']} ({total_items})",
                    callback_data=f"view_category_{cat_id}"
                )
            ])
                    
        keyboard.append([
            InlineKeyboardButton("➕ دسته جدید", url=f"https://t.me/{context.bot.username}?start=add_category"),
            InlineKeyboardButton("🗑️ حذف دسته", callback_data="delete_category_menu")
        ])

        keyboard.append([
            InlineKeyboardButton("🎬 نمره‌دهی فیلم‌ها", callback_data="movie_ratings_menu")
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def view_category(update: Update, context: ContextTypes.DEFAULT_TYPE, category_id: str):
    """نمایش آیتم‌های یک دسته"""
    shared_data = bot.get_shared_data()
    
    if category_id not in shared_data['categories']:
        await update.callback_query.answer("❌ دسته‌بندی پیدا نشد!")
        return
    
    category = shared_data['categories'][category_id]
    items = category['items']
    
    text = f"{category['icon']} **{category['name']}**\n\n"
    
    if not items:
        text += "📝 هیچ آیتمی وجود ندارد!\n\n"
        keyboard = [
            [
                InlineKeyboardButton("➕ آیتم جدید", url=f"https://t.me/{context.bot.username}?start=add_item_{category_id}")
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_categories")]
        ]
    else:
        completed_count = sum(1 for item in items if item['completed'])
        total_count = len(items)
        progress = int((completed_count / total_count) * 10) if total_count > 0 else 0
        
        text += f"📊 **پیشرفت:** {completed_count}/{total_count}\n"
        text += f"{'🟩' * progress}{'⬜' * (10 - progress)}\n\n"
        
        for item in items:
            status = "✅" if item['completed'] else "⭕"
            text += f"{status} {item['text']}\n"
            text += f"   📅 {item['created_at']}"
            if 'added_by' in item:
                text += f" • 👤 {item['added_by']}"
            text += "\n\n"
        
        keyboard = [
            [
                InlineKeyboardButton("➕ آیتم جدید", url=f"https://t.me/{context.bot.username}?start=add_item_{category_id}"),
                InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_menu_{category_id}")
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_categories")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
#    print("debug2: " , update)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, category_id: str):
    """منوی ویرایش آیتم‌ها"""
    shared_data = bot.get_shared_data()
    
    category = shared_data['categories'][category_id]
    items = category['items']
    
    if not items:
        text = f"✏️ **ویرایش آیتم‌های {category['name']}:**\n\n"
        text += "❌ هیچ آیتمی برای ویرایش وجود ندارد!\n\n"
        text += "برای شروع، یک آیتم جدید اضافه کنید."
        
        keyboard = [
            [InlineKeyboardButton("➕ آیتم جدید", url=f"https://t.me/{context.bot.username}?start=add_item_{category_id}")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"view_category_{category_id}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        return
    
    text = f"✏️ **ویرایش آیتم‌های {category['name']}:**\n\n"
    
    keyboard = []
    for item in items:
        status = "✅" if item['completed'] else "⭕"
        keyboard.append([
            InlineKeyboardButton(
                f"{status} {item['text'][:20]}{'...' if len(item['text']) > 20 else ''}",
                callback_data=f"edit_item_{category_id}_{item['id']}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت", callback_data=f"view_category_{category_id}")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def edit_item_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, category_id: str, item_id: str):
    """منوی ویرایش یک آیتم خاص"""
    shared_data = bot.get_shared_data()
    
    category = shared_data['categories'][category_id]
    item = next((item for item in category['items'] if item['id'] == item_id), None)
    
    if not item:
        await update.callback_query.answer("❌ آیتم پیدا نشد!")
        return
    
    status = "✅ انجام شده" if item['completed'] else "⭕ انجام نشده"
    text = f"✏️ **ویرایش آیتم:**\n\n"
    text += f"📝 متن: {item['text']}\n"
    text += f"📊 وضعیت: {status}\n"
    text += f"📅 تاریخ: {item['created_at']}\n"
    
    if 'added_by' in item:
        text += f"👤 اضافه شده توسط: {item['added_by']}\n"
    
    if 'last_modified_by' in item:
        text += f"✏️ آخرین تغییر: {item['last_modified_by']} در {item['last_modified_at']}\n"
    
    text += "\n"
    
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ تکمیل" if not item['completed'] else "⭕ عدم تکمیل",
                callback_data=f"toggle_item_{category_id}_{item_id}"
            )
        ],
        [
            InlineKeyboardButton("🗑️ حذف", callback_data=f"delete_item_{category_id}_{item_id}")
        ],
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data=f"edit_menu_{category_id}")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')


@check_access
async def movie_ratings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی اصلی نمره‌دهی فیلم‌ها"""
    movies = bot.get_movie_ratings()
    
    text = "🎬 **نمره‌دهی فیلم‌ها** ⭐\n\n"
    
    if not movies:
        text += "📝 هیچ فیلمی نمره‌دهی نشده است!\n\n"
        text += "برای شروع، یک فیلم نمره‌دهی کنید."
    else:
        text += f"📊 تعداد فیلم‌های نمره‌دهی شده: {len(movies)}\n\n"
        
        # نمایش 5 فیلم برتر
        sorted_movies = bot.get_movie_ratings('rating')
        top_movies = list(sorted_movies.items())[:5]
        
        text += "🏆 **برترین فیلم‌ها:**\n"
        for i, (movie, data) in enumerate(top_movies, 1):
            stars = "⭐" * int(data['average'])
            text += f"{i}. {movie} - {data['average']:.1f}/10 {stars}\n"
            text += f"   👥 {data['total_ratings']} نمره\n"
        
        if len(movies) > 5:
            text += f"\n... و {len(movies) - 5} فیلم دیگر"
    
    keyboard = [
        [
            InlineKeyboardButton("➕ نمره‌دهی جدید", url=f"https://t.me/{context.bot.username}?start=add_movie"),
            InlineKeyboardButton("📋 همه فیلم‌ها", callback_data="view_all_movies")
        ],
        [
            InlineKeyboardButton("📊 آمار", callback_data="movie_stats")
        ],
        [
            InlineKeyboardButton("🔙 منوی اصلی", callback_data="back_to_categories")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def view_all_movies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش همه فیلم‌های نمره‌دهی شده"""
    movies = bot.get_movie_ratings()
    
    if not movies:
        await update.callback_query.answer("هیچ فیلمی نمره‌دهی نشده!")
        return
    
    text = "🎬 **همه فیلم‌های نمره‌دهی شده:**\n\n"
    
    keyboard = []
    for movie, data in movies.items():
        stars = "⭐" * int(data['average'])
        text += f"🎬 {movie}\n"
        text += f"   📊 {data['average']:.1f}/10 {stars}\n"
        text += f"   👥 {data['total_ratings']} نمره\n\n"
        
        keyboard.append([
            InlineKeyboardButton(
                f"🎬 {movie[:20]}{'...' if len(movie) > 20 else ''} ({data['average']:.1f}/10)",
                callback_data=f"view_movie_{movie}"
            )
    ])
    
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت", callback_data="movie_ratings_menu")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def view_movie_details(update: Update, context: ContextTypes.DEFAULT_TYPE, movie_name: str):
    """نمایش جزئیات یک فیلم"""
    movies = bot.get_movie_ratings()
    
    if movie_name not in movies:
        await update.callback_query.answer("فیلم پیدا نشد!")
        return
    
    movie_data = movies[movie_name]
    user_id = update.effective_user.id
    
    text = f"🎬 **{movie_name}**\n\n"
    text += f"📊 **میانگین نمره:** {movie_data['average']:.1f}/10\n"
    text += f"👥 **تعداد نمره‌ها:** {movie_data['total_ratings']}\n\n"
    
    # نمایش نمره‌ها
    text += "📝 **نمره‌ها و نظرات:**\n\n"
    for rating in movie_data['ratings']:
        stars = "⭐" * rating['rating']
        text += f"👤 {rating['user_name']}\n"
        text += f"   📊 {rating['rating']}/10 {stars}\n"
        if rating['comment']:
            text += f"   💬 {rating['comment']}\n"
        text += f"   📅 {rating['date']}\n\n"
    
    # دکمه‌ها
    keyboard = []
    
    # بررسی اینکه آیا کاربر قبلا نمره داده یا نه
    user_rating = bot.get_user_movie_rating(movie_name, user_id)
    
    if user_rating:
        keyboard.append([
            InlineKeyboardButton("✏️ ویرایش نمره من", callback_data=f"edit_my_rating_{movie_name}")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton("➕ نمره‌دهی", callback_data=f"rate_movie_{movie_name}")
        ])
    
    keyboard.append([
        InlineKeyboardButton("🗑️ حذف فیلم", callback_data=f"delete_movie_{movie_name}"),
        InlineKeyboardButton("🔙 بازگشت", callback_data="view_all_movies")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def rate_movie_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, movie_name: str):
    """منوی نمره‌دهی به فیلم"""
    text = f"⭐ **نمره‌دهی به فیلم:**\n\n🎬 {movie_name}\n\n"
    text += "لطفاً نمره خود را انتخاب کنید (1-10):"
    
    keyboard = []
    
    # ساخت دکمه‌های نمره 1 تا 10
    for i in range(1, 11):
        stars = "⭐" * i
        keyboard.append([
            InlineKeyboardButton(f"{i}/10 {stars}", callback_data=f"set_rating_{movie_name}_{i}")
        ])
    
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت", callback_data=f"view_movie_{movie_name}")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def ask_for_comment(update: Update, context: ContextTypes.DEFAULT_TYPE, movie_name: str, rating: int):
    """درخواست نظر برای فیلم"""
    text = f"⭐ نمره {rating}/10 برای فیلم '{movie_name}' انتخاب شد!\n\n"
    text += "💬 نظر خود را درباره فیلم بنویسید یا روی SKIP کلیک کنید."
    
    keyboard = [[
        InlineKeyboardButton("⏩ SKIP", callback_data=f"skip_comment_{movie_name}_{rating}")
    ]]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def movie_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار فیلم‌ها"""
    movies = bot.get_movie_ratings()
    if not movies:
        await update.callback_query.answer("هیچ فیلمی نمره‌دهی نشده!")
        return
    text = "📊 **آمار فیلم‌ها:**\n\n"
    total_movies = len(movies)
    total_ratings = sum(data['total_ratings'] for data in movies.values())
    if total_ratings > 0:
        overall_average = sum(data['average'] * data['total_ratings'] for data in movies.values()) / total_ratings
    else:
        overall_average = 0
    text += f"🎬 تعداد فیلم‌ها: {total_movies}\n"
    text += f"📊 تعداد کل نمره‌ها: {total_ratings}\n"
    text += f"⭐ میانگین کلی: {overall_average:.1f}/10\n\n"
    if movies:
        best_movie = max(movies.items(), key=lambda x: x[1]['average'])
        text += f"🏆 **بهترین فیلم:**\n"
        text += f"   🎬 {best_movie[0]}\n"
        text += f"   ⭐ {best_movie[1]['average']:.1f}/10\n\n"
    rating_distribution = {}
    for movie_data in movies.values():
        for rating in movie_data['ratings']:
            score = rating['rating']
            rating_distribution[score] = rating_distribution.get(score, 0) + 1
    if rating_distribution:
        text += "📈 **توزیع نمره‌ها:**\n"
        for score in sorted(rating_distribution.keys(), reverse=True):
            count = rating_distribution[score]
            bars = "█" * min(count, 10)
            text += f"   {score}/10: {bars} ({count})\n"
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="movie_ratings_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def inline_query(update: Update, context):
    query = update.inline_query.query
    user_id = update.effective_user.id
    
    results = []
    
    if not query:
        # اضافه کردن دستور Film_Rate
        movied = bot.get_movie_ratings('rating')  # دریافت فیلم‌ها به صورت مرتب شده
        movie_text = '🎬 **لیست برترین فیلم‌ها**\n\n'
        
        # انتخاب 5 فیلم برتر
        top_movies = list(movied.items())[:5]
        
        if top_movies:
            for i, (movie, data) in enumerate(top_movies, 1):
                stars = "⭐" * int(data['average'])
                movie_text += f"{'═' * 35}\n"
                movie_text += f"**{i}. {movie}**\n"
                movie_text += f"📊 میانگین: {data['average']:.1f}/10 {stars}\n"
                movie_text += f"👥 تعداد نمره‌ها: {data['total_ratings']}\n\n"
                movie_text += "**نمره‌های کاربران:**\n"
                
                # مرتب‌سازی نمره‌ها بر اساس تاریخ (جدیدترین اول)
                sorted_ratings = sorted(data['ratings'], key=lambda x: x['date'], reverse=True)
                
                for rating in sorted_ratings:
                    user_stars = "⭐" * rating['rating']
                    movie_text += f"• {rating['user_name']}: {rating['rating']}/10 {user_stars}\n"
                    if rating['comment']:
                        movie_text += f"  💬 {rating['comment']}\n"
                movie_text += "\n"
            
            movie_text += f"{'═' * 35}\n"
            movie_text += "\n📝 برای مشاهده همه فیلم‌ها از دکمه‌های زیر استفاده کنید."
        else:
            movie_text = "هیچ فیلمی هنوز نمره‌دهی نشده است!"

        # دکمه‌های مربوط به فیلم
        movie_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ نمره‌دهی جدید", callback_data="show_unrated_movies"),
             InlineKeyboardButton("📋 همه فیلم‌ها", callback_data="view_all_movies")],
            [InlineKeyboardButton("📊 آمار", callback_data="movie_stats")]
        ])
        
        results.append(InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="🎬 نمایش لیست فیلم‌ها و نمرات",
            description="کلیک کنید تا لیست همه فیلم‌ها و نمرات آنها را ببینید",
            input_message_content=InputTextMessageContent(
                message_text=movie_text,
                parse_mode='Markdown'
            ),
            reply_markup=movie_keyboard
        ))
        
        # اضافه کردن همه دسته‌بندی‌ها
        shared_data = bot.get_shared_data()
        categories = shared_data['categories']
        
        for cat_id, category in categories.items():
            # فیلتر کردن آیتم‌های تیک نخورده
            uncompleted_items = [item for item in category['items'] if not item['completed']]
            total_items = len(category['items'])
            uncompleted_count = len(uncompleted_items)
            
            text = f"{category['icon']} **{category['name']}**\n\n"
            text += f"📊 وضعیت: {total_items - uncompleted_count}/{total_items} تکمیل شده\n\n"
            
            if uncompleted_items:
                text += "📝 **آیتم‌های انجام نشده:**\n\n"
                for item in uncompleted_items:
                    text += f"⭕ {item['text']}\n"
                    text += f"📅 {item['created_at']}"
                    if 'added_by' in item:
                        text += f" • 👤 {item['added_by']}"
                    text += "\n\n"
            else:
                text += "✅ همه آیتم‌ها تکمیل شده‌اند!"

            # دکمه‌های مربوط به هر دسته‌بندی
            category_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ آیتم جدید", url=f"https://t.me/{context.bot.username}?start=add_item_{cat_id}"),
                 InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_menu_{cat_id}")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_categories")]
            ])
            
            results.append(InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"{category['icon']} {category['name']} ({len(uncompleted_items)} آیتم)",
                description=f"تکمیل شده: {total_items - uncompleted_count}/{total_items}",
                input_message_content=InputTextMessageContent(
                    message_text=text,
                    parse_mode='Markdown'
                ),
                reply_markup=category_keyboard
            ))
    
    elif query.strip():  # اگر کوئری خالی نباشد
        shared_data = bot.get_shared_data()
        categories = shared_data['categories']
        
        # جستجو در دسته‌بندی‌ها
        for cat_id, category in categories.items():
            if query.lower() in category['name'].lower():
                # فیلتر کردن آیتم‌های تیک نخورده
                uncompleted_items = [item for item in category['items'] if not item['completed']]
                
                if uncompleted_items:
                    text = f"{category['icon']} **{category['name']}**\n\n"
                    text += "📝 **آیتم‌های انجام نشده:**\n\n"
                    
                    for item in uncompleted_items:
                        text += f"⭕ {item['text']}\n"
                        text += f"📅 {item['created_at']}"
                        if 'added_by' in item:
                            text += f" • 👤 {item['added_by']}"
                        text += "\n\n"

                    # دکمه‌های مربوط به دسته‌بندی
                    category_keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("➕ آیتم جدید", url=f"https://t.me/{context.bot.username}?start=add_item_{cat_id}"),
                         InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_menu_{cat_id}")],
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_categories")]
                    ])
                    
                    results.append(InlineQueryResultArticle(
                        id=str(uuid.uuid4()),
                        title=f"{category['icon']} {category['name']} ({len(uncompleted_items)} آیتم)",
                        description=f"نمایش {len(uncompleted_items)} آیتم انجام نشده",
                        input_message_content=InputTextMessageContent(
                            message_text=text,
                            parse_mode='Markdown'
                        ),
                        reply_markup=category_keyboard
                    ))

    await update.inline_query.answer(results, cache_time=0)
        
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت دکمه‌ها"""
    query = update.callback_query
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "کاربر"
    
    # بررسی دسترسی
    if not bot.is_user_allowed(user_id):
        await query.answer("❌ شما مجاز به استفاده از این ربات نیستید!")
        return
    
    await query.answer()
    
    data = query.data
    
    print(f"DEBUG: Button pressed: {data}")  # برای دیباگ
    
    if data == "back_to_categories":
        await show_categories(update, context)
    
    elif data.startswith("view_category_"):
        category_id = data.split("_")[-1]
        await view_category(update, context, category_id)
    
    elif data.startswith("edit_menu_"):
        category_id = data.split("_")[-1]
        await edit_menu(update, context, category_id)
    
    elif data.startswith("edit_item_"):
        parts = data.split("_")
        category_id = parts[2]
        item_id = parts[3]
        await edit_item_menu(update, context, category_id, item_id)
    
    elif data.startswith("toggle_item_"):
        parts = data.split("_")
        category_id = parts[2]
        item_id = parts[3]
        
        success = bot.toggle_item(category_id, item_id, user_name)
        if success:
            await query.answer("✅ وضعیت تغییر کرد!")
            await edit_item_menu(update, context, category_id, item_id)
        else:
            await query.answer("❌ خطا در تغییر وضعیت!")
    
    elif data.startswith("delete_item_"):
        parts = data.split("_")
        category_id = parts[2]
        item_id = parts[3]
        
        success = bot.delete_item(category_id, item_id)
        if success:
            await query.answer("✅ آیتم حذف شد!")
            await edit_menu(update, context, category_id)
        else:
            await query.answer("❌ خطا در حذف آیتم!")
    
    elif data.startswith("add_item_"):
        category_id = data.split("_")[-1]
        context.user_data['waiting_for_item'] = category_id
        await query.edit_message_text("📝 متن آیتم جدید را بنویسید:")
    
    elif data == "add_category":
        context.user_data['waiting_for_category'] = True
        await query.edit_message_text("📝 نام دسته‌بندی جدید را بنویسید:")
    
    elif data == "delete_category_menu":
        await delete_category_menu(update, context)
    
    elif data.startswith("confirm_delete_category_"):
        category_id = data.split("_")[-1]
        success = bot.delete_category(category_id)
        if success:
            await query.answer("✅ دسته‌بندی حذف شد!")
            await show_categories(update, context)
        else:
            await query.answer("❌ خطا در حذف دسته‌بندی!")

    elif data == "movie_ratings_menu":
        await movie_ratings_menu(update, context)

    elif data == "add_movie_rating":
        context.user_data['waiting_for_movie_name'] = True
        await query.edit_message_text("🎬 نام فیلم را وارد کنید:")

    elif data == "view_all_movies":
        await view_all_movies(update, context)

    elif data.startswith("view_movie_"):
        movie_name = data[11:]  # حذف "view_movie_"
        await view_movie_details(update, context, movie_name)

    elif data.startswith("rate_movie_"):
        movie_name = data[11:]  # حذف "rate_movie_"
        await rate_movie_menu(update, context, movie_name)

    elif data.startswith("set_rating_"):
        parts = data.split("_")
        movie_name = "_".join(parts[2:-1])  # نام فیلم
        rating = int(parts[-1])  # نمره
        
        await ask_for_comment(update, context, movie_name, rating)
        await query.answer(f"⭐ نمره {rating} انتخاب شد!")
        return

    elif data.startswith("delete_movie_"):
        movie_name = data[13:]  # حذف "delete_movie_"
        success = bot.delete_movie_rating(movie_name)
        if success:
            await query.answer("✅ فیلم حذف شد!")
            await view_all_movies(update, context)
        else:
            await query.answer("❌ خطا در حذف فیلم!")

    elif data.startswith("edit_my_rating_"):
        movie_name = data[15:]  # حذف "edit_my_rating_"
        await rate_movie_menu(update, context, movie_name)

    elif data == "movie_stats":
        await movie_stats(update, context)
        
    elif data == "show_unrated_movies":
        user_id = update.effective_user.id
        movied = bot.get_movie_ratings()
        
        # پیدا کردن فیلم‌هایی که کاربر هنوز نمره نداده
        unrated_movies = []
        for movie_name, data in movied.items():
            user_rating = bot.get_user_movie_rating(movie_name, user_id)
            if not user_rating:
                unrated_movies.append((movie_name, data))
        
        text = "🎬 **فیلم‌های نمره داده نشده:**\n\n"
        keyboard = []
        
        if unrated_movies:
            for movie, data in unrated_movies:
                stars = "⭐" * int(data['average'])
                text += f"• {movie}\n"
                text += f"  📊 میانگین: {data['average']:.1f}/10 {stars}\n"
                text += f"  👥 تعداد نمره‌ها: {data['total_ratings']}\n\n"
                keyboard.append([
                    InlineKeyboardButton(f"نمره دادن به {movie[:20]}{'...' if len(movie) > 20 else ''}", 
                                       callback_data=f"rate_movie_{movie}")
                ])
        else:
            text += "✅ شما به همه فیلم‌ها نمره داده‌اید!\n\n"
            text += "برای اضافه کردن فیلم جدید از دکمه زیر استفاده کنید."
        
        keyboard.append([
            InlineKeyboardButton("➕ افزودن فیلم جدید", url=f"https://t.me/{context.bot.username}?start=add_movie")
        ])
        keyboard.append([
            InlineKeyboardButton("🔙 بازگشت", callback_data="movie_ratings_menu")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif data.startswith("sort_movies_"):
        sort_type = data[12:]  # name یا rating
        movies = bot.get_movie_ratings(sort_type)
        await view_all_movies(update, context)
    
    elif data.startswith("skip_comment_"):
        parts = data.split("_")
        movie_name = parts[2]
        rating = int(parts[3])
        
        success = bot.add_movie_rating(movie_name, rating, "", user_name, user_id)
        
        if success:
            await query.answer("✅ نظر رد شد!")
            await view_movie_details(update, context, movie_name)
        else:
            await query.answer("❌ خطا در رد کردن نظر!")
    
    else:
        await query.answer("❌ دکمه ناشناخته!")
        print(f"UNKNOWN BUTTON: {data}")



async def delete_category_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی حذف دسته‌بندی"""
    shared_data = bot.get_shared_data()
    
    if not shared_data['categories']:
        await update.callback_query.answer("❌ هیچ دسته‌بندی‌ای برای حذف وجود ندارد!")
        await show_categories(update, context)
        return
    
    text = "🗑️ **حذف دسته‌بندی:**\n\n⚠️ توجه: با حذف دسته‌بندی، تمام آیتم‌های آن نیز حذف خواهند شد!\n\n"
    text += "کدام دسته‌بندی را می‌خواهید حذف کنید؟\n\n"
    
    keyboard = []
    for cat_id, category in shared_data['categories'].items():
        item_count = len(category['items'])
        keyboard.append([
            InlineKeyboardButton(
                f"🗑️ {category['icon']} {category['name']} ({item_count} آیتم)",
                callback_data=f"confirm_delete_category_{cat_id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_categories")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')


@check_access
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت پیام‌های متنی"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "کاربر"
    text = update.message.text
    
    # اضافه کردن آیتم جدید
    if 'waiting_for_item' in context.user_data:
        category_id = context.user_data['waiting_for_item']
        success = bot.add_item(category_id, text, user_name)
        
        if success:
            await update.message.reply_text(f"✅ آیتم '{text}' اضافه شد!")
            del context.user_data['waiting_for_item']
            
            # نمایش دسته‌بندی مجدد
            shared_data = bot.get_shared_data()
            category = shared_data['categories'][category_id]
            
            keyboard = [[
                InlineKeyboardButton("👁️ مشاهده دسته", callback_data=f"view_category_{category_id}"),
                InlineKeyboardButton("📂 همه دسته‌ها", callback_data="back_to_categories")
            ]]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"آیتم به دسته {category['icon']} {category['name']} اضافه شد.",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text("❌ خطا در اضافه کردن آیتم!")
            del context.user_data['waiting_for_item']
    
    # اضافه کردن دسته‌بندی جدید
    elif 'waiting_for_category' in context.user_data:
        # اگر پیام شامل آیکون باشد
        if len(text) > 2 and text[0] in '🎬📚🎮🍔🎵🏠🚗✈️🎯📱💼🏋️🎨📖🌟':
            icon = text[0]
            name = text[1:].strip()
        else:
            icon = '⭐'
            name = text.strip()
        
        cat_id = bot.add_category(name, icon)
        await update.message.reply_text(f"✅ دسته‌بندی '{icon} {name}' اضافه شد!")
        del context.user_data['waiting_for_category']
        
        keyboard = [[
            InlineKeyboardButton("👁️ مشاهده دسته", callback_data=f"view_category_{cat_id}"),
            InlineKeyboardButton("📂 همه دسته‌ها", callback_data="back_to_categories")
        ]]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "دسته‌بندی جدید ایجاد شد!",
            reply_markup=reply_markup
        )
    elif 'waiting_for_movie_name' in context.user_data:
        movie_name = text.strip()
        context.user_data['temp_movie_name'] = movie_name
        del context.user_data['waiting_for_movie_name']
        
        # بررسی اینکه آیا کاربر قبلا برای این فیلم نمره داده یا نه
        user_rating = bot.get_user_movie_rating(movie_name, user_id)
        
        if user_rating:
            await update.message.reply_text(
                f"⚠️ شما قبلاً برای فیلم '{movie_name}' نمره {user_rating['rating']}/10 داده‌اید!\n\n"
                f"آیا می‌خواهید نمره خود را تغییر دهید؟",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ بله", callback_data=f"rate_movie_{movie_name}"),
                    InlineKeyboardButton("❌ خیر", callback_data="movie_ratings_menu")
                ]])
            )
        else:
            await rate_movie_menu(update, context, movie_name)

    # نمره‌دهی فیلم - مرحله دوم: نظر
    elif 'waiting_for_comment' in context.user_data:
        movie_name = context.user_data['temp_movie_name']
        rating = context.user_data['temp_rating']
        
        comment = ""
        if text.lower() not in ['رد', 'skip', '-']:
            comment = text.strip()
        
        success = bot.add_movie_rating(movie_name, rating, comment, user_name, user_id)
        
        if success:
            await update.message.reply_text(
                f"✅ نمره شما ثبت شد!\n\n"
                f"🎬 فیلم: {movie_name}\n"
                f"⭐ نمره: {rating}/10\n"
                f"💬 نظر: {comment if comment else 'بدون نظر'}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🎬 نمایش فیلم", callback_data=f"view_movie_{movie_name}"),
                    InlineKeyboardButton("📋 همه فیلم‌ها", callback_data="view_all_movies")
                ]])
            )
        else:
            await update.message.reply_text("❌ خطا در ثبت نمره!")
        
        # پاک کردن داده‌های موقت
        del context.user_data['temp_movie_name']
        del context.user_data['temp_rating']
        del context.user_data['waiting_for_comment']

    else:
        # پیام عادی
        help_text = "👋 سلام! از دستورات زیر استفاده کنید:\n\n"
        help_text += "• /categories - نمایش دسته‌بندی‌ها\n"
        help_text += "• /add_category - اضافه کردن دسته جدید\n"
        help_text += "• /help - راهنما\n"
        
        if user_id == ADMIN_ID:
            help_text += "\n👑 **دستورات ادمین:**\n"
            help_text += "• /whitelist - مدیریت کاربران مجاز\n"
            help_text += "• /add_user [user_id] - اضافه کردن کاربر\n"
            help_text += "• /remove_user [user_id] - حذف کاربر\n"
        
        await update.message.reply_text(help_text)

def main():
    """شروع ربات"""
    print("🚀 ربات مدیریت ویش لیست مشترک در حال راه‌اندازی...")
    print(f"👑 آیدی ادمین: {ADMIN_ID}")
    
    # بررسی و تنظیم آیدی ادمین
    if ADMIN_ID == 123456789:
        print("⚠️ هشدار: لطفاً آیدی ادمین را در متغیر ADMIN_ID تنظیم کنید!")
        print("💡 برای دریافت آیدی تلگرام خود، به ربات @userinfobot پیام دهید")
    
    # ایجاد application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # اضافه کردن handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("categories", show_categories))
    application.add_handler(CommandHandler("add_category", lambda update, context: context.user_data.update({'waiting_for_category': True}) or update.message.reply_text("📝 نام دسته‌بندی جدید را بنویسید:")))
    application.add_handler(CommandHandler("movies", movie_ratings_menu))
    # handlers ادمین
    application.add_handler(CommandHandler("whitelist", admin_whitelist))
    application.add_handler(CommandHandler("add_user", admin_add_user))
    application.add_handler(CommandHandler("remove_user", admin_remove_user))
    application.add_handler(InlineQueryHandler(inline_query))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("✅ ربات آماده است!")
    print("\n📋 دستورات کاربران:")
    print("   /start - شروع ربات")
    print("   /categories - نمایش دسته‌بندی‌ها")
    print("   /add_category - اضافه کردن دسته جدید")
    print("   /help - راهنما")
    print("\n👑 دستورات ادمین:")
    print("   /whitelist - مدیریت کاربران مجاز")
    print("   /add_user [user_id] - اضافه کردن کاربر")
    print("   /remove_user [user_id] - حذف کاربر")
    print("\n🤝 ویژگی‌ها:")
    print("   • سیستم وایت لیست برای کنترل دسترسی")
    print("   • ویش لیست مشترک بین کاربران مجاز")
    print("   • ردیابی کاربر اضافه‌کننده هر آیتم")
    print("   • مدیریت کامل توسط ادمین")
    
    # شروع ربات
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
