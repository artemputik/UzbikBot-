from flask import Flask, request
import telebot
import sqlite3
import os
import requests

# ==================== НАСТРОЙКИ ====================
TELEGRAM_TOKEN = os.environ.get('BOT_TOKEN', "8366285540:AAFFnzLCJapG71eO8PatI_DmOkwBKEZNhHw")
YOUTUBE_URL = "https://youtube.com/@uzbik_of?si=H4sMvZ37sHI8vJhp"

# ==================== БАЗА ДАННЫХ ====================
DB_PATH = "uzbik_bot.db"

def init_database():
    """Инициализация базы данных"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            username TEXT,
            message_text TEXT,
            platform TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.commit()
        conn.close()
        print(f"✅ База данных готова: {DB_PATH}")
    except Exception as e:
        print(f"❌ Ошибка базы: {e}")

def save_message(user_id, username, message_text, platform="telegram"):
    """Сохраняет сообщение в базу"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (user_id, username, message_text, platform) VALUES (?, ?, ?, ?)",
            (user_id, username, message_text, platform)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return False

# Инициализируем базу
init_database()

# ==================== TELEGRAM БОТ ====================
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# ==================== КОМАНДЫ TELEGRAM ====================
@bot.message_handler(commands=['start'])
def start(message):
    save_message(message.from_user.id, message.from_user.first_name, "/start")
    
    text = """
🤖 <b>Бот-помощник Uzbik</b>

🎥 <b>YouTube канал:</b>
/yt - Ссылка на наш YouTube

💬 <b>Просто спроси:</b>
"ссылка" или "где ссылка?"

📊 <b>Статистика:</b>
/stats - Моя статистика
    """
    bot.send_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['yt', 'youtube', 'канал'])
def youtube_link(message):
    save_message(message.from_user.id, message.from_user.first_name, "/yt")
    
    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton("🎥 Наш YouTube", url=YOUTUBE_URL)
    markup.add(btn)
    bot.send_message(message.chat.id, "📺 Подписывайся:", reply_markup=markup)

@bot.message_handler(commands=['stats'])
def stats(message):
    save_message(message.from_user.id, message.from_user.first_name, "/stats")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM messages WHERE user_id = ?", (message.from_user.id,))
    user_messages = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM messages")
    total_messages = cursor.fetchone()[0]
    conn.close()
    
    bot.send_message(
        message.chat.id, 
        f"📊 <b>Статистика:</b>\n"
        f"👤 Ваших сообщений: {user_messages}\n"
        f"📨 Всего сообщений: {total_messages}",
        parse_mode='HTML'
    )

@bot.message_handler(content_types=['text'])
def handle_text(message):
    save_message(message.from_user.id, message.from_user.first_name, message.text)
    
    text_lower = message.text.lower()
    if any(phrase in text_lower for phrase in ['можно ссылку?', 'где ссылка?', 'ссылка', 'название канала какое?']):
        bot.send_message(message.chat.id, f"🎥 Вот ссылка: {YOUTUBE_URL}")

# ==================== WEBHOOK ДЛЯ KOYEB ====================
@app.route('/')
def home():
    return "🤖 Бот @uzbikoff_bot работает на Koyeb! 🚀"

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Forbidden', 403

# ==================== ЗАПУСК ====================
if __name__ == '__main__':
    # Для локального тестирования
    print("🚀 Запускаю Uzbik бота...")
    bot.remove_webhook()
    bot.polling(none_stop=True)
