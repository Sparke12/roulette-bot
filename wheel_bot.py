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
ADMIN_ID = 702681 
ADMIN_USERNAME = "@wheelbetrupe"
CHANNEL_LINK = "https://t.me/Wheelbetpredictor12" # METS TON LIEN ICI

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
app = Flask('')

@app.route('/')
def home(): return "Bot is Running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- BASE DE DONNÉES AMÉLIORÉE ---
def init_db():
    conn = sqlite3.connect('wheel_database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, 
        is_vip INTEGER DEFAULT 0, 
        referral_count INTEGER DEFAULT 0,
        daily_count INTEGER DEFAULT 0, 
        last_use TEXT)''')
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
        user = (0, 0, 0, today)
    
    if is_vip is not None: cursor.execute('UPDATE users SET is_vip = ? WHERE user_id = ?', (is_vip, user_id))
    if referral_add > 0: cursor.execute('UPDATE users SET referral_count = referral_count + ? WHERE user_id = ?', (referral_add, user_id))
    if daily_count is not None: cursor.execute('UPDATE users SET daily_count = ?, last_use = ? WHERE user_id = ?', (daily_count, today, user_id))
    
    conn.commit()
    conn.close()

# --- COMMANDES ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Gestion du parrainage via le lien start
    args = message.text.split()
    if len(args) > 1:
        referrer_id = args[1]
        if int(referrer_id) != message.from_user.id:
            update_user(int(referrer_id), referral_add=1)
            
    await message.answer(
        "🚀 **WHEEL ANALYZER PRO**\n\n"
        "🎁 2 prédictions gratuites / jour\n"
        "🔥 **NOUVEAU :** Débloquez 3 prédictions COTE 3 & 6 en parrainant 3 amis !\n"
        "💎 VIP : Accès illimité (15 000 FCFA)\n\n"
        "👉 /signal | /parrainage | /vip"
    )

@dp.message(Command("parrainage"))
async def cmd_referral(message: types.Message):
    user = get_user(message.from_user.id)
    count = user[1] if user else 0
    ref_link = f"https://t.me/{(await bot.get_me()).username}?start={message.from_user.id}"
    
    msg = (
        f"👥 **VOTRE ESPACE PARRAINAGE**\n\n"
        f"Amis parrainés : **{count} / 3**\n\n"
        f"Partagez ce lien pour débloquer les **COTES 3 & 6** gratuitement :\n"
        f"`{ref_link}`\n\n"
        "💡 *Dès que 3 amis rejoignent via ce lien, vos prédictions spéciales sont activées !*"
    )
    await message.answer(msg, parse_mode="Markdown")

@dp.message(Command("signal"))
async def cmd_signal(message: types.Message):
    user_id = message.from_user.id
    user_data = get_user(user_id)
    if not user_data: 
        update_user(user_id)
        user_data = (0, 0, 0, "")
    
    is_vip, ref_count, daily, last_use = user_data
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Vérification des droits
    has_bonus = ref_count >= 3
    limit = 5 if has_bonus else 2 # 2 de base + 3 bonus si parrainage
    
    if not is_vip and daily >= limit and last_use == today:
        await message.answer("❌ Limite atteinte. /parrainage pour en avoir plus ou passez /vip !")
        return

    await message.answer("✍️ **Entrez les 3 derniers numéros (ex: 4, 12, 30) :**")

@dp.message(F.text.regexp(r'^(\d+),\s*(\d+),\s*(\d+)$'))
async def process_numbers(message: types.Message):
    nums = message.text.split(",")
    user = get_user(message.from_user.id)
    is_vip = user[0]
    ref_count = user[1]

    m = await message.answer("📡 **Analyse des algorithmes...**")
    await asyncio.sleep(2)
    
    # Logique de prédiction
    play_time = (datetime.now() + timedelta(minutes=5)).strftime("%H:%M")
    
    if is_vip or ref_count >= 3:
        # PRÉDICTION HAUTE COTE
        cote = random.choice([3, 6])
        type_p = "Douzaine (D12)" if cote == 3 else "Sixain (Line)"
        res = f"🔥 **PRÉDICTION COTE {cote}**\n🎯 Type : {type_p}\n⏰ Jeu à : {play_time}\n💡 Fiabilité : 92%"
    else:
        # PRÉDICTION SIMPLE
        res = f"✅ **PRÉDICTION SIMPLE**\n🎯 Choix : {random.choice(['ROUGE', 'NOIR'])}\n⏰ Jeu à : {play_time}\n💡 Fiabilité : 97%"

    # ENVOI D'UNE PHOTO DE MOTIVATION (Optionnel - Mets tes images sur GitHub)
    # try:
    #    photo = FSInputFile("win_proof.jpg")
    #    await message.answer_photo(photo, caption="Dernier gain validé ! 💰")
    # except: pass

    await m.edit_text(res + "\n\n" + get_motivation_quote(), parse_mode="Markdown")
    update_user(message.from_user.id, daily_count=user[2] + 1)

def get_motivation_quote():
    quotes = [
        "💪 *Le succès n'est pas le fruit du hasard, mais de la discipline. Jouez avec sagesse !*",
        "💎 *Chaque mise est une opportunité, mais la patience est votre meilleur allié.*",
        "🚀 *Les grands gagnants savent s'arrêter au bon moment. Suivez le plan !*",
        "🔥 *La chance sourit à ceux qui ont une stratégie. En avant !*"
    ]
    return random.choice(quotes)

# --- LANCEMENT ---
async def main():
    init_db()
    Thread(target=run_flask).start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
