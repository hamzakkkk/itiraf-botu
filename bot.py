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


# --- 2. BOT AYARLARI VE DAHİLİ BURÇ YORUMLARI ---
ADMIN_ID = 8200746117
TOKEN = '8870037601:AAFmFTITU4Fi9H2wrXZpu1tRNfjOT4DXCxw'

itiraflar = []

BURC_YORUMLARI = {
    'koc': [
        'Bugün enerjin oldukça yüksek! Karar alırken acele etmemeye çalış, sabırlı olmak kazandıracak.',
        'İletişimde açık olman gereken bir gün. Yakın çevrenle küçük fikir ayrılıkları yaşanabilir.',
        'Kariyer ve kişisel hedeflerinde sürpriz gelişmeler olabilir. Şans senden yana!',
    ],
    'boga': [
        'Maddi konularda temkinli olmanda fayda var. Bugün kendine vakit ayırmak sana çok iyi gelecek.',
        'Sakinliğin sayesinde karmaşık bir durumu kolayca çözeceksin. Akşam saatleri sürprizlere açık.',
        'Güvendiğin insanlarla vakit geçirmek enerjini yenileyecek. Yeni fırsatlar kapıda.',
    ],
    'ikizler': [
        'Zihnin çok aktif! Yeni fikirler üretebilir, ertelediğin işleri hızlıca tamamlayabilirsin.',
        'Sosyal çevrenle iletişiminin yoğun olacağı bir gün. Yeni haberler alabilirsin.',
        'Duygusal ve mantıksal kararlar arasında kalabilirsin, hislerine güven.',
    ],
    'yengec': [
        'Duygusal derinliğinin yüksek olduğu bir gün. Sevdiklerine vakit ayırmak huzur verecek.',
        'Sezgilerin bugün çok güçlü. Karar verirken iç sesini dinlemeyi unutma.',
        'Kendini ifade etmekte zorlanmadığın, motivasyonunun yüksek olduğu bir gün.',
    ],
    'aslan': [
        'Liderlik özelliklerin ön plana çıkıyor. Çevrendekilerin takdirini toplayacaksın.',
        'Özgüveninin yüksek olduğu bir gün ancak ego çatışmalarına dikkat etmelisin.',
        'Yaratıcılığını kullanabileceğin işlerde büyük başarılar elde edebilirsin.',
    ],
    'basak': [
        'Detaylara olan dikkatin sayesinde bir hatayı önceden fark edeceksin. Düzen şart!',
        'Sağlığına ve beslenmene dikkat etmen gereken bir gün. Zihnini dinlendirmeyi dene.',
        'Planlı hareket etmek sana zaman kazandıracak. İşlerini sırayla hallet.',
    ],
    'terazi': [
        'Denge ve uyum arayışındasın. Kararsız kaldığın konularda güvendiğin birine danış.',
        'İlişkilerde güzel gelişmeler var. Tatlı dilinle çözemeyeceğin sorun yok.',
        'Sanatsal ve estetik konulara olan ilgin artabilir, kendini şımart.',
    ],
    'akrep': [
        'Tutkulu ve kararlı duruşun sayesinde istediğin bir konuyu çözüme kavuşturacaksın.',
        'Gizemli konular ilgini çekebilir. Şüpheci yaklaşmak yerine akışa bırak.',
        'Odaklandığın işlerde derinlemesine başarı yakalayabileceğin bir gün.',
    ],
    'yay': [
        'Özgürlük arzun yüksek. Yeni şeyler öğrenmek veya plan yapmak isteyebilirsin.',
        'Pozitif enerjin çevrene de yansıyor. Günün getirdiği fırsatları kaçırma.',
        'İyimser tutumun sayesinde engelleri kolayca aşacaksın.',
    ],
    'oglak': [
        'Disiplinli ve odaklısın. Uzun süredir emek verdiğin bir konuda meyve yiyebilirsin.',
        'Sorumlulukların artabilir ama planlı davranırsan hepsinin üstesinden gelirsin.',
        'Geleceğe yönelik sağlam adımlar atabileceğin verimli bir gün.',
    ],
    'kova': [
        'Farklı ve yenilikçi fikirlerinle dikkat çekeceksin. Sıradışı olmaktan korkma.',
        'Arkadaş gruplarınla eğlenceli vakit geçirebilirsin. Paylaşımlar önemli.',
        'Zihnini özgür bırak, yeni projelere başlamak için harika bir gün.',
    ],
    'balik': [
        'Hayal gücün ve empati yeteneğin zirvede. Sanatsal işler için harika bir gün.',
        'İç dünyandaki huzuru korumaya çalış. Geçmişe takılmak yerine önüne bak.',
        'Romantik ve duygusal sürprizlere açık ol, sezgilerin seni yanıltmayacak.',
    ],
}


# --- 3. KOMUTLAR VE OTOMATİK MENÜ ---
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

    if burc not in BURC_YORUMLARI:
        await update.message.reply_text(
            '⚠️ Geçersiz burç adı. Örnek kullanım: /burc koc'
        )
        return

    bugun_str = datetime.now().strftime('%Y-%m-%d')
    gun_sayisi = sum(ord(c) for c in bugun_str)
    index = gun_sayisi % len(BURC_YORUMLARI[burc])
    yorum = BURC_YORUMLARI[burc][index]

    await update.message.reply_text(
        f'🔮 {burc.upper()} BURCU GÜNLÜK YORUMU:\n\n{yorum}'
    )


async def belo_etiketle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('belo @fehmi99')


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

    print('Bot aktif!')
    app.run_polling()
