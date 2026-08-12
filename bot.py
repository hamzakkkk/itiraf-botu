from datetime import datetime
import json
import os
import threading
import time
from flask import Flask
import requests
from telegram import BotCommand, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- 1. RENDER İÇİN WEB SUNUCUSU ---
app_web = Flask('')


@app_web.route('/')
def home():
    return 'Bot 7/24 Canli!'


def run_web():
    app_web.run(host='0.0.0.0', port=8080)


def keep_alive():
    t = threading.Thread(target=run_web)
    t.start()


# --- 2. BOT AYARLARI VE KALICI VERİ DEPOLAMA ---
ADMIN_ID = 8200746117
TOKEN = '8870037601:AAFmFTITU4Fi9H2wrXZpu1tRNfjOT4DXCxw'
MOLA_SURESI = 5
DATA_FILE = 'data.json'


def veri_yukle():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('itiraflar', []), data.get('itiraf_sayaci', 1)
        except Exception:
            pass
    return [], 1


def veri_kaydet():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(
            {'itiraflar': itiraflar, 'itiraf_sayaci': itiraf_sayaci},
            f,
            ensure_ascii=False,
            indent=2,
        )


itiraflar, itiraf_sayaci = veri_yukle()
son_itiraf_zamani = 0


# --- 3. KOMUTLAR VE OTOMATİK MENÜ TANIMLARI ---
async def post_init(app):
    komutlar = [
        BotCommand('itiraf', 'Anonim itiraf gönder (Sadece özel mesajda)'),
        BotCommand('itirafgetir', 'Havuza eklenen itirafı gruba getir'),
        BotCommand(
            'havadurumu', 'Anlık hava durumunu öğren (Örn: /havadurumu izmit)'
        ),
        BotCommand('hava', 'Hava durumunu öğren (Kısa kullanım)'),
        BotCommand('doviz', 'Anlık Dolar, Euro ve Altın fiyatları'),
    ]
    await app.bot.set_my_commands(komutlar)


async def hava_durumu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sehir = ' '.join(context.args) if context.args else 'Izmit'
    try:
        url = f'https://wttr.in/{sehir}?format=%C+%t+%w&lang=tr'
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and 'Unknown' not in res.text:
            mesaj = f'🌤️ **{sehir.capitalize()} için Hava Durumu:**\n\n{res.text.strip()}'
        else:
            mesaj = '⚠️ Şehir bulunamadı. Lütfen geçerli bir şehir adı yazın. (Örn: `/havadurumu izmit`)'
    except Exception:
        mesaj = '⚠️ Hava durumu bilgisi alınırken bir hata oluştu.'

    await update.message.reply_text(mesaj, parse_mode='Markdown')


async def doviz_bilgisi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = requests.get(
            'https://api.genelpara.com/embed/doviz.json', timeout=5
        ).json()
        usd_al, usd_sat = res['USD']['alis'], res['USD']['satis']
        eur_al, eur_sat = res['EUR']['alis'], res['EUR']['satis']
        ga_al, ga_sat = res['GA']['alis'], res['GA']['satis']

        mesaj = (
            f'📊 **ANLIK PIYASA VERİLERİ**\n\n'
            f'💵 **Dolar (USD):** Alış: {usd_al} TL | Satış: {usd_sat} TL\n'
            f'💶 **Euro (EUR):** Alış: {eur_al} TL | Satış: {eur_sat} TL\n'
            f'🏆 **Gram Altın:** Alış: {ga_al} TL | Satış: {ga_sat} TL'
        )
    except Exception:
        mesaj = '⚠️ Piyasa verileri çekilemedi, lütfen tekrar deneyin.'

    await update.message.reply_text(mesaj, parse_mode='Markdown')


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

    veri_kaydet()

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
            f'⏳ Biraz yavaşla! {kalan_saniye} saniye beklemeniz gerekiyor.'
        )
        return

    if not itiraflar:
        await update.message.reply_text('Şu an havuzda hiç itiraf yok!')
        return

    son_itiraf_zamani = su_an
    siradaki_itiraf = itiraflar.pop(0)

    veri_kaydet()

    await update.message.reply_text(siradaki_itiraf)


if __name__ == '__main__':
    keep_alive()
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler('itiraf', itiraf_et))
    app.add_handler(CommandHandler('itirafgetir', itiraf_getir))
    app.add_handler(CommandHandler('havadurumu', hava_durumu))
    app.add_handler(CommandHandler('hava', hava_durumu))
    app.add_handler(CommandHandler('doviz', doviz_bilgisi))

    print('Bot güncellendi ve menü komutlarıyla aktif!')
    app.run_polling()
