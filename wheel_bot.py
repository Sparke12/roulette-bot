import logging
import asyncio
import sqlite3
import random
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
API_TOKEN = '7743738047:AAHZDxCyYsSMjxQ5gf8ealNPPJ70dPhYGTg'
ADMIN_ID = 702681 
ADMIN_USERNAME = "@wheelbetrupe"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
app = Flask('')

# --- SERVEUR WEB POUR RENDER ---
@app.route('/')
def home():
    return "Bot is Running!"

def run_flask():
    # Render utilise la variable d'environnement PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- LOGIQUE DU BOT (Gardée identique) ---
def init_db():
    conn = sqlite3.connect('wheel_database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, is_vip INTEGER DEFAULT 0, daily_count INTEGER DEFAULT 0, last_use TEXT)''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('wheel_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT is_vip, daily_count, last_use FROM users WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res

def update_user(user_id, is_vip=None, daily_count=None):
    conn = sqlite3.connect('wheel_database.db')
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    if not get_user(user_id):
        cursor.execute('INSERT INTO users (user_id, is_vip, daily_count, last_use) VALUES (?, 0, 0, ?)', (user_id, today))
    if is_vip is not None:
        cursor.execute('UPDATE users SET is_vip = ? WHERE user_id = ?', (is_vip, user_id))
    if daily_count is not None:
        cursor.execute('UPDATE users SET daily_count = ?, last_use = ? WHERE user_id = ?', (daily_count, today, user_id))
    conn.commit()
    conn.close()

async def generate_schedule(is_vip=False):
    now = datetime.now()
    opt2 = ["🔴 ROUGE", "⚫ NOIR", "PAIR", "IMPAIR", "MANQUE", "PASSE"]
    opt3 = ["P12", "M12", "D12", "Col 1", "Col 2", "Col 3"]
    nb = 4 if is_vip else 1
    texte = "📊 **CALENDRIER DE PRÉDICTIONS**\n━━━━━━━━━━━━━━━━━━\n"
    for i in range(1, nb + 1):
        h = (now + timedelta(minutes=i * 10)).strftime("%H:%M")
        pred = random.choice(opt2 if random.random() > 0.5 else opt3)
        texte += f"⏰ **{h}** : {pred}\n🔥 Fiabilité : {random.randint(85,98)}%\n------------------\n"
    if not is_vip: texte += "\n💡 /vip pour 4 signaux !"
    return texte

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("🚀 **WHEEL PREDICTOR**\n\n🎁 Gratuit : 2/jour\n💎 VIP : Illimité\n👉 /signal")

@dp.message(Command("signal"))
async def cmd_signal(message: types.Message):
    user_id = message.from_user.id
    user_data = get_user(user_id)
    today = datetime.now().strftime('%Y-%m-%d')
    if not user_data: 
        update_user(user_id, daily_count=0)
        user_data = (0, 0, today)
    is_vip, daily_count, last_use = user_data
    if last_use != today: update_user(user_id, daily_count=0)
    if not is_vip and daily_count >= 2:
        await message.answer("❌ Limite gratuite atteinte. /vip")
        return
    m = await message.answer("🔍 Analyse...")
    await asyncio.sleep(2)
    res = await generate_schedule(bool(is_vip))
    await m.edit_text(res, parse_mode="Markdown")
    if not is_vip: update_user(user_id, daily_count=daily_count + 1)

@dp.message(Command("setvip"))
async def cmd_setvip(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        try:
            target = int(message.text.split()[1])
            update_user(target, is_vip=1)
            await message.answer(f"✅ ID `{target}` est VIP !")
        except: await message.answer("Usage: /setvip ID")

# --- LANCEMENT ---
async def main():
    init_db()
    # Lancer Flask dans un thread séparé
    Thread(target=run_flask).start()
    print("🤖 Bot démarré avec serveur web !")
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
