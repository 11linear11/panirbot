# 🎉 PaNIrBot

PaNIrBot is a **Telegram bot** for managing a **shared wishlist** and **movie rating system**.  
Only whitelisted users can create categories, add items, mark them as done, or rate movies.

---

## ✨ Features
- 📂 Create and manage categories and items
- ✅ Mark items as completed
- ✏️ Edit or delete items
- 🤝 Shared wishlist across authorized users
- 🎬 Rate movies and add comments
- 👑 Whitelist system for access control

---

## ⚠️ Important
Before running the bot, you must edit `bot/panirbot.py` and set:

```python
BOT_TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 123456789  # Your Telegram user ID
```

---

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/11linear11/panirbot.git
cd panirbot
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
- Open `bot/panirbot.py`
- Set your **Telegram Bot Token** in `BOT_TOKEN`
- Set your **Admin ID** in `ADMIN_ID` (use [@userinfobot](https://t.me/userinfobot) to get it)

### 4. Run the bot
```bash
python bot/panirbot.py
```

---

## 🚀 Usage

### User commands
- `/start` – Start the bot
- `/categories` – Show all categories
- `/add_category` – Add a new category
- `/movies` – Rate and view movies
- `/help` – Show help

### Admin commands
- `/whitelist` – Manage allowed users
- `/add_user [user_id]` – Add a user
- `/remove_user [user_id]` – Remove a user

---

## 🐳 Docker

If you prefer Docker, a `Dockerfile` is included.  
Build and run with:

```bash
docker build -t panirbot .
docker run -d --name panirbot panirbot
```

---

## 👤 Author
[11linear11](https://github.com/11linear11)
