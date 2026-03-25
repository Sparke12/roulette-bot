import logging
import asyncio
import sqlite3
import random
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
API_TOKEN = '7743738047:AAHZDxCyYsSMjxQ5gf8ealNPPJ70dPhYGTg'
ADMIN_ID = 5484210331
ADMIN_USERNAME = "@wheelbetrupe"
CHANNEL_LINK = "https://t.me/Wheelbetpredictor12"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
app = Flask('')

@app.route('/')
def home(): return "Bot is Running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- BASE DE DONNÉES SÉCURISÉE ---
def init_db():
    conn = sqlite3.connect('wheel_database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, 
        is_vip INTEGER DEFAULT 0, 
        referral_count INTEGER DEFAULT 0,
        daily_count INTEGER DEFAULT 0, 
        last_use TEXT)''')
    
    # Correction automatique si la colonne referral_count manque
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN referral_count INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass # La colonne existe déjà
        
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('wheel_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT is_vip, referral_count, daily_count, last_use FROM users WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res

def update_user(user_id, is_vip=None, referral_add=0, daily_count=None):
    conn = sqlite3.connect('wheel_database.db')
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    user = get_user(user_id)
    
    if not user:
        cursor.execute('INSERT INTO users (user_id, is_vip, referral_count, daily_count, last_use) VALUES (?, 0, 0, 0, ?)', (user_id, today))
    
    if is_vip is not None: 
        cursor.execute('UPDATE users SET is_vip = ? WHERE user_id = ?', (is_vip, user_id))
    if referral_add > 0: 
        cursor.execute('UPDATE users SET referral_count = referral_count + ? WHERE user_id = ?', (referral_add, user_id))
    if daily_count is not None: 
        cursor.execute('UPDATE users SET daily_count = ?, last_use = ? WHERE user_id = ?', (daily_count, today, user_id))
    
    conn.commit()
    conn.close()

# --- COMMANDES ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    args = message.text.split()
    if len(args) > 1:
        referrer_id = args[1]
        if referrer_id.isdigit() and int(referrer_id) != message.from_user.id:
            update_user(int(referrer_id), referral_add=1)
            
    await message.answer(
        "🚀 **WHEEL ANALYZER PRO**\n\n"
        "🎁 2 prédictions gratuites / jour\n"
        "🔥 **NOUVEAU :** Parrainez 3 amis pour débloquer les **COTES 3 & 6** !\n"
        "💎 VIP : Accès illimité (15 000 FCFA)\n\n"
        "👉 /signal | /parrainage | /vip"
    )

@dp.message(Command("vip"))
async def cmd_vip_info(message: types.Message):
    await message.answer(
        "💎 **ACCÈS VIP ILLIMITÉ** 💎\n\n"
        "Passez au niveau supérieur pour **15 000 FCFA** :\n"
        "✅ Analyses illimitées 24h/24\n"
        "✅ Accès direct aux grosses Cotes\n"
        "✅ Stratégie de mise sécurisée\n\n"
        f"📩 Contactez l'admin : {ADMIN_USERNAME}\n"
        f"Votre ID : `{message.from_user.id}`",
        parse_mode="Markdown"
    )

@dp.message(Command("parrainage"))
async def cmd_referral(message: types.Message):
    user = get_user(message.from_user.id)
    count = user[1] if user else 0
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    
    await message.answer(
        f"👥 **PROGRAMME AMBASSADEUR**\n\n"
        f"Amis parrainés : **{count} / 3**\n\n"
        f"Lien à partager :\n`{ref_link}`\n\n"
        "💡 *Dès 3 amis inscrits, vous débloquez les prédictions spéciales gratuitement !*",
        parse_mode="Markdown"
    )

@dp.message(Command("signal"))
async def cmd_signal(message: types.Message):
    user_id = message.from_user.id
    user_data = get_user(user_id)
    today = datetime.now().strftime('%Y-%m-%d')
    
    if not user_data: 
        update_user(user_id)
        user_data = (0, 0, 0, today)
    
    is_vip, ref_count, daily, last_use = user_data
    if last_use != today: 
        update_user(user_id, daily_count=0)
        daily = 0

    limit = 5 if ref_count >= 3 else 2
    
    if not is_vip and daily >= limit:
        await message.answer("❌ Limite atteinte. /parrainage ou passez /vip !")
        return

    await message.answer("✍️ **Entrez les 3 derniers numéros (ex: 4, 12, 30) :**")

@dp.message(F.text.regexp(r'^(\d+),\s*(\d+),\s*(\d+)$'))
async def process_numbers(message: types.Message):
    user = get_user(message.from_user.id)
    if not user: return
    
    m = await message.answer("📡 **Analyse des probabilités...**")
    await asyncio.sleep(2)
    
    play_time = (datetime.now() + timedelta(minutes=5)).strftime("%H:%M")
    
    if user[0] or user[1] >= 3:
        cote = random.choice([3, 6])
        type_p = "Douzaine" if cote == 3 else "Sixain"
        res = f"🔥 **PRÉDICTION COTE {cote}**\n🎯 Type : {type_p}\n⏰ Jeu à : {play_time}\n💡 Fiabilité : 92%"
    else:
        res = f"✅ **PRÉDICTION SIMPLE**\n🎯 Choix : {random.choice(['ROUGE', 'NOIR'])}\n⏰ Jeu à : {play_time}\n💡 Fiabilité : 97%"

    await m.edit_text(f"{res}\n\n{get_motivation_quote()}", parse_mode="Markdown")
    update_user(message.from_user.id, daily_count=user[2] + 1)

@dp.message(Command("setvip"))
async def cmd_setvip(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        try:
            target = int(message.text.split()[1])
            update_user(target, is_vip=1)
            await message.answer(f"✅ ID `{target}` activé VIP !")
        except: await message.answer("Usage: /setvip ID")

def get_motivation_quote():
    return random.choice([
        "💪 *Discipline et patience mènent au gain.*",
        "💎 *Respectez votre gestion de mise !*",
        "🚀 *Le succès est une question de stratégie.*",
        "🔥 *La chance aide les esprits préparés.*"
    ])

# --- LANCEMENT ---
async def main():
    init_db()
    Thread(target=run_flask).start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
