import logging
import asyncio
import sqlite3
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# --- CONFIGURATION (Identifiants à ne pas partager) ---
API_TOKEN = '7743738047:AAHZDxCyYsSMjxQ5gf8ealNPPJ70dPhYGTg'
ADMIN_ID = 702681 # Ton ID Telegram personnel
ADMIN_USERNAME = "@wheelbetrupe" # Remplace par ton pseudo pour les paiements

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- INITIALISATION DE LA BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('wheel_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            is_vip INTEGER DEFAULT 0,
            daily_count INTEGER DEFAULT 0,
            last_use TEXT
        )
    ''')
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
        cursor.execute('INSERT INTO users (user_id, is_vip, daily_count, last_use) VALUES (?, ?, ?, ?)', 
                       (user_id, 0, 0, today))
    
    if is_vip is not None:
        cursor.execute('UPDATE users SET is_vip = ? WHERE user_id = ?', (is_vip, user_id))
    if daily_count is not None:
        cursor.execute('UPDATE users SET daily_count = ?, last_use = ? WHERE user_id = ?', (daily_count, today, user_id))
    
    conn.commit()
    conn.close()

# --- GÉNÉRATEUR DE SIGNAUX HORAIRES ---
async def generate_schedule(is_vip=False):
    now = datetime.now()
    options_cote2 = ["🔴 ROUGE", "⚫ NOIR", "PAIR", "IMPAIR", "MANQUE (1-18)", "PASSE (19-36)"]
    options_cote3 = ["P12 (Douzaine 1)", "M12 (Douzaine 2)", "D12 (Douzaine 3)", "Colonne 1", "Colonne 2", "Colonne 3"]
    
    # On génère 1 signal pour les gratuits, 4 pour les VIP
    nb_signaux = 4 if is_vip else 1
    
    texte = "📊 **CALENDRIER DE PRÉDICTIONS**\n"
    texte += "━━━━━━━━━━━━━━━━━━\n"
    
    for i in range(1, nb_signaux + 1):
        # Intervalle de 10 minutes
        heure_signal = (now + timedelta(minutes=i * 10)).strftime("%H:%M")
        # Alternance aléatoire entre cote 2 et 3
        type_jeu = random.choice([options_cote2, options_cote3])
        prediction = random.choice(type_jeu)
        confiance = random.randint(85, 98)
        
        texte += f"⏰ **{heure_signal}** : {prediction}\n"
        texte += f"🔥 Fiabilité : {confiance}%\n"
        texte += "------------------\n"

    if not is_vip:
        texte += "\n💡 *Passez VIP pour recevoir 4 signaux d'avance !* /vip"
    else:
        texte += "\n💎 *Mode VIP Activé - Bonne chance !*"
        
    return texte

# --- COMMANDES DU BOT ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🚀 **BIENVENUE SUR WHEEL PREDICTOR**\n\n"
        "L'algorithme analyse les failles de la roulette américaine en temps réel.\n\n"
        "🎁 **Gratuit** : 2 signaux par jour\n"
        "💎 **VIP (15.000F)** : Signaux illimités + Horaires précis\n\n"
        "👉 Tapez /signal pour commencer."
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

    # Reset du compteur quotidien
    if last_use != today:
        daily_count = 0
        update_user(user_id, daily_count=0)

    # Vérification des limites
    if not is_vip and daily_count >= 2:
        await message.answer("❌ Limite gratuite atteinte (2/2).\n\nPour continuer à gagner, rejoignez le groupe VIP !\n💰 Prix : 15.000 FCFA / mois\nCommande : /vip")
        return

    wait_msg = await message.answer("🔍 *Analyse des cycles en cours...*")
    await asyncio.sleep(3)
    
    planning = await generate_schedule(is_vip=bool(is_vip))
    await wait_msg.edit_text(planning, parse_mode="Markdown")
    
    if not is_vip:
        update_user(user_id, daily_count=daily_count + 1)

@dp.message(Command("vip"))
async def cmd_vip(message: types.Message):
    await message.answer(
        "💎 **OFFRE VIP WHEEL PREDICTOR** 💎\n\n"
        "✅ Accès illimité aux signaux 24h/24\n"
        "✅ Précision augmentée (95%)\n"
        "✅ Calendrier de jeu complet\n\n"
        "💰 **Prix : 15.000 FCFA / Mois**\n"
        "📱 Paiement via Orange Money / Moov / MTN\n\n"
        f"📩 Contactez l'admin pour activer : {ADMIN_USERNAME}"
    )

# --- COMMANDE ADMIN (Pour toi uniquement) ---
@dp.message(Command("setvip"))
async def cmd_setvip(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        try:
            target_id = int(message.text.split()[1])
            update_user(target_id, is_vip=1)
            await message.answer(f"✅ L'ID `{target_id}` est maintenant VIP ! 💎")
        except:
            await message.answer("⚠️ Usage : `/setvip ID_TELEGRAM`")
    else:
        await message.answer("❌ Vous n'êtes pas administrateur.")

# --- LANCEMENT ---
async def main():
    init_db()
    print("🤖 Bot Wheel Predictor démarré !")
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot arrêté.")
