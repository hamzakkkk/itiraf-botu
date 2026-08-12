from datetime import datetime
import os
import threading
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


# --- 2. BOT AYARLARI ---
ADMIN_ID = 8200746117
TOKEN = '8870037601:AAFmFTITU4Fi9H2wrXZpu1tRNfjOT4DXCxw'

itiraflar = []


# --- 3. KOMUTLAR VE OTOMATİK MENÜ TANIMLARI ---
async def post_init(app):
    komutlar = [
        BotCommand('itiraf', 'Anonim itiraf gönder (Sadece özel mesajda)'),
        BotCommand('itirafgetir', 'Havuza eklenen itirafı gruba getir'),
        BotCommand('hava', 'Hava durumunu öğren (Örn: /hava izmit)'),
        BotCommand('doviz', 'Anlık Dolar, Euro ve Altın fiyatları'),
        BotCommand('burc', 'Günlük burç yorumu (Örn: /burc koc)'),
        BotCommand('belo', 'Belo ve Fehmiyi etiketler'),
    ]
    await app.bot.set_my_commands(komutlar)


# 🌤️ HAVA DURUMU (Sadece /hava)
async def hava_durumu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sehir = ' '.join(context.args) if context.args else 'Izmit'
    try:
        headers = {'User-Agent': 'curl/7.68.0'}
        url = f'https://wttr.in/{sehir}?format=%C+%t+%w&lang=tr'
        res = requests.get(url, headers=headers, timeout=5)

        if res.status_code == 200 and 'Unknown' not in res.text:
            durum = res.text.strip()
            mesaj = f'🌤️ {sehir.capitalize()} için Hava Durumu:\n\n{durum}'
        else:
            mesaj = '⚠️ Şehir bulunamadı. Örnek kullanım: /hava izmit'
    except Exception:
        mesaj = '⚠️ Hava durumu bilgisi alınamadı, lütfen tekrar deneyin.'

    await update.message.reply_text(mesaj)


# 💱 DÖVİZ
async def doviz_bilgisi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = requests.get(
            'https://api.genelpara.com/embed/doviz.json', timeout=5
        ).json()
        usd_al, usd_sat = res['USD']['alis'], res['USD']['satis']
        eur_al, eur_sat = res['EUR']['alis'], res['EUR']['satis']
        ga_al, ga_sat = res['GA']['alis'], res['GA']['satis']

        mesaj = (
            f'📊 ANLIK PIYASA VERİLERİ\n\n'
            f'💵 Dolar (USD): Alış: {usd_al} TL | Satış: {usd_sat} TL\n'
            f'💶 Euro (EUR): Alış: {eur_al} TL | Satış: {eur_sat} TL\n'
            f'🏆 Gram Altın: Alış: {ga_al} TL | Satış: {ga_sat} TL'
        )
    except Exception:
        mesaj = '⚠️ Piyasa verileri çekilemedi, lütfen tekrar deneyin.'

    await update.message.reply_text(mesaj)


# 🔮 GÜNLÜK BURÇ YORUMU
async def burc_yorum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            'Lütfen bir burç adı yazın. Örnek: /burc koc\n'
            'Kullanabileceğin burçlar: koc, boga, ikizler, yengec, aslan, basak, terazi, akrep, yay, oglak, kova, balik'
        )
        return

    burc = context.args[0].lower().strip()
    # Türkçe karakter dönüştürme
    tr_map = {
        'koç': 'koc',
        'boğa': 'boga',
        'yengeç': 'yengec',
        'başak': 'basak',
        'oğlak': 'oglak',
        'balık': 'balik',
    }
    burc = tr_map.get(burc, burc)

    try:
        url = f'https://astrology-api-ce89.onrender.com/burc/{burc}'
        res = requests.get(url, timeout=5)

        if res.status_code == 200:
            data = res.json()
            yorum = data.get('yorum', 'Yorum bulunamadı.')
            mesaj = f'🔮 {burc.upper()} BURCU GÜNLÜK YORUMU:\n\n{yorum}'
        else:
            # Alternatif servis
            res_alt = requests.get(
                f'https://burc-api.vercel.app/burc/{burc}', timeout=5
            )
            if res_alt.status_code == 200:
                yorum = res_alt.json().get('yorum', 'Yorum bulunamadı.')
                mesaj = f'🔮 {burc.upper()} BURCU GÜNLÜK YORUMU:\n\n{yorum}'
            else:
                mesaj = '⚠️ Geçersiz burç adı veya servise ulaşılamıyor.'
    except Exception:
        mesaj = (
            '⚠️ Burç yorumu çekilirken bir hata oluştu. Örnek: `/burc koc`'
        )

    await update.message.reply_text(mesaj)


# 🏷️ BELO ETİKETLEME
async def belo_etiketle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('@belo @fehmi99')


# 📩 İTİRAF SİSTEMİ
async def itiraf_et(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    numarali_itiraf = f'📢 ANONİM İTİRAF:\n\n{metin}'
    itiraflar.append(numarali_itiraf)

    if ADMIN_ID != 0:
        admin_mesaj = (
            f'📥 YENİ İTİRAF HAVUZA EKLENDİ\n\n'
            f'👤 Gönderen: {user.full_name} (@{user.username})\n'
            f'🆔 User ID: {user.id}\n'
            f'🕒 Zaman: {zaman}\n\n'
            f'📝 İtiraf: {metin}'
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_mesaj)
        except Exception as e:
            print(f'Admin bildirim hatası: {e}')

    await update.message.reply_text(
        'İtirafın anonim olarak havuza kaydedildi! 👍'
    )


async def itiraf_getir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not itiraflar:
        await update.message.reply_text('Şu an havuzda hiç itiraf yok!')
        return

    siradaki_itiraf = itiraflar.pop(0)
    await update.message.reply_text(siradaki_itiraf)


if __name__ == '__main__':
    keep_alive()
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler('itiraf', itiraf_et))
    app.add_handler(CommandHandler('itirafgetir', itiraf_getir))
    app.add_handler(CommandHandler('hava', hava_durumu))
    app.add_handler(CommandHandler('doviz', doviz_bilgisi))
    app.add_handler(CommandHandler('burc', burc_yorum))
    app.add_handler(CommandHandler('belo', belo_etiketle))

    print('Bot hafifletilmiş modda aktif!')
    app.run_polling()
