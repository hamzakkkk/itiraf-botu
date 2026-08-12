import os
import threading
import time
from datetime import datetime
from flask import Flask
from telegram import BotCommand, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. RENDER İÇİN MİNİK WEB SUNUCUSU ---
app_web = Flask('')


@app_web.route('/')
def home():
    return 'Bot 7/24 Canli!'


def run_web():
    app_web.run(host='0.0.0.0', port=8080)


def keep_alive():
    t = threading.Thread(target=run_web)
    t.start()


# --- 2. BOT AYARLARI VE DEĞİŞKENLER ---
ADMIN_ID = 8200746117
TOKEN = '8870037601:AAFmFTITU4Fi9H2wrXZpu1tRNfjOT4DXCxw'
MOLA_SURESI = 5

itiraflar = []
itiraf_sayaci = 1
son_itiraf_zamani = 0


# --- 3. BOT FONKSİYONLARI ---
async def post_init(app):
    komutlar = [
        BotCommand('itiraf', 'Anonim itiraf gönder (Sadece özel mesajda)'),
        BotCommand('itirafgetir', 'Havuza eklenen itirafı gruba getir'),
    ]
    await app.bot.set_my_commands(komutlar)


async def itiraf_et(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global itiraf_sayaci

    if update.effective_chat.type != 'private':
        await update.message.reply_text(
            'İtirafları sadece özel mesajdan gönderebilirsin!'
        )
        return

    metin = ' '.join(context.args)
    if not metin:
        await update.message.reply_text(
            'Lütfen itirafını yaz. Örnek: /itiraf Hocaya aşık oldum'
        )
        return

    user = update.effective_user
    zaman = datetime.now().strftime('%d.%m.%Y %H:%M:%S')

    numarali_itiraf = f'📢 **ANONİM İTİRAF #{itiraf_sayaci}:**\n\n{metin}'
    itiraflar.append(numarali_itiraf)
    itiraf_sayaci += 1

    if ADMIN_ID != 0:
        admin_mesaj = (
            f'📥 **YENİ İTİRAF HAVUZA EKLENDİ**\n\n'
            f'👤 **Gönderen:** {user.full_name} (@{user.username})\n'
            f'🆔 **User ID:** `{user.id}`\n'
            f'🕒 **Zaman:** {zaman}\n\n'
            f'📝 **İtiraf:** {metin}'
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_mesaj)
        except Exception as e:
            print(f'Admin bildirim hatası: {e}')

    await update.message.reply_text(
        'İtirafın anonim olarak havuza kaydedildi! 👍'
    )


async def itiraf_getir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global son_itiraf_zamani

    su_an = time.time()
    gecen_sure = su_an - son_itiraf_zamani

    if gecen_sure < MOLA_SURESI:
        kalan_saniye = int(MOLA_SURESI - gecen_sure)
        await update.message.reply_text(
            f'⏳ Biraz yavaşla! Yeni bir itiraf getirmek için {kalan_saniye} saniye beklemeniz gerekiyor.'
        )
        return

    if not itiraflar:
        await update.message.reply_text('Şu an havuzda hiç itiraf yok!')
        return

    son_itiraf_zamani = su_an
    siradaki_itiraf = itiraflar.pop(0)

    await update.message.reply_text(siradaki_itiraf)


if __name__ == '__main__':
    keep_alive()  # Web sunucusunu başlatır
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler('itiraf', itiraf_et))
    app.add_handler(CommandHandler('itirafgetir', itiraf_getir))

    print('Bot 7/24 sunucu modunda çalışıyor!')
    app.run_polling()
