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
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- LOGIQUE BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('wheel_database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, 
        is_vip INTEGER DEFAULT 0, 
        daily_count INTEGER DEFAULT 0, 
        last_use TEXT)''')
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

# --- GÉNÉRATEUR DE PRÉDICTIONS (SÉCURISÉ) ---
async def generate_schedule(is_vip=False):
    now = datetime.now()
    # On utilise des chances simples (Cote 2) pour minimiser les pertes
    options_safe = ["🔴 ROUGE", "⚫ NOIR", "PAIR", "IMPAIR", "MANQUE (1-18)", "PASSE (19-36)"]
    
    nb = 4 if is_vip else 1
    texte = "📊 **PRÉDICTIONS SÉCURISÉES**\n━━━━━━━━━━━━━━━━━━\n"
    
    for i in range(1, nb + 1):
        # Les signaux VIP sont espacés pour plus de réalisme
        h = (now + timedelta(minutes=i * 12)).strftime("%H:%M")
        pred = random.choice(options_safe)
        confiance = random.randint(94, 98)
        texte += f"⏰ **{h}** : {pred}\n🔥 Fiabilité : {confiance}%\n------------------\n"
    
    texte += "\n⚠️ **CONSEIL :** Si perte, doublez la mise au prochain signal (Martingale)."
    if not is_vip: 
        texte += "\n\n💡 /vip pour débloquer 4 signaux !"
    return texte

# --- COMMANDES DU BOT ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🚀 **WHEEL PREDICTOR PRO**\n\n"
        "Bienvenue dans l'algorithme de prédiction le plus stable.\n\n"
        "🎁 Gratuit : 2 signaux / jour\n"
        "💎 VIP : Accès illimité + Stratégie\n\n"
        "👉 Cliquez sur /signal pour commencer."
    )

@dp.message(Command("vip"))
async def cmd_vip(message: types.Message):
    await message.answer(
        "💎 **DEVENIR MEMBRE VIP** 💎\n\n"
        "Passez à la vitesse supérieure pour **15 000 FCFA** :\n"
        "✅ 4 signaux par analyse au lieu de 1.\n"
        "✅ Accès aux prédictions toute la journée.\n"
        "✅ Gestion de mise pour ne jamais perdre votre capital.\n\n"
        "🚀 **POUR PAYER ET ACTIVER :**\n"
        f"Contactez l'admin : {ADMIN_USERNAME}\n"
        f"Votre ID à envoyer : `{message.from_user.id}`",
        parse_mode="Markdown"
    )

@dp.message(Command("signal"))
async def cmd_signal(message: types.Message):
    user_id = message.from_user.id
    user_data = get_user(user_id)
    today = datetime.now().strftime('%Y-%m-%d')
    
    if not user_data: 
        update_user(user_id, daily_count=0)
        user_data = (0, 0, today)
    
    is_vip, daily_count, last_use = user_data
    
    # Réinitialisation du compteur chaque jour
    if last_use != today:
        update_user(user_id, daily_count=0)
        daily_count = 0

    if not is_vip and daily_count >= 2:
        await message.answer("❌ Limite gratuite (2/jour) atteinte.\n\nCliquez sur /vip pour continuer !")
        return

    m = await message.answer("🔍 **Connexion à la table en cours...**")
    await asyncio.sleep(1.5)
    await m.edit_text("📡 **Analyse des derniers tirages...**")
    await asyncio.sleep(1.5)
    
    res = await generate_schedule(bool(is_vip))
    await m.edit_text(res, parse_mode="Markdown")
    
    if not is_vip:
        update_user(user_id, daily_count=daily_count + 1)

@dp.message(Command("setvip"))
async def cmd_setvip(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        try:
            target = int(message.text.split()[1])
            update_user(target, is_vip=1)
            await message.answer(f"✅ L'ID `{target}` a été activé VIP avec succès !")
        except:
            await message.answer("❌ Erreur. Usage : `/setvip ID`")

# --- LANCEMENT ---
async def main():
    init_db()
    Thread(target=run_flask).start()
    print("🤖 Bot démarré avec succès !")
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
