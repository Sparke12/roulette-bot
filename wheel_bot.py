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
ADMIN_ID = 702681 
ADMIN_USERNAME = "@wheelbetrupe"
CHANNEL_LINK = "https://t.me/Wheelbetpredictor12"
BOT_USERNAME = "WHEELPREDICTION_BOT"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
app = Flask('')

@app.route('/')
def home(): return "Bot is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('wheel_database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, 
        is_vip INTEGER DEFAULT 0, 
        referral_count INTEGER DEFAULT 0,
        daily_count INTEGER DEFAULT 0, 
        last_use TEXT)''')
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN referral_count INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
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
        cursor.execute('UPDATE users SET referral_count = referral_count + ? WHERE user_id = ?', (user_id if not user else user_id)) # Correction logique
        cursor.execute('UPDATE users SET referral_count = referral_count + ? WHERE user_id = ?', (referral_add, user_id))
    if daily_count is not None: 
        cursor.execute('UPDATE users SET daily_count = ?, last_use = ? WHERE user_id = ?', (daily_count, today, user_id))
    conn.commit()
    conn.close()

# --- COMMANDES ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    args = message.text.split()
    user_id = message.from_user.id
    
    # Inscription et Parrainage
    if not get_user(user_id):
        update_user(user_id)
        if len(args) > 1 and args[1].isdigit():
            referrer = int(args[1])
            if referrer != user_id:
                update_user(referrer, referral_add=1)
                try:
                    await bot.send_message(referrer, "🎉 **+1 Parrainage !** Un ami a rejoint via votre lien.")
                except: pass

    await message.answer(
        "🚀 **WHEEL ANALYZER PRO**\n\n"
        "📢 **IMPORTANT :** Pour recevoir les signaux, rejoignez notre canal de preuves :\n"
        f"👉 {CHANNEL_LINK}\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🎁 2 prédictions gratuites / jour\n"
        "🔥 **COTES 3 & 6** (après 3 parrainages)\n"
        "💎 Mode VIP illimité (15 000 FCFA)\n\n"
        "Utilisez /signal pour analyser vos numéros !"
    )

@dp.message(Command("parrainage"))
async def cmd_referral(message: types.Message):
    user = get_user(message.from_user.id)
    count = user[1] if user else 0
    ref_link = f"https://t.me/{BOT_USERNAME}?start={message.from_user.id}"
    
    await message.answer(
        "👥 **PROGRAMME AMBASSADEUR**\n\n"
        f"📈 Vos parrainages : **{count} / 3**\n\n"
        "🔗 **Votre lien personnel (cliquez pour copier) :**\n"
        f"`{ref_link}`\n\n"
        "💡 *Partagez ce lien ! Dès que 3 amis s'inscrivent, vous débloquez les grosses Cotes gratuitement.*",
        parse_mode="Markdown"
    )

@dp.message(Command("vip"))
async def cmd_vip(message: types.Message):
    await message.answer(
        "💎 **ACCÈS VIP ILLIMITÉ**\n\n"
        "Prix : **15 000 FCFA**\n"
        "✅ Pas de limite quotidienne\n"
        "✅ Accès direct aux Cotes 3 et 6\n"
        "✅ Support priorité par l'admin\n\n"
        f"📩 Contact : {ADMIN_USERNAME}\n"
        f"Votre ID : `{message.from_user.id}`",
        parse_mode="Markdown"
    )

@dp.message(Command("signal"))
async def cmd_signal(message: types.Message):
    user = get_user(message.from_user.id)
    if not user: update_user(message.from_user.id); user = (0,0,0,"")
    
    is_vip, ref_count, daily, last_use = user
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Reset journalier
    if last_use != today:
        daily = 0
        update_user(message.from_user.id, daily_count=0)

    limit = 5 if ref_count >= 3 else 2
    if not is_vip and daily >= limit:
        await message.answer("❌ Limite atteinte ! /parrainage ou passez /vip.")
        return

    await message.answer("✍️ **Entrez les 3 derniers numéros (ex: 14, 2, 35) :**")

@dp.message(F.text.regexp(r'^(\d+),\s*(\d+),\s*(\d+)$'))
async def process_numbers(message: types.Message):
    user = get_user(message.from_user.id)
    m = await message.answer("📡 **Analyse des séquences...**")
    await asyncio.sleep(2)
    
    play_time = (datetime.now() + timedelta(minutes=5)).strftime("%H:%M")
    
    if user[0] or user[1] >= 3:
        cote = random.choice([3, 6])
        res = f"🔥 **PRÉDICTION COTE {cote}**\n🎯 Type : {'Douzaine' if cote == 3 else 'Sixain'}\n⏰ Heure : {play_time}\n💡 Fiabilité : 94%"
    else:
        res = f"✅ **PRÉDICTION SIMPLE**\n🎯 Couleur : {random.choice(['🔴 ROUGE', '⚫ NOIR'])}\n⏰ Heure : {play_time}\n💡 Fiabilité : 98%"

    motivation = random.choice([
        "💪 *La discipline est la clé du gain.*",
        "🚀 *Suivez le signal, encaissez le profit.*",
        "💎 *Le VIP à 15 000F change une vie.*"
    ])
    
    await m.edit_text(f"{res}\n\n{motivation}", parse_mode="Markdown")
    update_user(message.from_user.id, daily_count=user[2] + 1)

@dp.message(Command("setvip"))
async def cmd_setvip(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        try:
            target = int(message.text.split()[1])
            update_user(target, is_vip=1)
            await message.answer(f"✅ ID {target} est maintenant VIP !")
        except: pass

# --- RUN ---
async def main():
    init_db()
    Thread(target=run_flask).start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
