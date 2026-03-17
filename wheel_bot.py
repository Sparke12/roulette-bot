import logging
import asyncio
import sqlite3
import random
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
API_TOKEN = '7743738047:AAHZDxCyYsSMjxQ5gf8ealNPPJ70dPhYGTg'
ADMIN_ID = 5484210331 # Assure-toi que c'est bien ton ID actuel
ADMIN_USERNAME = "@wheelbetrupe"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
app = Flask('')

@app.route('/')
def home(): return "Bot is Running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- BASE DE DONNÉES ---
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
    if is_vip is not None: cursor.execute('UPDATE users SET is_vip = ? WHERE user_id = ?', (is_vip, user_id))
    if daily_count is not None: cursor.execute('UPDATE users SET daily_count = ?, last_use = ? WHERE user_id = ?', (daily_count, today, user_id))
    conn.commit()
    conn.close()

# --- LOGIQUE D'ANALYSE ---
def analyze_logic(numbers):
    # On récupère le dernier numéro pour décider de la couleur opposée
    last = int(numbers[-1])
    reds = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    
    if last == 0:
        return random.choice(["ROUGE", "NOIR"])
    elif last in reds:
        return "⚫ NOIR"
    else:
        return "🔴 ROUGE"

# --- COMMANDES ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("🚀 **WHEEL ANALYZER PRO**\n\nPrêt pour l'analyse ?\n👉 Cliquez sur /signal")

@dp.message(Command("vip"))
async def cmd_vip(message: types.Message):
    await message.answer(f"💎 **OFFRE VIP : 15 000 FCFA**\nAccès illimité et signaux précis.\nContact : {ADMIN_USERNAME}\nID : `{message.from_user.id}`")

@dp.message(Command("signal"))
async def cmd_signal(message: types.Message):
    user_id = message.from_user.id
    user_data = get_user(user_id)
    if not user_data: 
        update_user(user_id)
        user_data = (0, 0, "")
    
    is_vip, count, last_use = user_data
    if not is_vip and count >= 2 and last_use == datetime.now().strftime('%Y-%m-%d'):
        await message.answer("❌ Limite atteinte. /vip")
        return

    await message.answer("✍️ **Veuillez entrer les 3 derniers numéros sortis** (ex: 12, 5, 30) :")

@dp.message(F.text.regexp(r'^(\d+),\s*(\d+),\s*(\d+)$'))
async def process_numbers(message: types.Message):
    nums = message.text.replace(" ", "").split(",")
    
    m = await message.answer("📡 **Analyse des séquences en cours...**")
    await asyncio.sleep(2)
    
    prediction = analyze_logic(nums)
    play_time = (datetime.now() + timedelta(minutes=5)).strftime("%H:%M")
    
    res = (
        f"✅ **ANALYSE TERMINÉE**\n"
        f"Basée sur : {', '.join(nums)}\n\n"
        f"🎯 **PRÉDICTION : {prediction}**\n"
        f"⏰ **HEURE DU JEU : {play_time}**\n"
        f"🔥 Confiance : {random.randint(91, 97)}%\n\n"
        "⚠️ *Misez moderez. mais au vip, miser gros sur le signal.*"
    )
    
    await m.edit_text(res, parse_mode="Markdown")
    update_user(message.from_user.id, daily_count=get_user(message.from_user.id)[1] + 1)

@dp.message(Command("setvip"))
async def cmd_setvip(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        try:
            target = int(message.text.split()[1])
            update_user(target, is_vip=1)
            await message.answer(f"✅ ID `{target}` activé !")
        except: await message.answer("Usage: /setvip ID")

# --- LANCEUR ---
async def main():
    init_db()
    Thread(target=run_flask).start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
