from datetime import datetime
import os
import re
import threading
import xml.etree.ElementTree as ET
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


# --- 3. KOMUTLAR VE OTOMATİK MENÜ ---
async def post_init(app):
    komutlar = [
        BotCommand('itiraf', 'Anonim itiraf gönder (Sadece özel mesajda)'),
        BotCommand('itirafgetir', 'Havuza eklenen itirafı gruba getir'),
        BotCommand('hava', 'Hava durumunu öğren (Örn: /hava izmit)'),
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


# 🔮 GÜNLÜK BURÇ YORUMU (Resmi Türkçe RSS Akışı - Kesintisiz)
async def burc_yorum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            'Lütfen bir burç adı yazın. Örnek: /burc koc\n'
            'Kullanabileceğin burçlar: koc, boga, ikizler, yengec, aslan, basak, terazi, akrep, yay, oglak, kova, balik'
        )
        return

    burc = context.args[0].lower().strip()
    tr_map = {
        'koç': 'koc',
        'boğa': 'boga',
        'yengeç': 'yengec',
        'başak': 'basak',
        'oğlak': 'oglak',
        'balık': 'balik',
    }
    burc = tr_map.get(burc, burc)

    burc_isimleri = {
        'koc': 'Koç',
        'boga': 'Boğa',
        'ikizler': 'İkizler',
        'yengec': 'Yengeç',
        'aslan': 'Aslan',
        'basak': 'Başak',
        'terazi': 'Terazi',
        'akrep': 'Akrep',
        'yay': 'Yay',
        'oglak': 'Oğlak',
        'kova': 'Kova',
        'balik': 'Balık',
    }

    if burc not in burc_isimleri:
        await update.message.reply_text(
            '⚠️ Geçersiz burç adı. Örnek kullanım: /burc koc'
        )
        return

    try:
        # Haber7 Resmi Astroloji RSS Akışı
        url = 'https://siteneekle.haber7.com/rss/astroloji.xml'
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5)

        if res.status_code == 200:
            root = ET.fromstring(res.content)
            hedef_isim = burc_isimleri[burc]

            for item in root.findall('.//item'):
                title = item.find('title')
                description = item.find('description')

                if title is not None and hedef_isim.lower() in title.text.lower():
                    if description is not None and description.text:
                        # HTML etiketlerini ve CDATA yapılarını temizle
                        metin = re.sub(r'<[^<]+?>', '', description.text).strip()
                        metin = metin.replace('&nbsp;', ' ')
                        
                        await update.message.reply_text(
                            f'🔮 **{hedef_isim.upper()} BURCU GÜNLÜK YORUMU:**\n\n{metin}'
                        )
                        return

        await update.message.reply_text('⚠️ Bugün için burç yorumu henüz güncellenmedi.')

    except Exception:
        await update.message.reply_text('⚠️ Burç yorumu alınırken bir hata oluştu.')


# 🏷️ BELO ETİKETLEME
async def belo_etiketle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('belo @fehmi99')


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
    app.add_handler(CommandHandler('burc', burc_yorum))
    app.add_handler(CommandHandler('belo', belo_etiketle))

    print('Bot aktif!')
    app.run_polling()
